"""Falsify release loading: a release must refuse to serve when it is not what it claims to be.

This is the local stand-in for the registry failure modes in docs/architecture.md. A swapped,
truncated or contract-mismatched artifact has to fail at load, loudly, rather than answer requests
with confident nonsense.

Everything here trains on a handful of synthetic rows: the point is the verification path, not the
model.
"""

from pathlib import Path

import pytest

from mlplatform.fingerprint import file_checksum
from mlplatform.release import ReleaseRecord, utc_now
from services.fraud_scoring.contract import (
    FEATURE_COLUMNS,
    SCHEMA_VERSION,
    TARGET_COLUMN,
    ModelContract,
    SchemaViolation,
    current_model_contract,
    feature_matrix,
)
from services.fraud_scoring.data import synthetic_frame
from services.fraud_scoring.predict import ReleaseIntegrityError, load_release
from services.fraud_scoring.train import build_estimator, save_artifact

SEED = 3


def build_release(tmp_path: Path, contract: ModelContract | None = None) -> tuple[Path, Path]:
    """Train a throwaway model and write a matching artifact plus release record."""
    frame = synthetic_frame(rows=300, seed=SEED, fraud_rate=0.2)
    estimator = build_estimator().set_params(max_iter=5)
    estimator.fit(feature_matrix(frame), frame[TARGET_COLUMN].to_numpy())

    artifact_path = save_artifact(
        estimator, contract or current_model_contract(), path=tmp_path / "model.joblib"
    )
    release_path = tmp_path / "release.json"
    ReleaseRecord(
        workload="fraud_scoring",
        schema_version=SCHEMA_VERSION,
        source_commit="0" * 40,
        source_dirty=False,
        dataset_content_hash="a" * 64,
        dataset_schema_hash="b" * 64,
        dataset_rows=len(frame),
        training_seed=1,
        artifact_path=str(artifact_path),
        artifact_sha256=file_checksum(artifact_path),
        metric_name="average_precision",
        metric_value=0.5,
        created_at=utc_now(),
    ).write(release_path)
    return artifact_path, release_path


def test_a_matching_release_loads_and_scores(tmp_path: Path) -> None:
    artifact_path, release_path = build_release(tmp_path)
    release = load_release(artifact_path, release_path)

    payload = synthetic_frame(rows=4, seed=SEED).loc[:, list(FEATURE_COLUMNS)]
    scores = release.score(payload)

    assert len(scores) == 4
    assert ((scores >= 0.0) & (scores <= 1.0)).all()


def test_decision_output_carries_release_metadata(tmp_path: Path) -> None:
    artifact_path, release_path = build_release(tmp_path)
    release = load_release(artifact_path, release_path)

    payload = synthetic_frame(rows=2, seed=SEED).loc[:, list(FEATURE_COLUMNS)]
    decided = release.decide(payload, threshold=0.5)

    assert set(decided.columns) == {
        "fraud_probability",
        "is_fraud",
        "threshold",
        "schema_version",
        "source_commit",
    }
    assert (decided["schema_version"] == SCHEMA_VERSION).all()


def test_a_swapped_artifact_is_refused(tmp_path: Path) -> None:
    artifact_path, release_path = build_release(tmp_path)
    payload = artifact_path.read_bytes()
    artifact_path.write_bytes(payload[:-1] + bytes([payload[-1] ^ 0x01]))

    with pytest.raises(ReleaseIntegrityError) as raised:
        load_release(artifact_path, release_path)
    assert "checksum" in str(raised.value)


def test_a_truncated_artifact_is_refused(tmp_path: Path) -> None:
    artifact_path, release_path = build_release(tmp_path)
    artifact_path.write_bytes(artifact_path.read_bytes()[: -1024])

    with pytest.raises(ReleaseIntegrityError):
        load_release(artifact_path, release_path)


def test_a_model_built_against_another_schema_is_refused(tmp_path: Path) -> None:
    stale = ModelContract(
        schema_version="fraud_scoring.v0",
        features=FEATURE_COLUMNS,
        target=TARGET_COLUMN,
        positive_label=1,
    )
    artifact_path, release_path = build_release(tmp_path, contract=stale)

    with pytest.raises(ReleaseIntegrityError) as raised:
        load_release(artifact_path, release_path)
    assert "incompatible" in str(raised.value)


def test_a_missing_release_record_is_refused(tmp_path: Path) -> None:
    artifact_path, release_path = build_release(tmp_path)
    release_path.unlink()

    with pytest.raises(ReleaseIntegrityError):
        load_release(artifact_path, release_path)


def test_a_missing_artifact_is_refused(tmp_path: Path) -> None:
    artifact_path, release_path = build_release(tmp_path)
    artifact_path.unlink()

    with pytest.raises(ReleaseIntegrityError):
        load_release(artifact_path, release_path)


def test_a_bad_payload_is_rejected_before_the_model_sees_it(tmp_path: Path) -> None:
    artifact_path, release_path = build_release(tmp_path)
    release = load_release(artifact_path, release_path)

    payload = synthetic_frame(rows=3, seed=SEED).loc[:, list(FEATURE_COLUMNS)].drop(columns=["V9"])
    with pytest.raises(SchemaViolation):
        release.score(payload)

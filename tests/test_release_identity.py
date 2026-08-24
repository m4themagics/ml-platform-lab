"""Falsify the identity chain: fingerprint, release record and artifact verification.

The repository's central claim is that a release can be pointed at exactly. These tests attack
that claim from the cheap end -- if a changed dataset or a swapped artifact can keep the same
identifiers, nothing further up the path is worth measuring.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from mlplatform.fingerprint import DatasetFingerprint, file_checksum, fingerprint_frame
from mlplatform.release import UNKNOWN_COMMIT, ReleaseRecord, source_commit, utc_now
from services.fraud_scoring.contract import TARGET_COLUMN
from services.fraud_scoring.data import synthetic_frame

SEED = 11


def record_for(tmp_path: Path, **overrides) -> ReleaseRecord:
    defaults = {
        "workload": "fraud_scoring",
        "schema_version": "fraud_scoring.v1",
        "source_commit": "0" * 40,
        "source_dirty": False,
        "dataset_content_hash": "a" * 64,
        "dataset_schema_hash": "b" * 64,
        "dataset_rows": 1000,
        "training_seed": 1,
        "artifact_path": "models/fraud_scoring/model.joblib",
        "artifact_sha256": "c" * 64,
        "metric_name": "average_precision",
        "metric_value": 0.8,
        "created_at": utc_now(),
    }
    defaults.update(overrides)
    return ReleaseRecord(**defaults)


def test_identical_frames_share_a_content_hash() -> None:
    left = fingerprint_frame(synthetic_frame(rows=200, seed=SEED))
    right = fingerprint_frame(synthetic_frame(rows=200, seed=SEED))
    assert left.content_hash == right.content_hash


def test_one_changed_value_changes_content_but_not_schema() -> None:
    frame = synthetic_frame(rows=200, seed=SEED)
    original = fingerprint_frame(frame)

    mutated = frame.copy()
    mutated.loc[mutated.index[0], "V4"] += 1e-9

    changed = fingerprint_frame(mutated)
    assert changed.content_hash != original.content_hash
    assert changed.schema_hash == original.schema_hash


def test_renaming_a_column_changes_the_schema_hash() -> None:
    frame = synthetic_frame(rows=50, seed=SEED)
    original = fingerprint_frame(frame)
    renamed = fingerprint_frame(frame.rename(columns={"V1": "V1_scaled"}))
    assert renamed.schema_hash != original.schema_hash


def test_changing_a_dtype_changes_the_schema_hash() -> None:
    frame = synthetic_frame(rows=50, seed=SEED)
    original = fingerprint_frame(frame)
    retyped = fingerprint_frame(frame.astype({TARGET_COLUMN: "int64"}))
    assert retyped.schema_hash != original.schema_hash


def test_row_order_is_part_of_dataset_identity() -> None:
    frame = synthetic_frame(rows=100, seed=SEED)
    reversed_frame = frame.iloc[::-1].reset_index(drop=True)
    assert fingerprint_frame(reversed_frame).content_hash != fingerprint_frame(frame).content_hash


def test_fingerprint_survives_a_write_read_round_trip(tmp_path: Path) -> None:
    original = fingerprint_frame(synthetic_frame(rows=20, seed=SEED))
    path = tmp_path / "fingerprint.json"
    original.write(path)
    assert DatasetFingerprint.read(path) == original


def test_release_record_survives_a_write_read_round_trip(tmp_path: Path) -> None:
    original = record_for(tmp_path)
    path = tmp_path / "release.json"
    original.write(path)
    assert ReleaseRecord.read(path) == original


def test_release_built_from_a_dirty_tree_is_not_reproducible(tmp_path: Path) -> None:
    assert record_for(tmp_path, source_dirty=True).is_reproducible() is False
    assert record_for(tmp_path, source_commit=UNKNOWN_COMMIT).is_reproducible() is False
    assert record_for(tmp_path).is_reproducible() is True


def test_file_checksum_detects_a_single_flipped_byte(tmp_path: Path) -> None:
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"release-payload")
    before = file_checksum(path)
    path.write_bytes(b"release-payloae")
    assert file_checksum(path) != before


def test_release_json_is_plain_readable_evidence(tmp_path: Path) -> None:
    path = tmp_path / "release.json"
    record_for(tmp_path).write(path)
    payload = json.loads(path.read_text("utf-8"))
    for key in ("source_commit", "dataset_content_hash", "artifact_sha256", "metric_value"):
        assert key in payload


def test_source_commit_reports_this_repository() -> None:
    commit, _dirty = source_commit()
    assert commit == UNKNOWN_COMMIT or len(commit) == 40


def test_csv_round_trip_preserves_the_content_hash(tmp_path: Path) -> None:
    """The cached dataset is read back from CSV on every run after the first.

    If ``to_csv`` lost a float bit, the fingerprint would differ between the run that downloaded
    the data and every run afterwards, and no release would ever match its own record.
    """
    from services.fraud_scoring.data import canonicalise, read_canonical_csv

    frame = canonicalise(synthetic_frame(rows=300, seed=SEED))
    path = tmp_path / "dataset.csv"
    frame.to_csv(path, index=False)

    restored = canonicalise(read_canonical_csv(path))
    assert fingerprint_frame(restored).content_hash == fingerprint_frame(frame).content_hash


@pytest.mark.parametrize("rows", [1, 2, 500])
def test_fingerprint_row_count_matches_the_frame(rows: int) -> None:
    frame: pd.DataFrame = synthetic_frame(rows=rows, seed=SEED)
    assert fingerprint_frame(frame).rows == rows

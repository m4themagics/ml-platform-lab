"""Load a release and score requests against it.

Loading is where a release stops being trusted and starts being verified. Three things are
checked before the model is allowed to answer anything: the artifact exists, its checksum still
matches the one recorded when the release was built, and the contract stored inside it matches
the contract this code was written against.

The checksum check is not paranoia. It is the local stand-in for the registry failure mode in
docs/architecture.md: a swapped or truncated artifact must fail closed at startup, not produce
confident nonsense at request time.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from mlplatform.fingerprint import file_checksum
from mlplatform.release import ReleaseRecord
from services.fraud_scoring.artifacts import ARTIFACT_PATH, RELEASE_PATH
from services.fraud_scoring.contract import (
    PROVISIONAL_DECISION_THRESHOLD,
    ModelContract,
    SchemaViolation,
    feature_matrix,
    validate_features,
)


class ReleaseIntegrityError(RuntimeError):
    """Raised when the stored release is not the release that was recorded."""


@dataclass(frozen=True)
class LoadedRelease:
    """A verified, ready-to-serve release."""

    record: ReleaseRecord
    contract: ModelContract
    estimator: object

    def score(self, frame: pd.DataFrame) -> np.ndarray:
        """Return P(fraud) for each row. Raises SchemaViolation before touching the model."""
        validate_features(frame, strict=True)
        return self.estimator.predict_proba(feature_matrix(frame))[:, 1]

    def decide(
        self, frame: pd.DataFrame, threshold: float = PROVISIONAL_DECISION_THRESHOLD
    ) -> pd.DataFrame:
        probabilities = self.score(frame)
        return pd.DataFrame(
            {
                "fraud_probability": probabilities,
                "is_fraud": probabilities >= threshold,
                "threshold": threshold,
                "schema_version": self.contract.schema_version,
                "source_commit": self.record.source_commit,
            }
        )


def load_release(
    artifact_path: Path = ARTIFACT_PATH, release_path: Path = RELEASE_PATH
) -> LoadedRelease:
    if not release_path.exists():
        raise ReleaseIntegrityError(f"no release record at {release_path}")
    if not artifact_path.exists():
        raise ReleaseIntegrityError(f"no artifact at {artifact_path}")

    record = ReleaseRecord.read(release_path)

    observed = file_checksum(artifact_path)
    if observed != record.artifact_sha256:
        raise ReleaseIntegrityError(
            f"artifact checksum {observed} does not match recorded {record.artifact_sha256}"
        )

    payload = joblib.load(artifact_path)
    contract = ModelContract(
        schema_version=payload["contract"]["schema_version"],
        features=tuple(payload["contract"]["features"]),
        target=payload["contract"]["target"],
        positive_label=payload["contract"]["positive_label"],
    )
    try:
        contract.assert_compatible_with_current()
    except SchemaViolation as violation:
        raise ReleaseIntegrityError(f"stored model is incompatible: {violation}") from violation

    return LoadedRelease(record=record, contract=contract, estimator=payload["estimator"])

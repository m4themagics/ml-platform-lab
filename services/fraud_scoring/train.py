"""Deterministic training for the fraud scoring workload.

Two properties matter here far more than the model itself:

* the same commit and the same dataset fingerprint must produce the same artifact checksum;
* the artifact must carry its own contract, so a loader can verify it instead of assuming it.

The metric is average precision. With roughly one fraudulent transaction in six hundred, accuracy
is met by predicting "legitimate" forever, and ROC AUC stays flattering because the true-negative
pool is enormous. Average precision is the one that moves when the model stops finding fraud --
which is exactly the regression the rollout gate has to catch.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score

from mlplatform.fingerprint import file_checksum
from mlplatform.release import ReleaseRecord, source_commit, utc_now
from services.fraud_scoring.artifacts import (
    ARTIFACT_PATH,
    METRICS_PATH,
    RELEASE_PATH,
    ROOT,
)
from services.fraud_scoring.contract import (
    SCHEMA_VERSION,
    TARGET_COLUMN,
    WORKLOAD_NAME,
    ModelContract,
    current_model_contract,
    feature_matrix,
)
from services.fraud_scoring.data import build_dataset, time_split

TRAINING_SEED = 20260824
METRIC_NAME = "average_precision"

HYPERPARAMETERS = {
    "max_iter": 120,
    "learning_rate": 0.1,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 40,
    "l2_regularization": 1.0,
    # Off on purpose: automatic early stopping carves out its own validation split, which makes
    # the fitted model depend on a second source of randomness for no gain at this size.
    "early_stopping": False,
    "random_state": TRAINING_SEED,
}


def build_estimator() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(**HYPERPARAMETERS)


def save_artifact(
    estimator: HistGradientBoostingClassifier,
    contract: ModelContract,
    path: Path = ARTIFACT_PATH,
) -> Path:
    """Store the estimator together with the contract it was trained against."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": contract.schema_version,
        "contract": asdict(contract),
        "estimator": estimator,
        "training_seed": TRAINING_SEED,
    }
    joblib.dump(payload, path, compress=0)
    return path


def train(*, refresh_data: bool = False) -> ReleaseRecord:
    frame, fingerprint = build_dataset(refresh=refresh_data)
    train_frame, holdout_frame = time_split(frame)

    estimator = build_estimator()
    estimator.fit(feature_matrix(train_frame), train_frame[TARGET_COLUMN].to_numpy())

    scores = estimator.predict_proba(feature_matrix(holdout_frame))[:, 1]
    metric_value = float(
        average_precision_score(holdout_frame[TARGET_COLUMN].to_numpy(), scores)
    )

    contract = current_model_contract()
    artifact_path = save_artifact(estimator, contract)
    commit, dirty = source_commit()

    record = ReleaseRecord(
        workload=WORKLOAD_NAME,
        schema_version=SCHEMA_VERSION,
        source_commit=commit,
        source_dirty=dirty,
        dataset_content_hash=fingerprint.content_hash,
        dataset_schema_hash=fingerprint.schema_hash,
        dataset_rows=fingerprint.rows,
        training_seed=TRAINING_SEED,
        artifact_path=str(artifact_path.relative_to(ROOT)),
        artifact_sha256=file_checksum(artifact_path),
        metric_name=METRIC_NAME,
        metric_value=metric_value,
        created_at=utc_now(),
    )
    record.write(RELEASE_PATH)

    METRICS_PATH.write_text(
        json.dumps(
            {
                METRIC_NAME: metric_value,
                "positives_in_holdout": int(holdout_frame[TARGET_COLUMN].sum()),
                "rows_train": len(train_frame),
                "rows_holdout": len(holdout_frame),
                "positive_rate_train": float(train_frame[TARGET_COLUMN].mean()),
                "positive_rate_holdout": float(holdout_frame[TARGET_COLUMN].mean()),
                "score_p50": float(np.percentile(scores, 50)),
                "score_p99": float(np.percentile(scores, 99)),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        "utf-8",
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the fraud scoring workload.")
    parser.add_argument(
        "--refresh-data",
        action="store_true",
        help="re-download and rebuild the canonical dataset before training",
    )
    args = parser.parse_args()

    record = train(refresh_data=args.refresh_data)
    print(json.dumps(record.as_dict(), indent=2, sort_keys=True))
    if not record.is_reproducible():
        print("\nWARNING: built from an uncommitted tree; this release cannot be rebuilt.")


if __name__ == "__main__":
    main()

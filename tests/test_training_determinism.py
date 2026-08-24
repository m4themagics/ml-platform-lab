"""The claim that a release can be rebuilt from its identifiers rests on training being a function.

If the same rows and the same seed produce two different artifacts, then a release record points at
something that cannot be recreated, and every identifier downstream of it is decoration.

Synthetic rows again: determinism is a property of the training code, not of the real dataset.
"""

from pathlib import Path

import numpy as np

from mlplatform.fingerprint import file_checksum
from services.fraud_scoring.contract import TARGET_COLUMN, current_model_contract, feature_matrix
from services.fraud_scoring.data import synthetic_frame
from services.fraud_scoring.train import build_estimator, save_artifact

SEED = 5
ROWS = 400


def fit_once(tmp_path: Path, name: str) -> tuple[Path, np.ndarray]:
    frame = synthetic_frame(rows=ROWS, seed=SEED, fraud_rate=0.2)
    estimator = build_estimator().set_params(max_iter=15)
    estimator.fit(feature_matrix(frame), frame[TARGET_COLUMN].to_numpy())

    probe = synthetic_frame(rows=32, seed=SEED + 1, fraud_rate=0.2)
    scores = estimator.predict_proba(feature_matrix(probe))[:, 1]

    path = save_artifact(estimator, current_model_contract(), path=tmp_path / f"{name}.joblib")
    return path, scores


def test_two_runs_of_the_same_input_agree_on_every_prediction(tmp_path: Path) -> None:
    _, first = fit_once(tmp_path, "first")
    _, second = fit_once(tmp_path, "second")
    np.testing.assert_array_equal(first, second)


def test_two_runs_of_the_same_input_produce_the_same_artifact_checksum(tmp_path: Path) -> None:
    first_path, _ = fit_once(tmp_path, "first")
    second_path, _ = fit_once(tmp_path, "second")
    assert file_checksum(first_path) == file_checksum(second_path)


def test_a_different_seed_produces_a_different_dataset_and_model(tmp_path: Path) -> None:
    frame = synthetic_frame(rows=ROWS, seed=SEED, fraud_rate=0.2)
    other = synthetic_frame(rows=ROWS, seed=SEED + 99, fraud_rate=0.2)
    assert not np.array_equal(feature_matrix(frame), feature_matrix(other))

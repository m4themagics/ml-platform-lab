"""Falsify the fraud scoring data contract.

Every test here describes a release that must be rejected. The contract is only worth something
if these fail loudly before a model reaches traffic, so each case is written as the failure it is
meant to catch, not as a happy path with an assertion bolted on.

The frames are synthetic on purpose: a contract test checks shape, not distribution, and CI must
not depend on a 150 MB download.
"""

import numpy as np
import pandas as pd
import pytest

from services.fraud_scoring.contract import (
    FEATURE_COLUMNS,
    ORDER_COLUMN,
    SCHEMA_VERSION,
    TARGET_COLUMN,
    ModelContract,
    SchemaViolation,
    current_model_contract,
    feature_matrix,
    validate_features,
    validate_training_frame,
)
from services.fraud_scoring.data import canonicalise, synthetic_frame, time_split

SEED = 7


@pytest.fixture
def training_frame() -> pd.DataFrame:
    return synthetic_frame(rows=400, seed=SEED)


@pytest.fixture
def payload(training_frame: pd.DataFrame) -> pd.DataFrame:
    return training_frame.loc[:, list(FEATURE_COLUMNS)].head(5).copy()


def test_valid_frames_pass_both_contracts(training_frame, payload) -> None:
    validate_training_frame(training_frame)
    validate_features(payload)


def test_missing_feature_is_named(payload) -> None:
    broken = payload.drop(columns=["V7"])
    with pytest.raises(SchemaViolation) as raised:
        validate_features(broken)
    assert "V7" in str(raised.value)


def test_unknown_column_is_rejected_rather_than_ignored(payload) -> None:
    broken = payload.assign(merchant_country="NL")
    with pytest.raises(SchemaViolation) as raised:
        validate_features(broken)
    assert "merchant_country" in str(raised.value)


def test_non_numeric_feature_is_rejected(payload) -> None:
    broken = payload.astype({"V1": "object"})
    broken.loc[broken.index[0], "V1"] = "high"
    with pytest.raises(SchemaViolation) as raised:
        validate_features(broken)
    assert "V1" in str(raised.value)


def test_missing_values_are_rejected(payload) -> None:
    broken = payload.copy()
    broken.loc[broken.index[0], "V3"] = np.nan
    with pytest.raises(SchemaViolation) as raised:
        validate_features(broken)
    assert "V3" in str(raised.value)


def test_infinite_values_are_rejected(payload) -> None:
    broken = payload.copy()
    broken.loc[broken.index[0], "V5"] = np.inf
    with pytest.raises(SchemaViolation):
        validate_features(broken)


def test_negative_amount_is_rejected(payload) -> None:
    broken = payload.copy()
    broken.loc[broken.index[0], "Amount"] = -1.0
    with pytest.raises(SchemaViolation) as raised:
        validate_features(broken)
    assert "Amount" in str(raised.value)


def test_empty_payload_is_rejected(payload) -> None:
    with pytest.raises(SchemaViolation):
        validate_features(payload.head(0))


def test_all_problems_are_reported_at_once(payload) -> None:
    broken = payload.drop(columns=["V2"]).assign(extra=1.0)
    with pytest.raises(SchemaViolation) as raised:
        validate_features(broken)
    assert len(raised.value.problems) >= 2


def test_single_class_training_frame_is_rejected(training_frame) -> None:
    broken = training_frame.assign(**{TARGET_COLUMN: 0})
    with pytest.raises(SchemaViolation) as raised:
        validate_training_frame(broken)
    assert "both classes" in str(raised.value)


def test_target_outside_the_declared_values_is_rejected(training_frame) -> None:
    broken = training_frame.copy()
    broken.loc[broken.index[0], TARGET_COLUMN] = 7
    with pytest.raises(SchemaViolation) as raised:
        validate_training_frame(broken)
    assert "7" in str(raised.value)


def test_model_declaring_another_schema_version_is_incompatible() -> None:
    stale = ModelContract(
        schema_version="fraud_scoring.v0",
        features=FEATURE_COLUMNS,
        target=TARGET_COLUMN,
        positive_label=1,
    )
    with pytest.raises(SchemaViolation) as raised:
        stale.assert_compatible_with_current()
    assert SCHEMA_VERSION in str(raised.value)


def test_model_with_reordered_features_is_incompatible() -> None:
    reordered = ModelContract(
        schema_version=SCHEMA_VERSION,
        features=(FEATURE_COLUMNS[1], FEATURE_COLUMNS[0], *FEATURE_COLUMNS[2:]),
        target=TARGET_COLUMN,
        positive_label=1,
    )
    with pytest.raises(SchemaViolation) as raised:
        reordered.assert_compatible_with_current()
    assert "different order" in str(raised.value)


def test_current_contract_is_self_compatible() -> None:
    current_model_contract().assert_compatible_with_current()


def test_feature_matrix_ignores_incoming_column_order(payload) -> None:
    shuffled = payload.loc[:, list(reversed(FEATURE_COLUMNS))]
    np.testing.assert_array_equal(feature_matrix(payload), feature_matrix(shuffled))


def test_time_split_never_puts_one_timestamp_on_both_sides() -> None:
    frame = synthetic_frame(rows=500, seed=SEED)
    frame.loc[frame.index[380:420], ORDER_COLUMN] = 1000.0
    frame = canonicalise(frame)

    train, holdout = time_split(frame, holdout_fraction=0.2)

    assert len(train) + len(holdout) == len(frame)
    assert train[ORDER_COLUMN].max() < holdout[ORDER_COLUMN].min()
    assert not set(train[ORDER_COLUMN]) & set(holdout[ORDER_COLUMN])


def test_canonicalise_orders_rows_by_time() -> None:
    frame = synthetic_frame(rows=50, seed=SEED).sample(frac=1.0, random_state=1)
    canonical = canonicalise(frame)
    assert canonical[ORDER_COLUMN].is_monotonic_increasing


def test_synthetic_frames_are_reproducible() -> None:
    left = synthetic_frame(rows=64, seed=SEED)
    right = synthetic_frame(rows=64, seed=SEED)
    pd.testing.assert_frame_equal(left, right)


def test_duplicate_columns_are_reported_as_a_contract_violation(payload) -> None:
    broken = pd.concat([payload, payload[["V1"]]], axis=1)
    with pytest.raises(SchemaViolation) as raised:
        validate_features(broken)
    assert "duplicate" in str(raised.value)

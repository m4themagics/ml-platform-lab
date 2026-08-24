"""Data and model contract for fraud scoring.

Three things are fixed here and nowhere else:

1. which columns exist, with which types, and what is allowed to be missing;
2. what the model accepts and returns;
3. when a candidate is *incompatible* rather than merely worse.

The distinction in (3) is the point of the whole repository. A worse model is a quality problem
and is caught by a metric gate. An incompatible model is a contract problem: it must be rejected
before it ever receives traffic, because no amount of latency budget makes a wrong-shaped
response correct.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

SCHEMA_VERSION = "fraud_scoring.v1"
WORKLOAD_NAME = "fraud_scoring"

#: Anonymised principal components from the source dataset, plus the transaction amount.
FEATURE_COLUMNS: tuple[str, ...] = tuple(f"V{index}" for index in range(1, 29)) + ("Amount",)

TARGET_COLUMN = "Class"

#: Seconds elapsed since the first transaction in the source dataset. Used to order the split and
#: never as a feature: it is a collection offset, so a model that leans on it learns when the data
#: was gathered rather than what a fraudulent transaction looks like.
ORDER_COLUMN = "Time"

TARGET_VALUES = (0, 1)

#: Provisional. The operating point must be chosen from the precision/recall curve and recorded in
#: configs/platform.toml before the first measured run; 0.5 is a placeholder, not a decision.
PROVISIONAL_DECISION_THRESHOLD = 0.5


class SchemaViolation(ValueError):
    """Raised when a frame or payload does not satisfy the data contract.

    Carries every problem found, not just the first: a caller fixing one column at a time cannot
    tell whether a release is one edit or ten edits away from valid.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("; ".join(problems))


@dataclass(frozen=True)
class ModelContract:
    """Stored beside the artifact so a loaded model can be checked, not trusted."""

    schema_version: str
    features: tuple[str, ...]
    target: str
    positive_label: int

    def assert_compatible_with_current(self) -> None:
        problems: list[str] = []
        if self.schema_version != SCHEMA_VERSION:
            problems.append(
                f"schema version {self.schema_version!r} != expected {SCHEMA_VERSION!r}"
            )
        if self.features != FEATURE_COLUMNS:
            missing = [name for name in FEATURE_COLUMNS if name not in self.features]
            unexpected = [name for name in self.features if name not in FEATURE_COLUMNS]
            if missing:
                problems.append(f"model is missing features: {missing}")
            if unexpected:
                problems.append(f"model expects unknown features: {unexpected}")
            if not missing and not unexpected:
                problems.append("model expects the same features in a different order")
        if problems:
            raise SchemaViolation(problems)


def current_model_contract() -> ModelContract:
    return ModelContract(
        schema_version=SCHEMA_VERSION,
        features=FEATURE_COLUMNS,
        target=TARGET_COLUMN,
        positive_label=1,
    )


def _numeric_problems(frame: pd.DataFrame, columns: tuple[str, ...]) -> list[str]:
    problems: list[str] = []
    for name in columns:
        column = frame[name]
        if not pd.api.types.is_numeric_dtype(column):
            problems.append(f"column {name!r} is {column.dtype}, expected a numeric dtype")
            continue
        values = column.to_numpy(dtype="float64", na_value=np.nan)
        if not np.isfinite(values).all():
            problems.append(f"column {name!r} contains missing or non-finite values")
    return problems


def validate_features(frame: pd.DataFrame, *, strict: bool = True) -> None:
    """Validate an inference payload.

    ``strict`` rejects unknown columns. That is deliberate for requests: silently ignoring an
    extra field is how a caller ends up believing it sent a feature that was dropped.
    """
    problems: list[str] = []

    duplicated = sorted({str(name) for name in frame.columns[frame.columns.duplicated()]})
    if duplicated:
        # Left unhandled, a repeated name makes frame[name] a DataFrame and every check below
        # fails with an AttributeError instead of a contract violation.
        raise SchemaViolation([f"duplicate columns: {duplicated}"])

    missing = [name for name in FEATURE_COLUMNS if name not in frame.columns]
    if missing:
        problems.append(f"missing required features: {missing}")

    if strict:
        unexpected = [name for name in frame.columns if name not in FEATURE_COLUMNS]
        if unexpected:
            problems.append(f"unexpected columns: {unexpected}")

    present = tuple(name for name in FEATURE_COLUMNS if name in frame.columns)
    problems.extend(_numeric_problems(frame, present))

    if "Amount" in frame.columns and pd.api.types.is_numeric_dtype(frame["Amount"]):
        amounts = frame["Amount"].to_numpy(dtype="float64", na_value=np.nan)
        negative = int((amounts < 0).sum())
        if negative:
            problems.append(f"{negative} row(s) have a negative Amount")

    if frame.empty:
        problems.append("payload contains no rows")

    if problems:
        raise SchemaViolation(problems)


def validate_training_frame(frame: pd.DataFrame) -> None:
    """Validate a training frame: features, the target, and the column the split is ordered by."""
    problems: list[str] = []

    for name in (TARGET_COLUMN, ORDER_COLUMN):
        if name not in frame.columns:
            problems.append(f"missing required column {name!r}")

    if TARGET_COLUMN in frame.columns:
        observed = set(pd.unique(frame[TARGET_COLUMN].dropna()))
        unknown = observed - set(TARGET_VALUES)
        if unknown:
            problems.append(f"target holds values outside {TARGET_VALUES}: {sorted(unknown)}")
        if frame[TARGET_COLUMN].isna().any():
            problems.append(f"column {TARGET_COLUMN!r} contains missing values")
        if len(observed & set(TARGET_VALUES)) < 2:
            problems.append("training frame does not contain both classes")

    if ORDER_COLUMN in frame.columns:
        problems.extend(_numeric_problems(frame, (ORDER_COLUMN,)))

    if problems:
        raise SchemaViolation(problems)

    validate_features(frame[list(FEATURE_COLUMNS)], strict=True)


def feature_matrix(frame: pd.DataFrame) -> np.ndarray:
    """Materialise features in contract order. Column order is part of the contract."""
    return frame[list(FEATURE_COLUMNS)].to_numpy(dtype="float64")

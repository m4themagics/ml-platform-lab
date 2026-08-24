"""Source data, canonical ordering, deterministic split and synthetic traffic.

The split is by time, not random. Fraud data is collected in sequence, and a shuffled split lets
the model see the future of the same fraud campaign it is being scored on. The holdout therefore
starts where the training window ends, and the cut is pushed to a second boundary so no single
timestamp lands on both sides.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mlplatform.fingerprint import DatasetFingerprint, fingerprint_frame
from services.fraud_scoring.contract import (
    FEATURE_COLUMNS,
    ORDER_COLUMN,
    TARGET_COLUMN,
    validate_training_frame,
)

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DATASET_PATH = PROCESSED_DIR / "fraud_scoring.csv"
FINGERPRINT_PATH = ROOT / "services" / "fraud_scoring" / "dataset_fingerprint.json"

#: Real transactions, downloaded once and never committed. Attribution and licence live in
#: services/fraud_scoring/README.md.
#:
#: Not dataset 1597, which is the same transactions: there ``Time`` is flagged as a row
#: identifier, so scikit-learn silently drops it and the frame arrives with 30 columns instead of
#: 31. The split here is ordered by ``Time``, so losing it would quietly turn a time split into a
#: positional one.
SOURCE = {
    "provider": "openml",
    "data_id": 42175,
    "name": "CreditCardFraudDetection",
    "url": "https://www.openml.org/d/42175",
}

HOLDOUT_FRACTION = 0.2

CANONICAL_COLUMNS: tuple[str, ...] = (ORDER_COLUMN, *FEATURE_COLUMNS, TARGET_COLUMN)


def download_raw_frame() -> pd.DataFrame:
    """Fetch the source dataset. Network is touched here and nowhere else."""
    from sklearn.datasets import fetch_openml

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    bunch = fetch_openml(
        data_id=SOURCE["data_id"],
        as_frame=True,
        data_home=str(RAW_DIR),
        parser="auto",
    )
    return bunch.frame


def _clean_target(column: pd.Series) -> pd.Series:
    """ARFF sources hand back the label as a quoted string or a category."""
    if pd.api.types.is_numeric_dtype(column):
        return column.astype("int8")
    text = column.astype("string").str.strip().str.strip("'\"")
    return pd.to_numeric(text, errors="raise").astype("int8")


def canonicalise(frame: pd.DataFrame) -> pd.DataFrame:
    """Impose the one row and column order every fingerprint of this dataset is taken in."""
    missing = [name for name in CANONICAL_COLUMNS if name not in frame.columns]
    if missing:
        raise KeyError(f"source frame is missing {missing}")

    canonical = frame.loc[:, list(CANONICAL_COLUMNS)].copy()
    canonical[TARGET_COLUMN] = _clean_target(canonical[TARGET_COLUMN])
    for name in (ORDER_COLUMN, *FEATURE_COLUMNS):
        canonical[name] = canonical[name].astype("float64")

    # Stable sort: rows sharing a timestamp keep their source order, so the result is a function
    # of the source alone and the fingerprint does not drift between machines.
    canonical = canonical.sort_values(ORDER_COLUMN, kind="stable").reset_index(drop=True)
    return canonical


def time_split(
    frame: pd.DataFrame, holdout_fraction: float = HOLDOUT_FRACTION
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by time, snapping the cut forward to the next distinct timestamp."""
    if not 0.0 < holdout_fraction < 1.0:
        raise ValueError("holdout_fraction must be strictly between 0 and 1")

    order = frame[ORDER_COLUMN].to_numpy()
    cut = int(len(frame) * (1.0 - holdout_fraction))
    while cut < len(frame) and order[cut] == order[cut - 1]:
        cut += 1

    train = frame.iloc[:cut].reset_index(drop=True)
    holdout = frame.iloc[cut:].reset_index(drop=True)
    if train.empty or holdout.empty:
        raise ValueError("time split produced an empty side")
    return train, holdout


def read_canonical_csv(path: Path) -> pd.DataFrame:
    """Read the cached dataset back without losing a float bit.

    pandas writes a round-trippable repr by default, but its default *reader* uses a fast parser
    that is not correctly rounded, so values come back off by an ulp. That is invisible in any
    metric and fatal here: the fingerprint taken on the run that downloaded the data would never
    again match the fingerprint taken on a cached run, and every release record would point at a
    dataset that no longer reproduces. ``float_precision="round_trip"`` is the correctly rounded
    parser.
    """
    return pd.read_csv(path, float_precision="round_trip")


def build_dataset(*, refresh: bool = False) -> tuple[pd.DataFrame, DatasetFingerprint]:
    """Materialise the canonical dataset and its fingerprint, downloading only when needed."""
    if DATASET_PATH.exists() and not refresh:
        frame = canonicalise(read_canonical_csv(DATASET_PATH))
    else:
        frame = canonicalise(download_raw_frame())
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        frame.to_csv(DATASET_PATH, index=False)

    validate_training_frame(frame)
    fingerprint = fingerprint_frame(frame)
    fingerprint.write(FINGERPRINT_PATH)
    return frame, fingerprint


def synthetic_frame(rows: int, seed: int, *, fraud_rate: float = 0.02) -> pd.DataFrame:
    """Schema-correct rows for tests and load traffic.

    These are not a stand-in for the real distribution and must never train a released model.
    They exist so contract tests run offline and so a load generator can send an unbounded,
    reproducible stream without replaying the same handful of real transactions.
    """
    rng = np.random.default_rng(seed)
    columns: dict[str, np.ndarray] = {
        ORDER_COLUMN: np.sort(rng.uniform(0.0, 172_800.0, size=rows)),
    }
    for name in FEATURE_COLUMNS:
        if name == "Amount":
            columns[name] = np.round(rng.gamma(shape=2.0, scale=40.0, size=rows), 2)
        else:
            columns[name] = rng.normal(0.0, 1.0, size=rows)
    columns[TARGET_COLUMN] = (rng.random(rows) < fraud_rate).astype("int8")

    frame = pd.DataFrame(columns).loc[:, list(CANONICAL_COLUMNS)]
    for name in (ORDER_COLUMN, *FEATURE_COLUMNS):
        frame[name] = frame[name].astype("float64")
    return frame


def main() -> None:
    import json

    _frame, fingerprint = build_dataset()
    print(json.dumps(fingerprint.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

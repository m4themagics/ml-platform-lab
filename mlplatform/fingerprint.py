"""Dataset identity that the platform layer can state without knowing what a column means.

Two hashes are produced on purpose. ``content_hash`` answers "were these exact bytes used";
``schema_hash`` answers "did the shape change". A release that fails only the second one is a
schema break, and that is a different incident from retraining on new rows.

Row order is part of ``content_hash``. A reordered frame is a different dataset unless the
workload canonicalises the order first, which is the workload's job, not the platform's.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ALGORITHM = "sha256"
FORMAT_VERSION = 1

_FIELD_SEPARATOR = b"\x1e"
_VALUE_SEPARATOR = "\x1f"


@dataclass(frozen=True)
class DatasetFingerprint:
    """Immutable identity of one materialised dataset."""

    algorithm: str
    format_version: int
    rows: int
    columns: tuple[str, ...]
    dtypes: tuple[str, ...]
    content_hash: str
    schema_hash: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", "utf-8")

    @classmethod
    def read(cls, path: Path) -> DatasetFingerprint:
        payload = json.loads(path.read_text("utf-8"))
        payload["columns"] = tuple(payload["columns"])
        payload["dtypes"] = tuple(payload["dtypes"])
        return cls(**payload)


def _column_bytes(column: pd.Series) -> bytes:
    values = column.to_numpy()
    if values.dtype == object or pd.api.types.is_string_dtype(column):
        rendered = _VALUE_SEPARATOR.join("" if v is None else str(v) for v in values)
        return rendered.encode("utf-8")
    return np.ascontiguousarray(values).tobytes()


def schema_hash(columns: tuple[str, ...], dtypes: tuple[str, ...]) -> str:
    digest = hashlib.new(ALGORITHM)
    digest.update(str(FORMAT_VERSION).encode("utf-8"))
    for name, dtype in zip(columns, dtypes, strict=True):
        digest.update(_FIELD_SEPARATOR)
        digest.update(f"{name}:{dtype}".encode())
    return digest.hexdigest()


def fingerprint_frame(frame: pd.DataFrame) -> DatasetFingerprint:
    """Fingerprint a frame exactly as it is laid out, column order included."""
    columns = tuple(str(name) for name in frame.columns)
    dtypes = tuple(str(frame[name].dtype) for name in frame.columns)

    digest = hashlib.new(ALGORITHM)
    digest.update(str(FORMAT_VERSION).encode("utf-8"))
    digest.update(str(len(frame)).encode("utf-8"))
    for name in frame.columns:
        digest.update(_FIELD_SEPARATOR)
        digest.update(str(name).encode("utf-8"))
        digest.update(str(frame[name].dtype).encode("utf-8"))
        digest.update(_column_bytes(frame[name]))

    return DatasetFingerprint(
        algorithm=ALGORITHM,
        format_version=FORMAT_VERSION,
        rows=len(frame),
        columns=columns,
        dtypes=dtypes,
        content_hash=digest.hexdigest(),
        schema_hash=schema_hash(columns, dtypes),
    )


def file_checksum(path: Path) -> str:
    """Checksum of a stored artifact, so a swapped file stops being the same release."""
    digest = hashlib.new(ALGORITHM)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

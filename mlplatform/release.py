"""Minimal release identity for the operational surface.

The full chain in docs/architecture.md also runs through an MLflow run and a registered model
version. Those arrive with phase 2. Until then a release is identified by what actually exists:
the source commit, the dataset it was trained on, and the checksum of the produced artifact.

The record deliberately stores no business meaning. It never learns what the metric measures or
what the workload predicts -- it only carries the name the workload gave them.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

UNKNOWN_COMMIT = "unknown"


@dataclass(frozen=True)
class ReleaseRecord:
    """What has to be true about a candidate before anything is packaged from it."""

    workload: str
    schema_version: str
    source_commit: str
    source_dirty: bool
    dataset_content_hash: str
    dataset_schema_hash: str
    dataset_rows: int
    training_seed: int
    artifact_path: str
    artifact_sha256: str
    metric_name: str
    metric_value: float
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", "utf-8")

    @classmethod
    def read(cls, path: Path) -> ReleaseRecord:
        return cls(**json.loads(path.read_text("utf-8")))

    def is_reproducible(self) -> bool:
        """A release built from uncommitted files cannot be rebuilt from its own identifiers."""
        return not self.source_dirty and self.source_commit != UNKNOWN_COMMIT


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def source_commit() -> tuple[str, bool]:
    """Return the current commit and whether the tree carries uncommitted changes."""
    commit = _git("rev-parse", "HEAD")
    if commit is None:
        return UNKNOWN_COMMIT, True
    status = _git("status", "--porcelain")
    return commit, bool(status)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()

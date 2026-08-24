"""Where a built release lives on disk.

Kept apart from ``train`` so that serving never imports training code. The inference image has no
reason to carry a training stack, and an import edge from serving to training is how that ends up
happening by accident.
"""

from __future__ import annotations

from pathlib import Path

from services.fraud_scoring.contract import WORKLOAD_NAME

ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = ROOT / "models" / WORKLOAD_NAME
ARTIFACT_PATH = MODEL_DIR / "model.joblib"
RELEASE_PATH = MODEL_DIR / "release.json"
METRICS_PATH = MODEL_DIR / "metrics.json"

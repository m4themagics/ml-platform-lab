"""Guard honest scope and unresolved platform decisions before implementation begins."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "platform.toml"

REQUIRED_SECTIONS = {
    "project",
    "identity",
    "environments",
    "release_gates",
    "slo",
    "recovery",
    "cost",
    "kafka_extension",
}


def load_config() -> dict:
    with CONFIG.open("rb") as stream:
        return tomllib.load(stream)


def test_config_declares_every_platform_decision_layer() -> None:
    assert REQUIRED_SECTIONS <= set(load_config())


def test_scaffold_does_not_claim_deployed_infrastructure() -> None:
    config = load_config()
    assert config["project"]["status"] == "scaffold"
    assert config["environments"]["local"]["enabled"] is False
    assert config["environments"]["cloud"]["enabled"] is False
    assert config["environments"]["cloud"]["apply_enabled"] is False


def test_release_identity_is_immutable() -> None:
    identity = load_config()["identity"]
    assert identity["registered_model_version_required"] is True
    assert identity["image_digest_required"] is True
    assert identity["deployment_reference"] == "immutable_model_version_and_image_digest"


def test_measurement_thresholds_remain_visibly_unset() -> None:
    config = load_config()
    assert config["release_gates"]["quality_threshold"] == "UNSET"
    assert config["slo"]["availability_target"] == "UNSET"
    assert config["slo"]["load_profile"] == "UNSET"
    assert config["recovery"]["drill_repetitions"] == "UNSET"
    assert config["cost"]["budget_limit"] == "UNSET"


def test_kafka_stays_closed_until_failure_semantics_exist() -> None:
    extension = load_config()["kafka_extension"]
    assert extension["enabled"] is False
    assert extension["requires_idempotency_contract"] is True
    assert extension["requires_consumer_lag_drill"] is True

"""Integration test for TER-v2.3 provider configuration audit."""

from __future__ import annotations

import json
from pathlib import Path

import tools.provider_utils.ntpe_provider_audit as audit

ROOT = Path(__file__).resolve().parents[2]


def test_provider_config_has_env_vars() -> None:
    data = json.loads((ROOT / "config" / "provider_config.json").read_text(encoding="utf-8"))
    providers = data["providers"]
    assert "nvidia" in providers
    assert providers["nvidia"]["env_var"] == "NVIDIA_API_KEY"
    assert all(config.get("env_var") for config in providers.values())


def test_audit_core_checks_pass_or_warn() -> None:
    items = audit.run_audit("nvidia")
    status_by_name = {item.name: item.status for item in items}
    assert status_by_name["Provider Config"] == "PASS"
    assert status_by_name["Hardcoded API Keys"] == "PASS"
    assert status_by_name["Runtime Provider Path"] in {"PASS", "WARN"}
    assert status_by_name["Legacy Config"] in {"PASS", "WARN"}

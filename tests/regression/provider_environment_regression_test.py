"""Regression test for provider environment template and verification logic."""

from __future__ import annotations

import os

import tools.provider_utils.ntpe_provider_setup as setup
import tools.provider_utils.ntpe_provider_verify as verify


def test_export_template_contains_known_env_vars() -> None:
    path = setup.export_template()
    text = path.read_text(encoding="utf-8")
    assert "NVIDIA_API_KEY=" in text
    assert "OPENAI_API_KEY=" in text
    assert "GEMINI_API_KEY=" in text
    assert "nvapi-" not in text


def test_verify_can_allow_missing_key(monkeypatch) -> None:
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    assert verify.verify("nvidia", require_key=False) == 0

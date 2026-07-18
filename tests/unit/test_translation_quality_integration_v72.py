from __future__ import annotations

from core.translation_quality_integration_v72 import QualityIntegrationFlags


def test_flags_default_off() -> None:
    assert QualityIntegrationFlags().enabled is False

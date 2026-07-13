from pathlib import Path

from ntpe_te_v700_stage011_adaptive_context_safety_stabilization_test import main


def test_stage011_safety_stabilization() -> None:
    assert main() == 0


def test_stage011_frozen_boundary_and_no_runtime_hook() -> None:
    from core.adaptive_context import ACE_VERSION
    from core.translation_release import TE_V6_FROZEN, TE_V6_STABLE_VERSION

    root = Path(__file__).resolve().parents[2]
    ace_source = "\n".join(path.read_text(encoding="utf-8") for path in (root / "core/adaptive_context").glob("*.py"))
    assert ACE_VERSION == "7.0.0-stage01.1"
    assert TE_V6_STABLE_VERSION == "6.0.0" and TE_V6_FROZEN is True
    assert "requests." not in ace_source and "httpx." not in ace_source
    assert "NVIDIA" not in ace_source

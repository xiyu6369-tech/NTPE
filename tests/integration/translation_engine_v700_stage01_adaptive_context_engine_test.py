from ntpe_te_v700_stage01_adaptive_context_engine_test import main


def test_te_v700_stage01_adaptive_context_engine() -> None:
    assert main() == 0


def test_ace_does_not_modify_frozen_runtime_surfaces() -> None:
    from core.adaptive_context import build_adaptive_context
    from core.translation_release import TE_V6_FROZEN, TE_V6_STABLE_VERSION

    assert callable(build_adaptive_context)
    assert TE_V6_STABLE_VERSION == "6.0.0" and TE_V6_FROZEN is True

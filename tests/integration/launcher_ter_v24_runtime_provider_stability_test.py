from pathlib import Path


def test_ter_v24_runtime_provider_stability_entrypoint_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "ntpe_ter_v24_runtime_provider_stability_test.py").exists()


def test_timeout_explicit_marker_is_set_by_launcher() -> None:
    root = Path(__file__).resolve().parents[2]
    data = (root / "ntpe_production_translate.py").read_text(encoding="utf-8")
    assert "NTPE_API_TIMEOUT_EXPLICIT" in data
    assert "--api-timeout" in data

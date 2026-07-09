from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import lts.txt_translation_runtime as runtime
from lts.txt_translation_runtime import TxtTranslationOptions, apply_runtime_speed_policy, build_prompt_package, translate_txt
from ntpe_production_translate import build_parser


def test_balanced_runtime_package_carries_speed_limits() -> None:
    options = apply_runtime_speed_policy(
        TxtTranslationOptions(input_path=Path("sample.txt"), output_dir=Path("output"), speed="balanced")
    )
    package = build_prompt_package(
        options=options,
        chunk_text="鄭泰義嘔了一口氣。",
        chunk_index=1,
        chunk_total=1,
        locked_dictionary={},
    )
    runtime = package["runtime"]
    assert runtime["speed"] == "balanced"
    assert runtime["provider_attempts"] == 2
    assert runtime["qa_attempts"] == 2
    assert runtime["speed_timeout"] == 120
    assert runtime["naturalness_retry_limit"] == 1


def test_cli_speed_and_chunk_size_defaults_are_policy_driven() -> None:
    parser = build_parser()
    args = parser.parse_args(["txt", "input.txt", "output", "--speed", "fast", "--api-timeout", "100"])
    assert args.speed == "fast"
    assert args.chunk_size is None
    assert args.api_timeout == 100

    explicit = parser.parse_args(["txt", "input.txt", "output", "--speed", "quality", "--chunk-size", "1500"])
    assert explicit.chunk_size == 1500


def test_user_api_timeout_is_not_expanded_by_speed_policy() -> None:
    old_env = dict(os.environ)
    try:
        os.environ["NTPE_API_TIMEOUT"] = "100"
        os.environ["NTPE_API_TIMEOUT_EXPLICIT"] = "1"
        options = apply_runtime_speed_policy(
            TxtTranslationOptions(input_path=Path("sample.txt"), output_dir=Path("output"), speed="quality")
        )
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    assert options.runtime_timeout == 100


def _write_source(root: Path) -> Path:
    source = root / "sample.txt"
    source.write_text("source text for runtime speed policy integration\n", encoding="utf-8")
    return source


def _naturalness_error_report() -> dict:
    return {
        "passed": False,
        "issues": [{"code": "NATURALNESS_GUARD", "severity": "error", "retry_worthy": True}],
        "metrics": {},
    }


def test_balanced_naturalness_issue_after_retry_passes_with_warning(monkeypatch, tmp_path) -> None:
    root = tmp_path / "NTPE"
    root.mkdir()
    source = _write_source(root)

    class FakeEngine:
        calls = 0

        def __init__(self, root=None):
            self.root = root

        def translate_package(self, package, package_path=None):
            FakeEngine.calls += 1
            out = root / f"provider_output_{FakeEngine.calls}.txt"
            out.write_text("translated output with naturalness issue\n", encoding="utf-8")
            return {"status": "success", "output_path": str(out)}

    monkeypatch.setattr(runtime, "TranslationEngine", FakeEngine)
    monkeypatch.setattr(runtime, "analyze_translation_quality", lambda *args, **kwargs: _naturalness_error_report())

    result = translate_txt(
        TxtTranslationOptions(input_path=source, output_dir=root / "out", speed="balanced", retry_base_seconds=0, progress_enabled=False),
        root=root,
    )

    assert result["status"] == "success"
    assert FakeEngine.calls == 2
    assert result["records"][0]["status"] == "pass_with_warning"
    assert result["records"][0]["qa"]["status"] == "pass_with_warning"
    assert result["records"][0]["qa"]["issues"][0]["severity"] == "warning"


def test_quality_naturalness_issue_can_still_fail(monkeypatch, tmp_path) -> None:
    root = tmp_path / "NTPE"
    root.mkdir()
    source = _write_source(root)

    class FakeEngine:
        calls = 0

        def __init__(self, root=None):
            self.root = root

        def translate_package(self, package, package_path=None):
            FakeEngine.calls += 1
            out = root / f"provider_output_{FakeEngine.calls}.txt"
            out.write_text("translated output with quality naturalness issue\n", encoding="utf-8")
            return {"status": "success", "output_path": str(out)}

    monkeypatch.setattr(runtime, "TranslationEngine", FakeEngine)
    monkeypatch.setattr(runtime, "analyze_translation_quality", lambda *args, **kwargs: _naturalness_error_report())

    result = translate_txt(
        TxtTranslationOptions(input_path=source, output_dir=root / "out", speed="quality", retry_base_seconds=0, progress_enabled=False),
        root=root,
    )

    assert result["status"] == "failed"
    assert result["failed_chunk"] == 1
    assert FakeEngine.calls == 2
    assert result["qa"]["issues"][0]["code"] == "NATURALNESS_GUARD"


def test_balanced_hard_errors_still_fail(monkeypatch, tmp_path) -> None:
    root = tmp_path / "NTPE"
    root.mkdir()
    source = _write_source(root)

    class FakeEngine:
        def __init__(self, root=None):
            self.root = root

        def translate_package(self, package, package_path=None):
            out = root / "provider_output.txt"
            out.write_text("translated output with hard issue\n", encoding="utf-8")
            return {"status": "success", "output_path": str(out)}

    hard_report = {
        "passed": False,
        "issues": [
            {"code": "NATURALNESS_GUARD", "severity": "error", "retry_worthy": True},
            {"code": "KOREAN_RESIDUE", "severity": "error"},
        ],
        "metrics": {},
    }
    monkeypatch.setattr(runtime, "TranslationEngine", FakeEngine)
    monkeypatch.setattr(runtime, "analyze_translation_quality", lambda *args, **kwargs: hard_report)

    result = translate_txt(
        TxtTranslationOptions(input_path=source, output_dir=root / "out", speed="balanced", retry_base_seconds=0, progress_enabled=False),
        root=root,
    )

    assert result["status"] == "failed"
    assert result["failed_chunk"] == 1
    assert any(issue["code"] == "KOREAN_RESIDUE" for issue in result["qa"]["issues"])


def test_fast_naturalness_issue_does_not_retry(monkeypatch, tmp_path) -> None:
    root = tmp_path / "NTPE"
    root.mkdir()
    source = _write_source(root)

    class FakeEngine:
        calls = 0

        def __init__(self, root=None):
            self.root = root

        def translate_package(self, package, package_path=None):
            FakeEngine.calls += 1
            out = root / "provider_output.txt"
            out.write_text("translated output with warning only\n", encoding="utf-8")
            return {"status": "success", "output_path": str(out)}

    warning_report = {
        "passed": True,
        "issues": [{"code": "NATURALNESS_GUARD", "severity": "warning", "retry_worthy": False}],
        "metrics": {},
    }
    monkeypatch.setattr(runtime, "TranslationEngine", FakeEngine)
    monkeypatch.setattr(runtime, "analyze_translation_quality", lambda *args, **kwargs: warning_report)

    result = translate_txt(
        TxtTranslationOptions(input_path=source, output_dir=root / "out", speed="fast", retry_base_seconds=0, progress_enabled=False),
        root=root,
    )

    assert result["status"] == "success"
    assert FakeEngine.calls == 1
    assert result["records"][0]["qa_attempt"] == 1
    assert result["records"][0]["qa"]["issues"][0]["severity"] == "warning"


if __name__ == "__main__":
    test_balanced_runtime_package_carries_speed_limits()
    test_cli_speed_and_chunk_size_defaults_are_policy_driven()
    test_user_api_timeout_is_not_expanded_by_speed_policy()
    print("PASS")

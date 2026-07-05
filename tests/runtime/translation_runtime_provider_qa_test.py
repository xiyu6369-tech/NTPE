from pathlib import Path

from core.translation_runtime import (
    RuntimeProviderAdapter,
    RuntimeProviderPolicy,
    TranslationRuntime,
    analyze_runtime_quality,
    is_retryable_provider_error,
)


class FakeEngine:
    def __init__(self):
        self.calls = 0

    def translate_package(self, package, package_path=None):
        self.calls += 1
        if self.calls == 1:
            return {"status": "failed", "error": "503 service unavailable"}
        return {"status": "success", "package_id": package["package_id"], "output_path": "out.txt"}


def test_provider_adapter_retries_retryable_errors():
    engine = FakeEngine()
    adapter = RuntimeProviderAdapter(engine, RuntimeProviderPolicy(max_retries=1, retry_base_seconds=0))
    result = adapter.translate_package({"package_id": "p1"})
    assert result["status"] == "success"
    assert result["provider_attempt"] == 2
    assert result["provider_trace"]["total_attempts"] == 2
    assert is_retryable_provider_error("429 rate limit")


def test_runtime_exposes_quality_boundary():
    result = analyze_runtime_quality("정태의는 문 앞에 섰다.", "鄭泰義站在門前。")
    assert result["passed"]
    failed = TranslationRuntime(root=Path(__file__).resolve().parents[2]).analyze_quality("정태의는 문 앞에 섰다.", "정태의는 문 앞")
    assert not failed["passed"]
    assert any(issue["code"] == "KOREAN_RESIDUE" for issue in failed["issues"])

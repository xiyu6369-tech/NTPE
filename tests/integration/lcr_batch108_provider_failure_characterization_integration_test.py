import hashlib
import json
from pathlib import Path

from core.provider_failure_characterization import FailureType, summarize_execution


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "audits/legacy_capability_recovery/batch10_7/LCR_BATCH107_EXECUTION_RESULT.json"


def test_batch107_execution_result_is_characterized_read_only_without_provider_calls():
    before = FIXTURE.read_bytes()
    before_hash = hashlib.sha256(before).hexdigest()
    result = json.loads(before.decode("utf-8"))
    summary = summarize_execution(result)
    after = FIXTURE.read_bytes()
    assert after == before and hashlib.sha256(after).hexdigest() == before_hash
    assert summary.execution_id == "lcr-batch107-tic-case-b2-8ae44c56c7ad3de4a6fd-chunk-000001"
    assert summary.provider == "nvidia" and summary.model == "meta/llama-3.2-90b-vision-instruct"
    assert summary.failure_type is FailureType.TIMEOUT
    assert summary.provider_request_count == summary.network_request_count == 1
    assert summary.batch108_provider_requests_added == 0
    assert summary.batch108_network_requests_added == 0
    assert summary.authorization_consumed and summary.execution_consumed
    assert not summary.candidate_available and not summary.semantic_verification_run
    assert not summary.rollback_required and summary.manual_review_required and summary.production_safe
    assert not summary.retry_allowed and not summary.fallback_allowed


def test_batch108_package_has_no_runtime_provider_or_network_dependency():
    package = ROOT / "core/provider_failure_characterization"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("*.py"))
    forbidden = (
        "requests.", "urllib.request", "http.client", "NvidiaClient",
        "ProviderManager", "launcher_translate", "ntpe_production_translate",
        "os.environ", "NVIDIA_API_KEY", "execute_batch107",
    )
    assert all(marker not in sources for marker in forbidden)


def test_production_hook_count_remains_one():
    calls = []
    for path in (ROOT / "core").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "run_read_only_lcr_shadow_hook(package)" in text:
            calls.append(path.relative_to(ROOT).as_posix())
    assert calls == ["core/adaptive_context_runtime_shadow/hook.py"]


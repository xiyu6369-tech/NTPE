from __future__ import annotations

from core.prompt_contract_verification_canary import CanaryConfig, validate_output

SOURCE = "그녀는 창가에 서서 조용히 비를 바라보았다."

def test_budget_attempt_retry_and_fallback_are_hard_limited() -> None:
    assert CanaryConfig("id", "bad").blockers() == ["authorization_invalid"]
    invalid = CanaryConfig("id", "bad", authorized_request_budget=3, attempts_per_arm=2, retry=1, fallback=True, parallelism=2)
    assert {"request_budget_must_equal_two", "attempt_or_retry_policy_invalid", "fallback_parallel_or_rerun_forbidden"} <= set(invalid.blockers())

def test_hangul_echo_labels_and_malformed_responses_fail_closed() -> None:
    for value in (SOURCE, "譯文：她站在窗邊。", "【Output】她站在窗邊。", ""):
        assert validate_output(SOURCE, value, success=bool(value), timeout=False, malformed=not bool(value))["status"] == "FAIL"
    assert validate_output(SOURCE, "她靜靜站在窗邊望著雨。", success=True, timeout=False, malformed=False)["status"] == "PASS"

def test_timeout_is_not_reviewable_and_cannot_be_successful() -> None:
    result = validate_output(SOURCE, "", success=False, timeout=True, malformed=False)
    assert "timeout" in result["failures"]

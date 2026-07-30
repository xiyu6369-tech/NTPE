from __future__ import annotations

from pathlib import Path

from core.translation_runtime.runtime_qa import soft_fail_naturalness_report
from core.translation_runtime.runtime_speed_policy import effective_timeout, get_runtime_speed_policy
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    analyze_translation_quality,
    apply_runtime_speed_policy,
    has_retry_worthy_naturalness_issue,
)


def test_speed_policy_values() -> None:
    fast = get_runtime_speed_policy("fast")
    balanced = get_runtime_speed_policy("balanced")
    quality = get_runtime_speed_policy("quality")

    assert (fast.provider_attempts, fast.qa_attempts, fast.timeout_seconds, fast.chunk_size, fast.naturalness_retry) == (2, 1, 90, 1200, "off")
    assert (balanced.provider_attempts, balanced.qa_attempts, balanced.timeout_seconds, balanced.chunk_size, balanced.naturalness_retry) == (2, 2, 120, 1000, "high_confidence_only")
    assert (quality.provider_attempts, quality.qa_attempts, quality.timeout_seconds, quality.chunk_size, quality.naturalness_retry) == (3, 2, 180, 800, "full")


def test_balanced_does_not_use_legacy_four_by_four_defaults() -> None:
    options = apply_runtime_speed_policy(TxtTranslationOptions(input_path=Path("sample.txt"), output_dir=Path("output"), speed="balanced"))
    assert options.provider_attempts == 2
    assert options.qa_attempts == 2
    assert options.provider_attempts != 4
    assert options.qa_attempts != 4


def test_user_timeout_is_upper_bound() -> None:
    quality = get_runtime_speed_policy("quality")
    fast = get_runtime_speed_policy("fast")
    assert effective_timeout(quality, user_timeout=100) == 100
    assert effective_timeout(fast, user_timeout=180) == 90


def test_chunk_size_policy_respects_user_override() -> None:
    auto_fast = apply_runtime_speed_policy(TxtTranslationOptions(input_path=Path("sample.txt"), output_dir=Path("output"), speed="fast"))
    explicit = apply_runtime_speed_policy(
        TxtTranslationOptions(input_path=Path("sample.txt"), output_dir=Path("output"), speed="quality", chunk_size=1500, chunk_size_explicit=True)
    )
    assert auto_fast.chunk_size == 1200
    assert explicit.chunk_size == 1500


def test_balanced_naturalness_retry_is_limited_to_one() -> None:
    options = apply_runtime_speed_policy(
        TxtTranslationOptions(input_path=Path("sample.txt"), output_dir=Path("output"), speed="balanced", quality_profile="literary", min_length_ratio=0.0)
    )
    report = analyze_translation_quality("source", "鄭泰義嘔了一口氣。", options, locked_dictionary={})
    retry_count = 0
    if has_retry_worthy_naturalness_issue(report):
        retry_count += 1
    assert report["passed"] is False
    assert options.naturalness_retry_limit == 1
    assert retry_count <= options.naturalness_retry_limit


def test_quality_enables_full_naturalness_retry() -> None:
    options = apply_runtime_speed_policy(
        TxtTranslationOptions(input_path=Path("sample.txt"), output_dir=Path("output"), speed="quality", quality_profile="quality", min_length_ratio=0.0)
    )
    report = analyze_translation_quality("source", "觀光客人纏繞在一起。", options, locked_dictionary={})
    issue = next(item for item in report["issues"] if item["code"] == "NATURALNESS_GUARD")
    assert options.provider_attempts == 3
    assert options.qa_attempts == 2
    assert issue["retry_worthy"] is True


def test_balanced_naturalness_after_retry_soft_fails() -> None:
    report = {
        "passed": False,
        "issues": [{"code": "NATURALNESS_GUARD", "severity": "error", "retry_worthy": True}],
        "metrics": {},
    }
    softened = soft_fail_naturalness_report(report, "balanced")
    assert softened["passed"] is True
    assert softened["status"] == "pass_with_warning"
    assert softened["issues"][0]["severity"] == "warning"
    assert softened["issues"][0]["retry_worthy"] is False


def test_quality_naturalness_can_still_fail() -> None:
    report = {
        "passed": False,
        "issues": [{"code": "NATURALNESS_GUARD", "severity": "error", "retry_worthy": True}],
        "metrics": {},
    }
    softened = soft_fail_naturalness_report(report, "quality")
    assert softened["passed"] is False
    assert softened["issues"][0]["severity"] == "error"


def test_balanced_hard_errors_still_fail() -> None:
    report = {
        "passed": False,
        "issues": [
            {"code": "NATURALNESS_GUARD", "severity": "error", "retry_worthy": True},
            {"code": "KOREAN_RESIDUE", "severity": "error"},
        ],
        "metrics": {},
    }
    softened = soft_fail_naturalness_report(report, "balanced")
    assert softened["passed"] is False
    assert softened["issues"][1]["code"] == "KOREAN_RESIDUE"


if __name__ == "__main__":
    test_speed_policy_values()
    test_balanced_does_not_use_legacy_four_by_four_defaults()
    test_user_timeout_is_upper_bound()
    test_chunk_size_policy_respects_user_override()
    test_balanced_naturalness_retry_is_limited_to_one()
    test_quality_enables_full_naturalness_retry()
    test_balanced_naturalness_after_retry_soft_fails()
    test_quality_naturalness_can_still_fail()
    test_balanced_hard_errors_still_fail()
    print("NTPE TE-v3.0 Stage-02.2 Runtime Speed Policy PASS")

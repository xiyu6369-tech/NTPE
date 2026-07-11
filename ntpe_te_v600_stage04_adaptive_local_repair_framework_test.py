from __future__ import annotations

from pathlib import Path

from core.translation_discipline import (
    LOCAL_REPAIR_FRAMEWORK_VERSION,
    AdaptiveLocalRepairFramework,
)


def _report(*issues: tuple[str, str]) -> dict:
    return {
        "merged_issues": [
            {
                "code": code,
                "severity": "medium",
                "metadata": {"discipline_route": route},
            }
            for code, route in issues
        ]
    }


def main() -> int:
    framework = AdaptiveLocalRepairFramework()

    result = framework.repair(
        "他請到一周的假期。那個雇員說：“你好。”",
        _report(
            ("SIMPLIFIED_CHINESE", "local_repair"),
            ("DIALOGUE_QUOTE_FORMAT", "local_repair"),
        ),
    )
    assert result.changed
    assert "一週" in result.text
    assert "僱員" in result.text
    assert "「你好。」" in result.text
    assert set(result.repaired_codes) == {"SIMPLIFIED_CHINESE", "DIALOGUE_QUOTE_FORMAT"}
    assert not result.metadata["provider_called"]
    print("Deterministic local repairs applied       PASS")

    naturalness = framework.repair(
        "被拋在遠國的男人。",
        _report(("NATURALNESS_GUARD", "local_repair")),
    )
    assert not naturalness.changed
    assert naturalness.unresolved_codes == ("NATURALNESS_GUARD",)
    print("Subjective naturalness is not rewritten  PASS")

    blocking = framework.repair(
        "短譯文",
        _report(("PARAGRAPH_OMISSION_SUSPECTED", "provider_retry")),
    )
    assert not blocking.changed
    assert not blocking.attempted_codes
    print("Provider-blocking issues remain untouched PASS")

    runtime = Path("lts/txt_translation_runtime.py").read_text(encoding="utf-8")
    assert "apply_adaptive_local_repairs" in runtime
    assert "revalidated=true" in runtime
    assert "run_quality_v5_phase1" in runtime
    print("Runtime repair and revalidation wired    PASS")

    assert LOCAL_REPAIR_FRAMEWORK_VERSION == "6.0.0-stage04"
    print("Stage 04 metadata version                PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from importlib import import_module
from pathlib import Path

EXPECTED_EXPORTS = (
    "RETRY_DECISION_ENGINE_VERSION",
    "ACCEPT",
    "ACCEPT_WITH_WARNINGS",
    "LOCAL_REPAIR",
    "PROVIDER_RETRY",
    "REJECT",
    "AdaptiveRetryDecisionEngine",
    "RetryDecision",
    "apply_adaptive_retry_decision",
)


def main() -> int:
    print("NTPE TE v6.0 Stage 08.1 Import & API Compatibility Fix")
    print("=" * 72)

    module_path = Path("core/translation_discipline/retry_decision_engine.py")
    assert module_path.is_file(), module_path
    print("Retry decision module exists                         PASS")

    module = import_module("core.translation_discipline.retry_decision_engine")
    assert module.RETRY_DECISION_ENGINE_VERSION == "6.0.0-stage05"
    print("Retry decision module imports                       PASS")

    package = import_module("core.translation_discipline")
    missing = [name for name in EXPECTED_EXPORTS if not hasattr(package, name)]
    assert not missing, missing
    print("Public package exports complete                     PASS")

    engine = package.AdaptiveRetryDecisionEngine()
    decision = engine.decide({"decision": "accepted", "merged_issues": []})
    assert decision.action == package.ACCEPT
    assert decision.accepted is True
    print("Public decision engine API operational              PASS")

    metadata = decision.to_metadata()
    assert metadata["version"] == "6.0.0-stage05"
    assert metadata["action"] == "accept"
    print("Decision metadata contract preserved                PASS")

    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

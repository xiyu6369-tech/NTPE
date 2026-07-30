from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeReadinessGateContract, RuntimeReadinessGateEvaluator


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def _ready_state() -> dict:
    return {
        "freezes": {f"TE-v3.{version}": True for version in range(2, 7)},
        "checks": {
            "feature_flag_present": True,
            "disabled_guard_present": True,
            "optin_hook_present": True,
            "preflight_present": True,
            "boundary_regression_present": True,
        },
        "mode": "mock_only",
    }


def test_readiness_evaluator_safe_defaults_and_ready_report() -> None:
    evaluator = RuntimeReadinessGateEvaluator()
    contract = RuntimeReadinessGateContract().build_contract()

    assert evaluator.is_ready(evaluator.evaluate()) is False
    assert evaluator.evaluate(contract=contract)["status"] == "not_ready"

    ready = evaluator.evaluate(contract=contract, state=_ready_state())
    assert ready["ready"] is True
    assert ready["status"] == "ready"
    assert ready["missing_freezes"] == []
    assert ready["missing_checks"] == []
    assert ready["unsafe_conditions"] == []
    assert ready["next_allowed_mode"] == "mock_only"
    assert ready["real_runtime_allowed"] is False
    assert evaluator.is_ready(ready) is True
    assert evaluator.validate_report(ready)["valid"] is True


def test_readiness_evaluator_rejects_missing_and_unsafe_evidence() -> None:
    evaluator = RuntimeReadinessGateEvaluator()
    contract = RuntimeReadinessGateContract().build_contract()

    missing_freeze = _ready_state()
    missing_freeze["freezes"]["TE-v3.6"] = False
    assert evaluator.evaluate(contract, missing_freeze)["missing_freezes"] == ["TE-v3.6"]

    missing_check = _ready_state()
    missing_check["checks"]["preflight_present"] = False
    assert evaluator.evaluate(contract, missing_check)["missing_checks"] == ["preflight_present"]

    unsafe_contract = {**contract, "runtime_touch_mode": "read", "real_translation": True}
    unsafe = evaluator.evaluate(unsafe_contract, _ready_state())
    assert unsafe["ready"] is False
    assert "runtime_touch_mode_not_none" in unsafe["unsafe_conditions"]
    assert "real_translation_not_false" in unsafe["unsafe_conditions"]

    wrong_mode = _ready_state()
    wrong_mode["mode"] = "enabled"
    assert "state_mode_not_mock_only" in evaluator.evaluate(contract, wrong_mode)["unsafe_conditions"]


def test_readiness_evaluator_has_no_external_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    watched = ["core.translation_engine.provider_runtime", "lts.txt_translation_runtime", "requests", "httpx"]
    before = {name: name in sys.modules for name in watched}
    try:
        evaluator = RuntimeReadinessGateEvaluator()
        report = evaluator.evaluate(RuntimeReadinessGateContract().build_contract(), _ready_state())
        assert evaluator.validate_report(report)["valid"] is True
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert {name: name in sys.modules for name in watched} == before
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_readiness_evaluator_safe_defaults_and_ready_report()
    test_readiness_evaluator_rejects_missing_and_unsafe_evidence()
    test_readiness_evaluator_has_no_external_side_effects()
    print("NTPE TE-v3.7 Stage-3.7.2 Runtime Readiness Gate Evaluator PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from core.translation_scheduler import ControlledRuntimeTrialContract


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifests" / "te_v38_controlled_runtime_trial_contract_manifest.json"
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_controlled_runtime_trial_contract() -> None:
    builder = ControlledRuntimeTrialContract()
    contract = builder.build_contract(metadata={"profile": "controlled-trial"})
    description = builder.describe_trial()

    assert contract["version"] == "TE-v3.8"
    assert contract["stage"] == "3.8.1"
    assert contract["default_mode"] == "disabled"
    assert contract["activation_mode"] == "explicit_opt_in_only"
    assert contract["execution_mode"] == "contract_only"
    assert contract["real_translation"] is False
    assert contract["real_runtime_execution"] is False
    assert contract["rollback_mode"] == "immediate_disable"
    assert contract["required_freezes"] == [f"TE-v3.{index}" for index in range(2, 8)]
    assert set(contract["required_prechecks"]) == set(builder.required_prechecks)
    assert set(contract["forbidden_trial_inputs"]) == set(builder.forbidden_trial_inputs)
    assert contract["provider_access"] == contract["http_access"] == contract["api_key_access"] == "forbidden"
    assert contract["launcher_touch_mode"] == contract["translation_runtime_touch_mode"] == "none"
    assert contract["safety_guarantees"]["execution_allowed"] is False
    assert contract["safety_guarantees"]["real_runtime_allowed"] is False
    assert builder.validate_contract(contract)["valid"] is True
    assert description == {
        "current_stage": "3.8.1",
        "current_mode": "contract_only",
        "execution_allowed": False,
        "real_runtime_allowed": False,
        "rollback_available": True,
        "provider_connected": False,
        "launcher_modified": False,
        "translation_runtime_modified": False,
    }


def test_manifest_validation_and_no_runtime_side_effects() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    watched_modules = (
        "core.translation_engine.provider_runtime",
        "core.production_runtime",
        "lts.txt_translation_runtime",
        "requests",
        "httpx",
    )
    before_modules = {name: name in sys.modules for name in watched_modules}
    try:
        builder = ControlledRuntimeTrialContract()
        contract = builder.build_contract()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        assert manifest["version"] == contract["version"]
        assert manifest["stage"] == contract["stage"]
        assert manifest["layer"] == contract["trial_layer"]
        assert manifest["execution_mode"] == "contract_only"
        assert manifest["required_freezes"] == contract["required_freezes"]
        assert manifest["required_prechecks"] == contract["required_prechecks"]

        unsafe = {**contract, "real_runtime_execution": True}
        assert builder.validate_contract(unsafe)["valid"] is False
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert {name: name in sys.modules for name in watched_modules} == before_modules
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_controlled_runtime_trial_contract()
    test_manifest_validation_and_no_runtime_side_effects()
    print("NTPE TE-v3.8 Stage-3.8.1 Controlled Runtime Trial Contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import ControlledRuntimeTrialContract


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_stage381_contract_is_contract_only_and_side_effect_free() -> None:
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
        description = builder.describe_trial()

        assert builder.validate_contract(contract)["valid"] is True
        assert contract["default_mode"] == "disabled"
        assert contract["activation_mode"] == "explicit_opt_in_only"
        assert contract["execution_mode"] == "contract_only"
        assert contract["rollback_mode"] == "immediate_disable"
        assert contract["real_translation"] is False
        assert contract["real_runtime_execution"] is False
        assert contract["safety_guarantees"]["execution_allowed"] is False
        assert contract["safety_guarantees"]["real_runtime_allowed"] is False
        assert description["provider_connected"] is False
        assert description["launcher_modified"] is False
        assert description["translation_runtime_modified"] is False

        assert os.environ.get("NVIDIA_API_KEY") is None
        assert {name: name in sys.modules for name in watched_modules} == before_modules
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

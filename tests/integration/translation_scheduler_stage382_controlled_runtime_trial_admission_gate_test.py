from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import ControlledRuntimeTrialAdmissionGate, ControlledRuntimeTrialContract


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = ROOT / "launcher_translate.py"


def test_stage382_admits_only_safe_metadata_for_future_isolated_dry_run() -> None:
    gate = ControlledRuntimeTrialAdmissionGate()
    contract = ControlledRuntimeTrialContract().build_contract()
    readiness = {
        "approved": True,
        "decision": "approved_for_mock_only",
        "next_allowed_mode": "mock_only",
        "real_runtime_allowed": False,
        "execution_allowed": False,
    }
    request = {
        "request_type": "controlled_runtime_trial",
        "runtime_id": "integration-382",
        "caller": "translation_runtime",
        "trial_mode": "isolated_dry_run",
        "chunk_count": 1,
        "chunk_metadata": [{"chunk_index": 1}],
    }
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    watched = (
        "core.translation_engine.provider_runtime",
        "core.production_runtime",
        "lts.txt_translation_runtime",
        "requests",
        "httpx",
    )
    before = {name: name in sys.modules for name in watched}
    try:
        admitted = gate.evaluate(request, contract, readiness, {"enabled": True})
        rejected = gate.evaluate(
            {**request, "payload": [{"nested": {"text": "must not survive"}}]},
            contract,
            readiness,
            {"enabled": True},
        )

        assert gate.is_admitted(admitted) is True
        assert admitted["execution_allowed"] is False
        assert admitted["real_runtime_allowed"] is False
        assert admitted["rollback_available"] is True
        assert gate.validate_result(admitted)["valid"] is True
        assert rejected["status"] == "rejected"
        assert "forbidden_input_present" in rejected["failed_checks"]
        assert "must not survive" not in str(rejected)
        assert gate.validate_result(rejected)["valid"] is True
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert {name: name in sys.modules for name in watched} == before
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key

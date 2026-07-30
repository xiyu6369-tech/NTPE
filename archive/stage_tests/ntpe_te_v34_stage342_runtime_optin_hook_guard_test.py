from __future__ import annotations

import os
import sys
from pathlib import Path

from core.translation_scheduler import RuntimeIntegrationFeatureFlag, RuntimeOptInHookContract, RuntimeOptInHookGuard


ROOT = Path(__file__).resolve().parent
LAUNCHER_PATH = ROOT / "launcher_translate.py"
SECRET_TEXT = "hook guard secret text"


def test_runtime_optin_hook_guard_rules() -> None:
    contract_builder = RuntimeOptInHookContract()
    contract = contract_builder.build_contract()
    flag = RuntimeIntegrationFeatureFlag()
    guard = RuntimeOptInHookGuard()
    valid_request = {
        "caller": "translation_runtime",
        "runtime_id": "runtime-342",
        "request_type": "hook",
        "source_text": SECRET_TEXT,
        "chunks": [SECRET_TEXT],
    }

    missing = guard.guard(contract=contract, flag_state=flag.resolve(config={"runtime_scheduler_integration_enabled": True}))
    wrong_caller = guard.guard(
        request={**valid_request, "caller": "launcher"},
        contract=contract,
        flag_state=flag.resolve(config={"runtime_scheduler_integration_enabled": True}),
    )
    disabled = guard.guard(request=valid_request, contract=contract, flag_state=flag.resolve())
    non_mock = guard.guard(
        request=valid_request,
        contract={**contract, "execution_mode": "real"},
        flag_state=flag.resolve(config={"runtime_scheduler_integration_enabled": True}),
    )
    allowed = guard.guard(
        request=valid_request,
        contract=contract,
        flag_state=flag.resolve(config={"runtime_scheduler_integration_enabled": True}),
    )

    assert missing["blocked"] is True
    assert missing["reason"] == "missing_request"
    assert wrong_caller["blocked"] is True
    assert wrong_caller["reason"] == "invalid_caller"
    assert disabled["blocked"] is True
    assert disabled["reason"] == "runtime_integration_disabled"
    assert non_mock["blocked"] is True
    assert non_mock["reason"] == "non_mock_execution_mode"
    assert allowed["allowed"] is True
    assert allowed["blocked"] is False
    assert allowed["reason"] == "hook_allowed"
    assert guard.is_allowed(allowed) is True

    for result in (missing, wrong_caller, disabled, non_mock, allowed):
        assert result["stage"] == "3.4.2"
        assert result["safety_boundaries"]["provider_runtime"] == "external"
        assert result["safety_boundaries"]["http_client"] == "forbidden"
        assert result["safety_boundaries"]["api_key"] == "forbidden"
        assert result["safety_boundaries"]["launcher_flow"] == "unchanged"
        assert result["safety_boundaries"]["translation_runtime_flow"] == "unchanged"
        assert result["safety_boundaries"]["real_translation"] == "forbidden"
        assert SECRET_TEXT not in str(result)
        assert guard.validate_guard_result(result)["valid"] is True


def test_runtime_optin_hook_guard_does_not_touch_runtime_dependencies() -> None:
    old_key = os.environ.pop("NVIDIA_API_KEY", None)
    launcher_before = LAUNCHER_PATH.read_text(encoding="utf-8")
    before_provider = "core.translation_engine.provider_runtime" in sys.modules
    before_translation_runtime = "lts.txt_translation_runtime" in sys.modules
    before_requests = "requests" in sys.modules
    before_httpx = "httpx" in sys.modules
    try:
        flag = RuntimeIntegrationFeatureFlag()
        contract = RuntimeOptInHookContract().build_contract()
        guard = RuntimeOptInHookGuard()
        result = guard.guard(
            request={"caller": "translation_runtime", "text": SECRET_TEXT},
            contract=contract,
            flag_state=flag.resolve(config={"runtime_scheduler_integration_enabled": True}),
        )

        assert result["allowed"] is True
        assert SECRET_TEXT not in str(result)
        assert os.environ.get("NVIDIA_API_KEY") is None
        assert ("core.translation_engine.provider_runtime" in sys.modules) == before_provider
        assert ("lts.txt_translation_runtime" in sys.modules) == before_translation_runtime
        assert ("requests" in sys.modules) == before_requests
        assert ("httpx" in sys.modules) == before_httpx
        assert LAUNCHER_PATH.read_text(encoding="utf-8") == launcher_before
    finally:
        if old_key is not None:
            os.environ["NVIDIA_API_KEY"] = old_key


def main() -> int:
    test_runtime_optin_hook_guard_rules()
    test_runtime_optin_hook_guard_does_not_touch_runtime_dependencies()
    print("NTPE TE-v3.4 Stage-3.4.2 Runtime Opt-in Hook Guard PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

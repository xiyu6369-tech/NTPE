from dataclasses import fields

import pytest

from core.controlled_translation_runtime_integration import (
    ControlledTranslationDispatchVerificationError,
    ControlledTranslationExecutor,
    ControlledTranslationOutputError,
    ControlledTranslationProviderConfigurationError,
    ControlledTranslationProviderRequestError,
    ControlledTranslationQualityError,
    verify_controlled_translation_runtime_execution,
)
from core.controlled_translation_runtime_integration.diagnostics import (
    ProviderFailure, Stage73NvidiaDiagnosticTransport,
)
from core.controlled_translation_runtime_integration.models import (
    ControlledTranslationExecutionRequest,
)
from tests.unit.controlled_translation_runtime_integration import (
    FAKE_TRANSLATION, build_context,
)


def test_authentic_dispatch_to_one_isolated_output(tmp_path):
    context = build_context(tmp_path)
    result, evidence = ControlledTranslationExecutor().execute(**context)
    assert result.provider_requests == result.provider_attempts == 1
    assert result.retries == result.fallbacks == 0
    assert evidence.chunk_count == 1 and evidence.source_character_count == 455
    assert (context["artifact_root"] / result.output_artifact_path).is_file()
    assert verify_controlled_translation_runtime_execution(
        context["request"], result, evidence,
        dispatch_package=context["dispatch_package"],
        artifact_root=context["artifact_root"],
        raise_on_error=True,
    ).valid


def test_dispatch_tamper_rejected(tmp_path):
    context = build_context(tmp_path)
    request = context["request"]
    values = {item.name: getattr(request, item.name) for item in fields(request) if item.init}
    values["dispatch_key"] = "0" * 64
    context["request"] = ControlledTranslationExecutionRequest(**values)
    with pytest.raises(ControlledTranslationDispatchVerificationError):
        ControlledTranslationExecutor().execute(**context)


def test_output_overwrite_is_blocked_before_second_provider_call(tmp_path):
    context = build_context(tmp_path)
    ControlledTranslationExecutor().execute(**context)
    second = build_context(tmp_path / "second")
    second["artifact_root"] = context["artifact_root"]
    with pytest.raises(ControlledTranslationOutputError):
        ControlledTranslationExecutor().execute(**second)
    assert second["transport"].calls == 0


@pytest.mark.parametrize("output", [
    "", "일레이 정태의 " * 30, "譯文：這是錯誤包裝。",
    "相同段落。\n\n相同段落。\n\n相同段落。",
    "錯誤\ufffd內容" * 20,
])
def test_invalid_outputs_fail_quality_closed(tmp_path, output):
    with pytest.raises(ControlledTranslationQualityError):
        ControlledTranslationExecutor().execute(
            **build_context(tmp_path, output=output)
        )


def test_real_mode_requires_gate_and_credential(tmp_path):
    context = build_context(tmp_path)
    context.update(execution_mode="real", transport=None, environ={})
    with pytest.raises(ControlledTranslationProviderConfigurationError):
        ControlledTranslationExecutor().execute(**context)

def test_real_provider_failure_writes_only_redacted_diagnostic(tmp_path):
    class FailedDiagnosticTransport(Stage73NvidiaDiagnosticTransport):
        def invoke(self, payload, plan, *, provider_url, api_key):
            self.network_requests = 1
            self.failure = ProviderFailure(
                exception_type="RuntimeError",
                cause_type="",
                http_status=429,
                provider_error_code="rate_limit",
                redacted_message="request rate limit exceeded",
                error_category="provider_rate_limit",
            )
            return {
                "status": "failed",
                "error": self.failure.redacted_message,
                "http_status": 429,
            }

    context = build_context(tmp_path)
    context.update(
        execution_mode="real",
        transport=FailedDiagnosticTransport(),
        environ={
            "NTPE_STAGE73_REAL_PROVIDER_CANARY": "1",
            "NVIDIA_API_KEY": "must-not-be-persisted",
        },
    )
    with pytest.raises(ControlledTranslationProviderRequestError):
        ControlledTranslationExecutor().execute(**context)
    diagnostic_paths = list(
        context["artifact_root"].glob("*.provider-diagnostic.json")
    )
    assert len(diagnostic_paths) == 1
    text = diagnostic_paths[0].read_text(encoding="utf-8")
    assert "must-not-be-persisted" not in text
    assert '"http_status": 429' in text
    assert '"provider_error_code": "rate_limit"' in text
    assert not list(context["artifact_root"].glob("*.translated.txt"))

"""Redacted deterministic diagnostics for the Stage 7.3 Provider canary."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from urllib.parse import urlsplit

from core.adaptive_context_provider_benchmark_session import ProviderAttemptPlan
from core.translation_engine.nvidia_client import NvidiaClient

from .serialization import canonical_json


DIAGNOSTIC_SCHEMA = "ntpe.controlled_translation_runtime_provider_diagnostic"
DIAGNOSTIC_VERSION = "1.0"
_HTTP_ERROR = re.compile(r"^NVIDIA API error (\d{3}):\s*(.*)$", re.DOTALL)
_SECRET = re.compile(
    r"(?i)(bearer\s+)[^\s\"']+|"
    r"((?:api[_ -]?key|authorization|token)[\"']?\s*[:=]\s*)[^\s,;}]+"
)


def _safe_text(value: object, *, limit: int = 240) -> str:
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    text = _SECRET.sub(lambda match: f"{match.group(1) or match.group(2)}[REDACTED]", text)
    return text[:limit]


def _provider_error(body: str) -> tuple[str, str]:
    try:
        payload = json.loads(body)
    except (TypeError, ValueError):
        return "", _safe_text(body)
    if not isinstance(payload, Mapping):
        return "", "provider returned an HTTP error"
    error = payload.get("error", payload)
    if isinstance(error, Mapping):
        code = _safe_text(error.get("code", ""), limit=80)
        message = _safe_text(
            error.get("message") or error.get("detail") or "provider returned an HTTP error"
        )
        return code, message
    return "", _safe_text(error)


@dataclass(frozen=True)
class ProviderFailure:
    exception_type: str
    cause_type: str
    http_status: int | None
    provider_error_code: str
    redacted_message: str
    error_category: str


@dataclass(frozen=True)
class ControlledTranslationProviderDiagnostic:
    execution_request_id: str
    dispatch_package_id: str
    source_fixture_id: str
    provider: str
    model_id: str
    endpoint_host: str
    endpoint_identity: str
    exception_type: str
    cause_type: str
    http_status: int | None
    provider_error_code: str
    redacted_provider_message: str
    redacted_error_category: str
    connect_timeout_seconds: int
    read_timeout_seconds: int
    streaming: bool
    authentication_present: bool
    payload_schema: str
    message_roles: tuple[str, ...]
    message_content_types: tuple[str, ...]
    max_output_tokens: int
    unsupported_parameters: tuple[str, ...]
    rate_limit_rpm: int
    request_count: int
    attempt_count: int
    retry_count: int = 0
    fallback_count: int = 0
    parallel_request_count: int = 0
    automatic_rollout_count: int = 0
    formal_output_replacement_count: int = 0
    full_source_persisted: bool = False
    full_prompt_persisted: bool = False
    full_payload_persisted: bool = False
    full_response_persisted: bool = False
    credential_persisted: bool = False
    authorization_header_persisted: bool = False
    no_secret_confirmation: bool = True
    schema: str = field(default=DIAGNOSTIC_SCHEMA, init=False)
    version: str = field(default=DIAGNOSTIC_VERSION, init=False)

    def to_json(self) -> str:
        return canonical_json(asdict(self))


@dataclass
class Stage73NvidiaDiagnosticTransport:
    """The authentic NVIDIA client with Stage 7.3-only safe failure capture."""

    provenance: str = "real"
    network_requests: int = 0
    captured_output: object = field(default="", init=False, repr=False)
    failure: ProviderFailure | None = field(default=None, init=False)
    connect_timeout_seconds: int = field(default=10, init=False)
    read_timeout_seconds: int = field(default=60, init=False)
    rate_limit_rpm: int = field(default=40, init=False)

    def invoke(
        self, payload: Mapping[str, object], plan: ProviderAttemptPlan, *,
        provider_url: str, api_key: str,
    ) -> Mapping[str, object]:
        prompt = payload.get("prompt", {})
        if not isinstance(prompt, Mapping):
            return self._local_failure(ValueError("provider payload prompt is invalid"))
        system_prompt = prompt.get("system_prompt")
        user_prompt = prompt.get("user_prompt")
        if not isinstance(system_prompt, str) or not isinstance(user_prompt, str):
            return self._local_failure(ValueError("provider message content is invalid"))
        client = NvidiaClient(
            api_key=api_key, api_url=provider_url, timeout=plan.timeout_seconds,
        )
        self.connect_timeout_seconds = client.connect_timeout
        self.read_timeout_seconds = client.timeout
        self.rate_limit_rpm = client.rpm_limit
        self.network_requests += 1
        try:
            output = client.chat(
                model=plan.model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.12,
                top_p=0.82,
                max_tokens=max(1, plan.estimated_output_tokens),
            )
        except RuntimeError as error:
            self.failure = _classify_failure(error)
            result: dict[str, object] = {
                "status": "failed",
                "error": self.failure.redacted_message,
            }
            if self.failure.http_status is not None:
                result["http_status"] = self.failure.http_status
            return result
        self.captured_output = output
        return {
            "status": "success",
            "provider_model": plan.model,
            "fallback_used": plan.fallback_used,
            "estimated_input_tokens": plan.estimated_input_tokens,
            "estimated_output_tokens": plan.estimated_output_tokens,
            "usage_source": "estimate",
        }

    def _local_failure(self, error: Exception) -> Mapping[str, object]:
        self.failure = _classify_failure(error)
        return {"status": "failed", "error": self.failure.redacted_message}


def _classify_failure(error: Exception) -> ProviderFailure:
    message = str(error)
    status = None
    code = ""
    safe_message = ""
    category = "provider_request"
    match = _HTTP_ERROR.match(message)
    if match:
        status = int(match.group(1))
        code, safe_message = _provider_error(match.group(2))
        if status == 401:
            category = "authentication"
        elif status == 403:
            category = "authorization"
        elif status == 404:
            category = "endpoint_or_model"
        elif status == 422:
            category = "payload_validation"
        elif status == 429:
            category = "provider_rate_limit"
        elif status >= 500:
            category = "provider_service"
        else:
            category = "provider_http"
    elif "timeout" in message.lower():
        category = "timeout"
        safe_message = "provider request timed out"
    elif "response format" in message.lower():
        category = "response_parsing"
        safe_message = "provider response format invalid"
    elif "request failed" in message.lower():
        category = "connection_dns_tls"
        safe_message = _safe_text(message.removeprefix("NVIDIA API request failed:"))
    else:
        safe_message = _safe_text(message) or "provider invocation failed"
    cause = error.__cause__
    return ProviderFailure(
        exception_type=type(error).__name__,
        cause_type=type(cause).__name__ if cause is not None else "",
        http_status=status,
        provider_error_code=code,
        redacted_message=safe_message,
        error_category=category,
    )


def build_provider_diagnostic(
    *, request, dispatch_package, transport: Stage73NvidiaDiagnosticTransport,
    provider: str, model: str, provider_url: str, authentication_present: bool,
    max_output_tokens: int,
) -> ControlledTranslationProviderDiagnostic:
    failure = transport.failure or ProviderFailure(
        exception_type="RuntimeError",
        cause_type="",
        http_status=None,
        provider_error_code="",
        redacted_message="provider attempt did not succeed",
        error_category="provider_request",
    )
    endpoint = urlsplit(provider_url)
    return ControlledTranslationProviderDiagnostic(
        execution_request_id=request.execution_request_id,
        dispatch_package_id=dispatch_package.dispatch_package_id,
        source_fixture_id=request.source_fixture_id,
        provider=provider,
        model_id=model,
        endpoint_host=endpoint.hostname or "",
        endpoint_identity=endpoint.path,
        exception_type=failure.exception_type,
        cause_type=failure.cause_type,
        http_status=failure.http_status,
        provider_error_code=failure.provider_error_code,
        redacted_provider_message=failure.redacted_message,
        redacted_error_category=failure.error_category,
        connect_timeout_seconds=transport.connect_timeout_seconds,
        read_timeout_seconds=transport.read_timeout_seconds,
        streaming=False,
        authentication_present=authentication_present,
        payload_schema="openai-compatible-chat-completions",
        message_roles=("system", "user"),
        message_content_types=("string", "string"),
        max_output_tokens=max_output_tokens,
        unsupported_parameters=(),
        rate_limit_rpm=transport.rate_limit_rpm,
        request_count=transport.network_requests,
        attempt_count=1,
    )

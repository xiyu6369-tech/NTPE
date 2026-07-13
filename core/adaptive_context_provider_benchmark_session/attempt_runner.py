from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping

from core.adaptive_context_provider_evidence import (
    ProviderEvidenceCollector, ProviderRequestIdentity,
)

from .model import ProviderAttemptPlan
from .provider_bridge import ProviderCallable, invoke_provider_unchanged


def run_caller_owned_attempts(
    *, collector: ProviderEvidenceCollector, identity: ProviderRequestIdentity,
    payload: Mapping[str, object], plans: Iterable[ProviderAttemptPlan], provider: ProviderCallable,
) -> tuple[int, bool, bool]:
    executed = 0
    payload_preserved = True
    prompt_preserved = True
    for plan in plans:
        attempt_identity = replace(
            identity, attempt=plan.attempt, model=plan.model,
            minimum_output_tokens=identity.minimum_output_tokens,
        )
        if attempt_identity.resumed:
            collector.collect_attempt(attempt_identity, {})
            break
        handle = collector.begin_attempt(attempt_identity)
        result, payload_ok, prompt_ok = invoke_provider_unchanged(provider, payload, plan)
        result["provider_model"] = str(result.get("provider_model") or plan.model)
        result["fallback_used"] = bool(result.get("fallback_used", plan.fallback_used))
        result["estimated_input_tokens"] = int(result.get("estimated_input_tokens", plan.estimated_input_tokens) or 0)
        result["estimated_output_tokens"] = int(result.get("estimated_output_tokens", plan.estimated_output_tokens) or 0)
        collector.finish_attempt(handle, result)
        executed += 1
        payload_preserved = payload_preserved and payload_ok
        prompt_preserved = prompt_preserved and prompt_ok
        if str(result.get("status", "")).lower() in {"success", "accepted"}:
            break
    return executed, payload_preserved, prompt_preserved

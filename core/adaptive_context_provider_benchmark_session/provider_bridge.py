from __future__ import annotations

import copy
from collections.abc import Callable, Mapping, MutableMapping

from .integrity import payload_fingerprint
from .model import ProviderAttemptPlan

ProviderCallable = Callable[[MutableMapping[str, object], ProviderAttemptPlan], Mapping[str, object]]


def invoke_provider_unchanged(
    provider: ProviderCallable,
    payload: Mapping[str, object],
    plan: ProviderAttemptPlan,
) -> tuple[dict[str, object], bool, bool]:
    before = payload_fingerprint(payload)
    prompt_before = payload_fingerprint(payload.get("prompt", {})) if isinstance(payload.get("prompt"), Mapping) else ""
    provider_payload = copy.deepcopy(dict(payload))
    try:
        result = provider(provider_payload, plan)
    except TimeoutError:
        result = {"status": "failed", "error": "provider request timed out"}
    except Exception as exc:
        result = {"status": "failed", "error": f"provider exception {type(exc).__name__}"}
    if not isinstance(result, Mapping):
        result = {"status": "failed", "error": "provider result type invalid"}
    payload_preserved = before == payload_fingerprint(payload)
    prompt_after = payload_fingerprint(payload.get("prompt", {})) if isinstance(payload.get("prompt"), Mapping) else ""
    return dict(result), payload_preserved, prompt_before == prompt_after

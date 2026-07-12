from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from core.adaptive_context_integration import integrate_adaptive_context, resolve_mode
from core.adaptive_context_integration.utils import canonical_hash
from core.adaptive_context_canary import apply_prompt_package_canary

from .audit import write_shadow_audit
from .model import ShadowAuditRecord
from .registry import append_shadow_record

SHADOW_RUNTIME_VERSION = "7.0.0-stage03"
_ORIGINAL_ATTR = "_ntpe_te_v7_stage03_original_build_prompt_package"
_WRAPPED_ATTR = "_ntpe_te_v7_stage03_shadow_wrapped"


def _sanitized_metrics(metrics: dict[str, object] | Any) -> dict[str, object]:
    allowed = {
        "mode", "baseline_context_tokens", "ace_context_tokens",
        "estimated_tokens_saved", "estimated_reduction_ratio",
        "baseline_item_count", "ace_selected_count", "ace_omitted_count",
        "ace_compressed_count", "admissible", "fallback_required",
        "fallback_reasons", "ace_fingerprint", "ace_build_latency_ms",
        "raw_context_retained",
    }
    source = dict(metrics or {})
    return {key: source[key] for key in sorted(allowed) if key in source}


def analyze_prompt_package_shadow(package: dict[str, object]) -> ShadowAuditRecord | None:
    effective_mode, _ = resolve_mode(None)
    if effective_mode != "shadow":
        return None
    before = canonical_hash(package)
    result = integrate_adaptive_context(package, context_key="context", mode="shadow")
    after = canonical_hash(package)
    record = ShadowAuditRecord(
        version=SHADOW_RUNTIME_VERSION,
        package_id=str(package.get("package_id", "")),
        mode="shadow",
        payload_hash_before=before,
        payload_hash_after=after,
        payload_equivalent=before == after and result.prompt_payload_hash == result.baseline_payload_hash,
        provider_calls_added=0,
        metrics=_sanitized_metrics(result.metrics),
    )
    append_shadow_record(record)
    write_shadow_audit(record)
    return record


def install_txt_runtime_shadow_hook() -> bool:
    import lts.txt_translation_runtime as runtime

    current = runtime.build_prompt_package
    if getattr(current, _WRAPPED_ATTR, False):
        return False

    original: Callable[..., dict[str, object]] = current

    @functools.wraps(original)
    def wrapped(*args: Any, **kwargs: Any) -> dict[str, object]:
        package = original(*args, **kwargs)
        apply_prompt_package_canary(package)
        analyze_prompt_package_shadow(package)
        return package

    setattr(wrapped, _WRAPPED_ATTR, True)
    setattr(runtime, _ORIGINAL_ATTR, original)
    runtime.build_prompt_package = wrapped
    return True


def uninstall_txt_runtime_shadow_hook() -> bool:
    import lts.txt_translation_runtime as runtime

    original = getattr(runtime, _ORIGINAL_ATTR, None)
    if original is None:
        return False
    runtime.build_prompt_package = original
    delattr(runtime, _ORIGINAL_ATTR)
    return True

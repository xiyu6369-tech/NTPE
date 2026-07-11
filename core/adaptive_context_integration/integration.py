from __future__ import annotations
import time
from collections.abc import Mapping
from core.adaptive_context import build_adaptive_context, estimate_tokens
from .adapter import adapt_runtime_context
from .admission import admission_reasons
from .mode import resolve_mode
from .model import ACEIntegrationResult
from .utils import canonical_hash

INTEGRATION_VERSION = '7.0.0-stage02'

def integrate_adaptive_context(
    prompt_payload: Mapping[str, object], *, context_key: str = 'context', mode: str | None = None,
    active_characters: tuple[str, ...] = (), model_context_limit: int = 8192,
    fixed_prompt_tokens: int = 0, source_tokens: int = 0, reserved_output_tokens: int = 1024,
    requested_context_tokens: int | None = None,
) -> ACEIntegrationResult:
    requested = mode if mode is not None else ''
    effective_mode, mode_reasons = resolve_mode(mode)
    baseline_payload = dict(prompt_payload)
    original = baseline_payload.get(context_key, {})
    if not isinstance(original, Mapping): original = {'context': original}
    original_dict = dict(original)
    baseline_hash = canonical_hash(baseline_payload)
    if effective_mode == 'disabled':
        return ACEIntegrationResult(INTEGRATION_VERSION, requested, 'disabled', original_dict, original_dict,
            baseline_payload, baseline_hash, baseline_hash, False, bool(mode_reasons), mode_reasons,
            {'raw_context_retained': False, 'mode': 'disabled'})
    items = adapt_runtime_context(original_dict)
    baseline_tokens = sum(estimate_tokens(item.content) for item in items)
    start = time.perf_counter_ns()
    ace = build_adaptive_context(items, active_characters=active_characters, model_context_limit=model_context_limit,
        fixed_prompt_tokens=fixed_prompt_tokens, source_tokens=source_tokens, reserved_output_tokens=reserved_output_tokens,
        requested_context_tokens=requested_context_tokens)
    elapsed_ms = round((time.perf_counter_ns()-start)/1_000_000, 3)
    reasons = admission_reasons(items, ace, baseline_tokens)
    candidate = {row.item_id: row.content for row in ace.selected}
    metrics = {
        'mode': effective_mode, 'baseline_context_tokens': baseline_tokens, 'ace_context_tokens': ace.estimated_tokens,
        'estimated_tokens_saved': max(0, baseline_tokens-ace.estimated_tokens),
        'estimated_reduction_ratio': round((baseline_tokens-ace.estimated_tokens)/baseline_tokens, 6) if baseline_tokens else 0.0,
        'baseline_item_count': len(items), 'ace_selected_count': len(ace.selected), 'ace_omitted_count': len(ace.omitted_ids),
        'ace_compressed_count': sum(1 for row in ace.selected if row.compressed), 'admissible': not reasons,
        'fallback_required': bool(reasons), 'fallback_reasons': reasons, 'ace_fingerprint': ace.fingerprint,
        'ace_build_latency_ms': elapsed_ms, 'raw_context_retained': False,
    }
    if effective_mode == 'shadow':
        return ACEIntegrationResult(INTEGRATION_VERSION, requested, 'shadow', original_dict, original_dict,
            baseline_payload, baseline_hash, baseline_hash, False, False, reasons, metrics)
    if reasons:
        return ACEIntegrationResult(INTEGRATION_VERSION, requested, 'active', original_dict, original_dict,
            baseline_payload, baseline_hash, baseline_hash, False, True, reasons, metrics)
    active_payload = dict(baseline_payload); active_payload[context_key] = candidate
    return ACEIntegrationResult(INTEGRATION_VERSION, requested, 'active', original_dict, candidate,
        active_payload, canonical_hash(active_payload), baseline_hash, True, False, (), metrics)

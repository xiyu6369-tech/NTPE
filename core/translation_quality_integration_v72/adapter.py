from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any, Mapping

from core.literary.prompt_profiler import estimate_tokens

from .budget import allocate_prompt_budget
from .errors import TranslationQualityIntegrationError
from .flags import QualityIntegrationFlags
from .models import PromptBudget, QualityIntegrationMetadata, QualityIntegrationRequest, QualityIntegrationResult
from .prompt_contract import serialize_candidate_prompt
from .renderer import NATURALNESS_POLICY, render_quality_sections
from .selection import select_quality_context


INTEGRATION_VERSION = "7.2.0-milestone-a"
ACTIVATION_GATE = "translation_quality_integration_ready_for_controlled_canary"


def _fingerprint(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _metadata(request: QualityIntegrationRequest, selected: object, section: str, exhausted: bool, *, status: str = "applied") -> QualityIntegrationMetadata:
    character_tokens = sum(item.estimated_tokens for item in selected.character_items)
    context_tokens = sum(item.estimated_tokens for item in selected.context_items)
    scene_tokens = sum(item.estimated_tokens for item in selected.scene_items)
    naturalness_tokens = estimate_tokens(NATURALNESS_POLICY) if request.flags.naturalness_enabled and NATURALNESS_POLICY in section else 0
    identity = {
        "version": INTEGRATION_VERSION,
        "character": [item.memory_id for item in selected.character_items],
        "context": [item.item_id for item in selected.context_items],
        "scene": [item.item_id for item in selected.scene_items],
        "section_sha256": hashlib.sha256(section.encode("utf-8")).hexdigest(),
        "flags": request.flags.to_dict(),
    }
    return QualityIntegrationMetadata(
        enabled=request.flags.enabled,
        character_records_considered=selected.character_considered,
        character_records_selected=len(selected.character_items),
        context_records_considered=selected.context_considered,
        context_records_selected=len(selected.context_items),
        scene_records_selected=len(selected.scene_items),
        character_tokens=character_tokens,
        context_tokens=context_tokens,
        scene_tokens=scene_tokens,
        naturalness_tokens=naturalness_tokens,
        total_added_tokens=estimate_tokens(section) if section else 0,
        budget_exhausted=exhausted,
        selection_fingerprint=_fingerprint(identity),
        flags=request.flags.to_dict(),
        status=status,
    )


def integrate_prompt(user_prompt: str, request: QualityIntegrationRequest) -> QualityIntegrationResult:
    if not request.flags.enabled:
        empty = type("EmptySelection", (), {"character_items": (), "context_items": (), "scene_items": (), "character_considered": 0, "context_considered": 0})()
        return QualityIntegrationResult(user_prompt, "", _metadata(request, empty, "", False, status="disabled"))
    if not request.source_text.strip():
        raise TranslationQualityIntegrationError("source_text must not be empty")
    allocation = allocate_prompt_budget(
        request.base_prompt_tokens,
        request.budget,
        naturalness_text=NATURALNESS_POLICY if request.flags.naturalness_enabled else "",
    )
    selected = select_quality_context(
        request,
        character_budget=allocation.character,
        context_budget=allocation.context,
        scene_budget=allocation.scene,
    )
    naturalness = request.flags.naturalness_enabled and allocation.naturalness >= estimate_tokens(NATURALNESS_POLICY)
    while True:
        section = render_quality_sections(
            characters=selected.character_items,
            contexts=selected.context_items,
            scenes=selected.scene_items,
            naturalness=naturalness,
        )
        if estimate_tokens(section) <= allocation.available_added:
            break
        # Trim least essential local context first. Source, existing policy and
        # glossary live in the untouched baseline and cannot be sacrificed.
        if selected.context_items:
            selected = replace(selected, context_items=selected.context_items[:-1])
        elif selected.scene_items:
            selected = replace(selected, scene_items=selected.scene_items[:-1])
        elif len(selected.character_items) > 1:
            selected = replace(selected, character_items=selected.character_items[:-1])
        elif naturalness:
            naturalness = False
        elif selected.character_items:
            selected = replace(selected, character_items=())
        else:
            section = ""
            break
    if not section:
        return QualityIntegrationResult(user_prompt, "", _metadata(request, selected, "", allocation.exhausted, status="no_eligible_content"))
    source = request.source_text.strip()
    if "\u3010Korean\u3011" in user_prompt or "\u3010Output\u3011" in user_prompt:
        integrated, verification = serialize_candidate_prompt(user_prompt, source, section)
        if not verification.valid:
            raise TranslationQualityIntegrationError("candidate_prompt_invalid:" + ",".join(verification.violations))
    else:
        insertion = user_prompt.rfind(source)
        if insertion < 0:
            raise TranslationQualityIntegrationError("final source prompt boundary unavailable")
        integrated = user_prompt[:insertion] + section + "\n" + user_prompt[insertion:]
    return QualityIntegrationResult(integrated, section, _metadata(request, selected, section, allocation.exhausted))


def apply_to_prompt_package(
    package: dict[str, Any],
    *,
    flags: QualityIntegrationFlags,
    character_store: object | None = None,
    context_scene_store: object | None = None,
    active_character_ids: tuple[str, ...] = (),
    chapter_id: str | None = None,
    scene_id: str | None = None,
    sequence_index: int | None = None,
    selection_time: str = "9999-01-01T00:00:00Z",
    budget: PromptBudget | None = None,
) -> dict[str, Any]:
    """Apply one provider-free, output-free adapter at final prompt serialization."""
    if not flags.enabled:
        return package
    prompt = package.get("prompt") or {}
    source = package.get("source") or {}
    profile = prompt.get("prompt_profile") or {}
    project = package.get("project") or {}
    request = QualityIntegrationRequest(
        source_text=str(source.get("chunk_text", "")),
        base_prompt_tokens=int(profile.get("total_tokens", 0)),
        glossary_tokens=int(profile.get("glossary_tokens", 0)),
        flags=flags,
        budget=budget or PromptBudget(),
        character_store=character_store,
        context_scene_store=context_scene_store,
        active_character_ids=active_character_ids,
        chapter_id=chapter_id,
        scene_id=scene_id,
        sequence_index=sequence_index,
        source_language=None if project.get("source_language") is None else str(project["source_language"]),
        scope={"chapter_id": chapter_id or "", "segment_id": str(sequence_index if sequence_index is not None else "")},
        selection_time=selection_time,
    )
    try:
        result = integrate_prompt(str(prompt.get("user_prompt", "")), request)
    except Exception as exc:
        # Fail closed: enabled integration errors preserve the provider-ready baseline.
        result_meta = {
            "enabled": True,
            "status": "degraded_baseline_preserved",
            "error_code": type(exc).__name__,
            "provider_requests_added": 0,
            "network_requests_added": 0,
        }
        updated_runtime = dict(package.get("prompt_runtime") or {})
        updated_runtime["translation_quality_integration_v72"] = result_meta
        updated = dict(package)
        updated["prompt_runtime"] = updated_runtime
        return updated
    updated_prompt = dict(prompt)
    updated_prompt["user_prompt"] = result.user_prompt
    updated_profile = dict(profile)
    updated_profile["total_tokens"] = int(updated_profile.get("total_tokens", 0)) + result.metadata.total_added_tokens
    updated_profile["total_chars"] = int(updated_profile.get("total_chars", 0)) + len(result.section)
    updated_prompt["prompt_profile"] = updated_profile
    updated_runtime = dict(package.get("prompt_runtime") or {})
    runtime_meta = result.metadata.to_dict()
    runtime_meta.update({
        "version": INTEGRATION_VERSION,
        "activation_gate": ACTIVATION_GATE,
        "provider_requests_added": 0,
        "network_requests_added": 0,
        "resume_changed": False,
        "output_changed": False,
    })
    updated_runtime["translation_quality_integration_v72"] = runtime_meta
    updated = dict(package)
    updated["prompt"] = updated_prompt
    updated["prompt_runtime"] = updated_runtime
    return updated


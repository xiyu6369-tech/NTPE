from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from time import perf_counter_ns

from core.translation_quality_integration_v72 import (
    QualityIntegrationFlags,
    QualityIntegrationRequest,
    integrate_prompt,
)

from .fixtures import SELECTION_TIME, build_offline_canary_stores
from .models import CanaryArmRecord, CanaryConfiguration, CanaryPairRecord


BASELINE_FLAGS = QualityIntegrationFlags()
CANDIDATE_FLAGS = QualityIntegrationFlags(
    integration=True,
    character_memory=True,
    context_scene=True,
    naturalness=True,
)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _fingerprint(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha_bytes(raw)


def _run_arm(
    *,
    case_id: str,
    arm: str,
    source_text: str,
    configuration: CanaryConfiguration,
    request: QualityIntegrationRequest,
) -> CanaryArmRecord:
    baseline_prompt = "CONTROLLED CANARY BASELINE\n" + source_text
    started = perf_counter_ns()
    result = integrate_prompt(baseline_prompt, request)
    latency_us = max(0, (perf_counter_ns() - started) // 1_000)
    configuration_fingerprint = _fingerprint(configuration.to_dict())
    input_fingerprint = _fingerprint({
        "case_id": case_id,
        "source_sha256": _sha_text(source_text),
        "baseline_prompt_sha256": _sha_text(baseline_prompt),
        "configuration_fingerprint": configuration_fingerprint,
    })
    metadata = result.metadata
    return CanaryArmRecord(
        case_id=case_id,
        arm=arm,
        source_sha256=_sha_text(source_text),
        input_fingerprint=input_fingerprint,
        configuration_fingerprint=configuration_fingerprint,
        flags=request.flags.to_dict(),
        prompt_sha256=_sha_text(result.user_prompt),
        prompt_tokens=configuration.base_prompt_tokens + metadata.total_added_tokens,
        character_selected=metadata.character_records_selected,
        context_selected=metadata.context_records_selected,
        scene_selected=metadata.scene_records_selected,
        budget_usage_tokens=metadata.total_added_tokens,
        integration_latency_microseconds=latency_us,
    )


def run_offline_canary_case(
    *,
    case_id: str,
    categories: tuple[str, ...],
    source_text: str,
    configuration: CanaryConfiguration,
) -> CanaryPairRecord:
    if not source_text.strip():
        raise ValueError("canary source text must not be empty")
    characters, contexts = build_offline_canary_stores()
    common = QualityIntegrationRequest(
        source_text=source_text,
        base_prompt_tokens=configuration.base_prompt_tokens,
        glossary_tokens=configuration.glossary_tokens,
        character_store=characters,
        context_scene_store=contexts,
        active_character_ids=("char-yeonghui",),
        chapter_id="chapter-1",
        scene_id="scene-1",
        sequence_index=2,
        source_language="ko",
        scope={"chapter_id": "chapter-1", "segment_id": case_id},
        selection_time=SELECTION_TIME,
    )
    baseline = _run_arm(
        case_id=case_id,
        arm="baseline",
        source_text=source_text,
        configuration=configuration,
        request=replace(common, flags=BASELINE_FLAGS),
    )
    candidate = _run_arm(
        case_id=case_id,
        arm="candidate",
        source_text=source_text,
        configuration=configuration,
        request=replace(common, flags=CANDIDATE_FLAGS),
    )
    parity = (
        baseline.case_id == candidate.case_id
        and baseline.source_sha256 == candidate.source_sha256
        and baseline.input_fingerprint == candidate.input_fingerprint
        and baseline.configuration_fingerprint == candidate.configuration_fingerprint
    )
    return CanaryPairRecord(
        case_id=case_id,
        categories=tuple(categories),
        baseline=baseline,
        candidate=candidate,
        parity_verified=parity,
        only_feature_flags_differ=parity and baseline.flags != candidate.flags,
    )

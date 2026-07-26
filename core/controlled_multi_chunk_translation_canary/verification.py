"""Fail-closed verification for completed Stage 7.4 executions."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .checkpoint import read_checkpoint
from .errors import ControlledMultiChunkVerificationError
from .models import (
    ChunkQualityAssessment, ChunkQualityVerificationResult,
    MultiChunkCanaryRequest, MultiChunkResult, MultiChunkVerificationResult,
)
from .policy import CHUNK_COUNT, COMBINED_BOUNDARY


_MANDATORY_QUALITY_FIELDS = (
    "non_empty",
    "minimum_output_length_passed",
    "hangul_residual_passed",
    "no_source_echo",
    "no_duplicate_loop",
    "no_corruption",
    "traditional_chinese_signal",
    "dialogue_punctuation_passed",
    "fixed_names_passed",
    "no_prohibited_prefix",
    "structural_passed",
    "baseline_passed",
)


def assess_dialogue_punctuation(source: str, candidate: str) -> dict:
    """Validate literary dialogue delimiters without rewriting candidate text."""
    source = source or ""
    candidate = candidate or ""
    source_has_dialogue = any(
        opening in source and closing in source
        for opening, closing in (("“", "”"), ('"', '"'), ("「", "」"))
    )
    counts = {
        "ascii_double_quote_count": candidate.count('"'),
        "curly_open_double_quote_count": candidate.count("“"),
        "curly_close_double_quote_count": candidate.count("”"),
        "curly_open_single_quote_count": candidate.count("‘"),
        "curly_close_single_quote_count": candidate.count("’"),
        "corner_open_count": candidate.count("「"),
        "corner_close_count": candidate.count("」"),
        "nested_corner_open_count": candidate.count("『"),
        "nested_corner_close_count": candidate.count("』"),
        "korean_style_quote_count": sum(
            candidate.count(mark) for mark in ("“", "”", "‘", "’")
        ),
    }
    reasons: list[str] = []
    unmatched: list[dict[str, int | str]] = []
    main_open: int | None = None
    nested_open: int | None = None
    completed_dialogue_spans = 0
    for position, mark in enumerate(candidate):
        if mark == "「":
            if main_open is not None:
                reasons.append("malformed-nested-dialogue")
                unmatched.append({"mark": mark, "position": position})
            else:
                main_open = position
        elif mark == "『":
            if main_open is None or nested_open is not None:
                reasons.append("malformed-nested-dialogue")
                unmatched.append({"mark": mark, "position": position})
            else:
                nested_open = position
        elif mark == "』":
            if nested_open is None:
                reasons.append("unmatched-nested-closing-quote")
                unmatched.append({"mark": mark, "position": position})
            else:
                nested_open = None
        elif mark == "」":
            if main_open is None:
                reasons.append("unmatched-closing-corner-quote")
                unmatched.append({"mark": mark, "position": position})
            elif nested_open is not None:
                reasons.append("malformed-nested-dialogue")
                unmatched.append({"mark": mark, "position": position})
                main_open = None
                nested_open = None
            else:
                content = candidate[main_open + 1:position].rstrip()
                if not content or content[-1] not in "。！？!?…，、；：":
                    reasons.append("dialogue-closing-punctuation-missing")
                    unmatched.append({"mark": mark, "position": position})
                completed_dialogue_spans += 1
                main_open = None
    if main_open is not None:
        reasons.append("unmatched-opening-corner-quote")
        unmatched.append({"mark": "「", "position": main_open})
    if nested_open is not None:
        reasons.append("unmatched-nested-opening-quote")
        unmatched.append({"mark": "『", "position": nested_open})
    if source_has_dialogue:
        if counts["ascii_double_quote_count"]:
            reasons.append("ascii-spoken-quotes-forbidden")
        if (
            counts["curly_open_double_quote_count"]
            or counts["curly_close_double_quote_count"]
        ):
            reasons.append("curly-spoken-quotes-forbidden")
            reasons.append("korean-spoken-quotes-forbidden")
        if (
            counts["curly_open_single_quote_count"]
            or counts["curly_close_single_quote_count"]
        ):
            reasons.append("korean-nested-quotes-forbidden")
        if completed_dialogue_spans == 0:
            reasons.append("corner-dialogue-required")
    reason_codes = tuple(dict.fromkeys(reasons))
    return {
        "passed": not reason_codes,
        "source_has_dialogue": source_has_dialogue,
        "completed_dialogue_spans": completed_dialogue_spans,
        "quote_type_counts": counts,
        "unmatched_position_summaries": tuple(unmatched),
        "reason_codes": reason_codes,
    }


def verify_chunk_quality_assessment(value) -> ChunkQualityVerificationResult:
    if type(value) is not ChunkQualityAssessment:
        raise ControlledMultiChunkVerificationError(
            "exact immutable chunk quality assessment required"
        )
    reasons = tuple(
        f"{name}-failed"
        for name in _MANDATORY_QUALITY_FIELDS
        if getattr(value, name, None) is not True
    )
    if value.quality_passed is not True:
        reasons += ("aggregate-quality-failed",)
    return ChunkQualityVerificationResult(
        valid=not reasons,
        reason_codes=tuple(dict.fromkeys(reasons)),
        assessment_fingerprint=value.assessment_fingerprint,
    )

def verify_multi_chunk_result(
    request: MultiChunkCanaryRequest,
    result: MultiChunkResult,
    *,
    artifact_root: str | Path,
    raise_on_error: bool = False,
) -> MultiChunkVerificationResult:
    reasons: list[str] = []
    root = Path(artifact_root).resolve()
    if result.request_id != request.request_id:
        reasons.append("request-id-mismatch")
    exact = (
        result.chunks_planned == result.chunks_started == result.chunks_completed
        == result.provider_requests == result.provider_attempts
        == result.provider_successes == result.translation_executions
        == result.chunk_outputs_written == result.checkpoints_written == CHUNK_COUNT
    )
    if not exact or result.combined_output_written != 1:
        reasons.append("success-counters-invalid")
    if any((
        result.retries, result.fallbacks, result.parallel_requests,
        result.automatic_rollouts, result.formal_output_replacements,
        result.resume_execution_attempts, result.cache_mutations,
    )):
        reasons.append("zero-policy-violated")
    if len(result.chunk_evidence) != CHUNK_COUNT:
        reasons.append("chunk-evidence-count-invalid")
    outputs: list[str] = []
    for evidence in result.chunk_evidence:
        path = (root / evidence.output_artifact_path).resolve()
        if root not in path.parents or not path.is_file():
            reasons.append("chunk-output-missing")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != evidence.output_fingerprint:
            reasons.append("chunk-output-fingerprint-mismatch")
        outputs.append(path.read_text(encoding="utf-8"))
        checkpoint = root / f"checkpoint-{evidence.index:03d}.json"
        try:
            record = read_checkpoint(checkpoint)
            if record.completed_chunk_count != evidence.index:
                reasons.append("checkpoint-order-invalid")
        except ControlledMultiChunkVerificationError:
            reasons.append("checkpoint-invalid")
        except Exception:
            reasons.append("checkpoint-invalid")
    combined_path = (root / result.combined_output_path).resolve()
    expected_combined = COMBINED_BOUNDARY.join(outputs)
    if root not in combined_path.parents or not combined_path.is_file():
        reasons.append("combined-output-missing")
    else:
        combined = combined_path.read_text(encoding="utf-8")
        if combined != expected_combined:
            reasons.append("combined-output-order-mismatch")
        if hashlib.sha256(combined_path.read_bytes()).hexdigest() != result.combined_output_fingerprint:
            reasons.append("combined-output-fingerprint-mismatch")
    verification = MultiChunkVerificationResult(
        valid=not reasons,
        reason_codes=tuple(dict.fromkeys(reasons)),
        request_id=request.request_id,
        result_fingerprint=result.result_fingerprint,
    )
    if raise_on_error and not verification.valid:
        raise ControlledMultiChunkVerificationError(",".join(verification.reason_codes))
    return verification

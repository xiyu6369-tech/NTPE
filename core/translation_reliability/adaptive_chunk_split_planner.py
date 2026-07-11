
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class ChunkSplitSegment:
    index: int
    start: int
    end: int
    text: str
    chars: int


@dataclass(frozen=True)
class ChunkSplitPlan:
    should_split: bool
    reason: str
    original_chars: int
    requested_chunk_size: int
    effective_chunk_size: int
    min_chunk_size: int
    overlap_chars: int
    segment_count: int
    segments: List[Dict[str, Any]]
    merge_strategy: str
    metadata: Dict[str, Any]


class AdaptiveChunkSplitPlanner:
    """Pure planner for retry-time chunk splitting.

    It does not call providers, Translation Runtime, launchers, HTTP clients,
    API keys, or execute translation. It only returns a deterministic plan.
    """

    version = "TE-v4.0"
    stage = "4.0.3"
    name = "adaptive_chunk_split_planner"

    SPLIT_OUTCOMES = {
        "read_timeout",
        "connect_timeout",
        "empty_output",
        "too_short",
        "hangul_residue",
        "duplicate_output",
    }

    def plan(
        self,
        text: Optional[str],
        decision: Optional[Mapping[str, Any]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        source = str(text or "")
        retry_decision = dict(decision or {})
        cfg = self._normalize_config(config)

        requested_size = max(
            cfg["min_chunk_size"],
            int(retry_decision.get("next_chunk_size", cfg["default_chunk_size"]) or cfg["default_chunk_size"]),
        )
        effective_size = min(requested_size, cfg["max_chunk_size"])
        outcome = str(retry_decision.get("outcome") or "unknown_failure")
        retry_enabled = retry_decision.get("retry") is True

        should_split = bool(
            source
            and retry_enabled
            and outcome in self.SPLIT_OUTCOMES
            and len(source) > effective_size
        )

        if not source:
            reason = "empty_source"
        elif not retry_enabled:
            reason = "retry_not_enabled"
        elif outcome not in self.SPLIT_OUTCOMES:
            reason = "outcome_does_not_require_split"
        elif len(source) <= effective_size:
            reason = "source_within_effective_chunk_size"
        else:
            reason = "adaptive_split_required"

        segments = (
            self._split_text(source, effective_size, cfg["overlap_chars"])
            if should_split
            else [self._segment(1, 0, len(source), source)] if source else []
        )

        plan = ChunkSplitPlan(
            should_split=should_split,
            reason=reason,
            original_chars=len(source),
            requested_chunk_size=requested_size,
            effective_chunk_size=effective_size,
            min_chunk_size=cfg["min_chunk_size"],
            overlap_chars=cfg["overlap_chars"] if should_split else 0,
            segment_count=len(segments),
            segments=[asdict(segment) for segment in segments],
            merge_strategy="ordered_concat_trim_overlap" if should_split else "identity",
            metadata={
                "planner": self.name,
                "version": self.version,
                "stage": self.stage,
                "outcome": outcome,
                "provider_called": False,
                "http_called": False,
                "api_key_accessed": False,
                "runtime_modified": False,
                "launcher_modified": False,
                "translation_executed": False,
            },
        )
        return asdict(plan)

    def validate_plan(self, plan: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(plan, Mapping):
            return False

        required = {
            "should_split",
            "reason",
            "original_chars",
            "requested_chunk_size",
            "effective_chunk_size",
            "min_chunk_size",
            "overlap_chars",
            "segment_count",
            "segments",
            "merge_strategy",
            "metadata",
        }
        if not required.issubset(plan):
            return False
        if int(plan.get("effective_chunk_size", 0)) <= 0:
            return False
        if int(plan.get("min_chunk_size", 0)) <= 0:
            return False
        if int(plan.get("segment_count", -1)) != len(plan.get("segments", [])):
            return False
        if not isinstance(plan.get("metadata"), Mapping):
            return False

        segments = plan.get("segments", [])
        previous_start = -1
        for expected_index, segment in enumerate(segments, start=1):
            if not isinstance(segment, Mapping):
                return False
            if int(segment.get("index", 0)) != expected_index:
                return False
            start = int(segment.get("start", -1))
            end = int(segment.get("end", -1))
            chars = int(segment.get("chars", -1))
            text = str(segment.get("text", ""))
            if start < 0 or end < start:
                return False
            if chars != len(text) or chars != end - start:
                return False
            if start < previous_start:
                return False
            previous_start = start

        if plan.get("should_split") is True and len(segments) < 2:
            return False
        if plan.get("should_split") is False and len(segments) > 1:
            return False

        return True

    def merge_preview(self, plan: Mapping[str, Any]) -> str:
        """Reconstruct source text from a plan without translated outputs."""
        if not self.validate_plan(plan):
            raise ValueError("invalid chunk split plan")

        segments = list(plan.get("segments", []))
        if not segments:
            return ""
        if plan.get("merge_strategy") == "identity":
            return str(segments[0].get("text", ""))

        overlap = int(plan.get("overlap_chars", 0))
        merged = str(segments[0].get("text", ""))
        for segment in segments[1:]:
            text = str(segment.get("text", ""))
            merged += text[overlap:] if overlap > 0 else text
        return merged

    @staticmethod
    def _normalize_config(config: Optional[Mapping[str, Any]]) -> Dict[str, int]:
        src = dict(config or {})
        min_chunk_size = max(1, int(src.get("min_chunk_size", 200) or 200))
        default_chunk_size = max(
            min_chunk_size,
            int(src.get("default_chunk_size", 600) or 600),
        )
        max_chunk_size = max(
            default_chunk_size,
            int(src.get("max_chunk_size", 1200) or 1200),
        )
        overlap_chars = max(0, int(src.get("overlap_chars", 0) or 0))
        overlap_chars = min(overlap_chars, max(0, min_chunk_size - 1))

        return {
            "min_chunk_size": min_chunk_size,
            "default_chunk_size": default_chunk_size,
            "max_chunk_size": max_chunk_size,
            "overlap_chars": overlap_chars,
        }

    @classmethod
    def _split_text(
        cls,
        text: str,
        chunk_size: int,
        overlap_chars: int,
    ) -> List[ChunkSplitSegment]:
        if not text:
            return []

        segments: List[ChunkSplitSegment] = []
        start = 0
        index = 1
        text_length = len(text)

        while start < text_length:
            end = min(text_length, start + chunk_size)
            segment_text = text[start:end]
            segments.append(cls._segment(index, start, end, segment_text))
            if end >= text_length:
                break
            next_start = end - overlap_chars
            if next_start <= start:
                next_start = end
            start = next_start
            index += 1

        return segments

    @staticmethod
    def _segment(index: int, start: int, end: int, text: str) -> ChunkSplitSegment:
        return ChunkSplitSegment(
            index=index,
            start=start,
            end=end,
            text=text,
            chars=len(text),
        )


__all__ = [
    "ChunkSplitSegment",
    "ChunkSplitPlan",
    "AdaptiveChunkSplitPlanner",
]

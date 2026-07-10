from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from core.translation_reliability import AdaptiveChunkSplitPlanner


class QualityChunkRebuildPlanner:
    version = "TE-v5.1"
    stage = "5.1.3"

    def __init__(self) -> None:
        self.planner = AdaptiveChunkSplitPlanner()

    def build(
        self,
        source_text: Optional[str],
        retry_result: Optional[Mapping[str, Any]],
        repair_plan: Optional[Mapping[str, Any]],
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        retry = dict(retry_result or {})
        repair = dict(repair_plan or {})
        cfg = dict(config or {})
        source = str(source_text or "")

        if retry.get("retry") is not True:
            return {
                "stage": self.stage,
                "rebuild_required": False,
                "split_required": False,
                "plan": {},
                "reason": "retry_not_enabled",
                "source_text_retained": False,
            }

        decision = dict(retry.get("decision") or {})
        if repair.get("split_required") is True:
            decision["retry"] = True
            decision["outcome"] = retry.get("outcome", "too_short")
            decision["next_chunk_size"] = min(
                int(decision.get("next_chunk_size", cfg.get("chunk_size", 600)) or 600),
                max(
                    int(cfg.get("min_chunk_size", 200) or 200),
                    max(1, len(source) // 2),
                ),
            )

        plan = self.planner.plan(
            source,
            decision,
            {
                "min_chunk_size": int(cfg.get("min_chunk_size", 200) or 200),
                "default_chunk_size": int(cfg.get("chunk_size", 600) or 600),
                "max_chunk_size": int(cfg.get("max_chunk_size", 1200) or 1200),
                "overlap_chars": int(cfg.get("overlap_chars", 0) or 0),
            },
        )

        safe_plan = dict(plan)
        safe_plan["segments"] = [
            {key: value for key, value in segment.items() if key != "text"}
            for segment in plan.get("segments", [])
        ]

        return {
            "stage": self.stage,
            "rebuild_required": True,
            "split_required": plan.get("should_split") is True,
            "plan": safe_plan,
            "reason": str(plan.get("reason") or "quality_rebuild_planned"),
            "source_text_retained": False,
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False
        required = {
            "stage", "rebuild_required", "split_required",
            "plan", "reason", "source_text_retained"
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("source_text_retained") is not False:
            return False
        for segment in result.get("plan", {}).get("segments", []):
            if "text" in segment:
                return False
        return True

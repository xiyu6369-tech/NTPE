"""
Baseline Manager (RM-5.8.5)

Orchestrates baseline lifecycle: promote, rollback, list, load.
Works with BaselineStorage for persistence and BaselineIndex for state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from .models import (
    BaselineEntry,
    BaselineIndex,
    BaselineStatus,
    BaselineRecordSnapshot,
    utc_now_iso,
)
from .storage import BaselineStorage


def _extract_scorecard_metrics(scorecard_data: Dict[str, Any]) -> tuple[float, str, Dict[str, float], List[BaselineRecordSnapshot]]:
    """Extract key metrics from a scorecard dict for a baseline entry."""
    overall = scorecard_data.get("overall", {})
    overall_score = overall.get("overall_score", 0.0)
    grade = overall.get("grade", "F")

    extractor_scores: Dict[str, float] = {}
    metric_snapshots: List[BaselineRecordSnapshot] = []

    extractor_data = overall.get("extractor_scores", {})
    for ext_name, ext_sc in extractor_data.items():
        score = ext_sc.get("extractor_score", 0.0)
        extractor_scores[ext_name] = round(score, 4)

        metrics = ext_sc.get("metric_scores", {})
        for metric_name, ms_data in metrics.items():
            metric_snapshots.append(BaselineRecordSnapshot(
                extractor_type=ext_name,
                metric_name=metric_name,
                score=ms_data.get("value", 0.0),
                details=ms_data.get("details", {}),
            ))

    return overall_score, grade, extractor_scores, metric_snapshots


class BaselineManager:
    """Manages the baseline lifecycle: promote, load, rollback, list."""

    def __init__(self, storage: Optional[BaselineStorage] = None):
        self.storage = storage or BaselineStorage()

    def list_baselines(self) -> Dict[str, Any]:
        index = self.storage.read_index()
        baselines_list = []
        for b in index.baselines:
            baselines_list.append({
                "baseline_id": b.baseline_id,
                "run_id": b.run_id,
                "overall_score": b.overall_score,
                "grade": b.grade,
                "status": b.status.value,
                "promoted_at": b.promoted_at,
                "notes": b.notes,
            })
        return {
            "active_id": index.active_id,
            "previous_id": index.previous_id,
            "total_baselines": len(baselines_list),
            "baselines": baselines_list,
        }

    def load_baseline(self, baseline_id: Optional[str] = None) -> Optional[BaselineEntry]:
        if baseline_id:
            return self.storage.load_entry(baseline_id)

        index = self.storage.read_index()
        active_id = index.active_id
        if active_id:
            return self.storage.load_entry(active_id)
        return None

    def promote(
        self,
        run_id: str,
        overall_scorecard: Dict[str, Any],
        notes: str = "",
    ) -> BaselineEntry:
        overall_score, grade, extractor_scores, snapshots = _extract_scorecard_metrics(
            overall_scorecard,
        )

        baseline_id = f"baseline_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
        entry = BaselineEntry(
            baseline_id=baseline_id,
            run_id=run_id,
            overall_score=round(overall_score, 4),
            grade=grade,
            extractor_scores=extractor_scores,
            metric_snapshots=snapshots,
            status=BaselineStatus.PROMOTED,
            notes=notes,
        )

        index = self.storage.read_index()
        index.add_entry(entry)

        self.storage.save_entry(entry)
        self.storage.save_index(index)

        return entry

    def rollback(self) -> Optional[BaselineEntry]:
        index = self.storage.read_index()
        if len(index.baselines) >= 2:
            index.active_id = index.baselines[-2].baseline_id
            index.previous_id = index.baselines[-1].baseline_id
            self.storage.save_index(index)
            return index.get_active()

        return None

    def get_history(self) -> Dict[str, Any]:
        return self.list_baselines()


def create_baseline_manager() -> BaselineManager:
    return BaselineManager()
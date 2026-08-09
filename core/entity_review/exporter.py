"""RM-7.3.2 P4 — Knowledge Evolution Bridge.

Exports accepted ReviewCandidates as KnowledgeEvolutionCandidates
for the Knowledge Evolution pipeline.

Bridge preserves full provenance:
    Consistency Mismatch
        ↓
    ReviewCandidate (OPEN)
        ↓
    ACCEPTED (human review)
        ↓
    KnowledgeEvolutionCandidate
        ↓
    Knowledge Evolution pipeline (promote/reject)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.entity_review.models import (
    KnowledgeEvolutionCandidate,
    ReviewCandidate,
    ReviewStatus,
)
from core.entity_review.review import ReviewEngine, get_review_engine
from core.knowledge_evolution.manager import KnowledgeManager
from core.knowledge_evolution.models import (
    CandidateStatus,
    EntityType,
    LearningCandidate,
    PriorityLevel,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeEvolutionExporter:
    """Bridge from Entity Review to Knowledge Evolution.
    
    Responsibilities:
    1. Collect ACCEPTED ReviewCandidates
    2. Convert to KnowledgeEvolutionCandidate format
    3. Submit to KnowledgeManager as LearningCandidates
    4. Preserve full provenance chain
    
    Does NOT auto-promote. Knowledge Evolution pipeline decides promotion.
    """
    
    def __init__(
        self,
        knowledge_manager: Optional[KnowledgeManager] = None,
        review_engine: Optional[ReviewEngine] = None,
    ) -> None:
        self._km = knowledge_manager or KnowledgeManager()
        self._review = review_engine or get_review_engine()
        self._exported_ids: set = set()

    def export_accepted(self, clear_after: bool = True) -> List[LearningCandidate]:
        """Export all ACCEPTED candidates as LearningCandidates.
        
        Args:
            clear_after: If True, mark exported candidates to avoid re-export
        
        Returns:
            List of LearningCandidates submitted to Knowledge Manager
        """
        ke_candidates = self._review.get_accepted_ke_candidates()
        
        learning_candidates = []
        for ke_candidate in ke_candidates:
            if clear_after and ke_candidate.source_candidate_id in self._exported_ids:
                continue
            
            # Check if entity already exists in knowledge base
            existing = self._km.resolver.resolve(ke_candidate.entity_id)
            if existing:
                # Entity exists - could be a conflict or update
                # For P4, we still create a candidate but with higher confidence
                confidence = 0.8
            else:
                confidence = 0.7
            
            # Create LearningCandidate for Knowledge Evolution
            lc = self._km.add_candidate(
                source=ke_candidate.entity_id,
                canonical=ke_candidate.expected_translation,
                entity_type=ke_candidate.entity_type,
                confidence=confidence,
                context_hints=[
                    f"source_form:{ke_candidate.source_form}",
                    f"form_type:{ke_candidate.form_type.value}",
                    f"actual_translation:{ke_candidate.actual_translation}",
                    f"evidence_rule:{ke_candidate.evidence.rule}",
                    f"provenance:{ke_candidate.provenance.get('source', 'ENTITY_CONSISTENCY')}",
                ],
            )
            
            learning_candidates.append(lc)
            self._exported_ids.add(ke_candidate.source_candidate_id)
        
        return learning_candidates

    def export_single(self, candidate_id: str) -> Optional[LearningCandidate]:
        """Export a single ACCEPTED candidate by ID."""
        candidate = self._review.get_candidate(candidate_id)
        if not candidate or candidate.status != ReviewStatus.ACCEPTED:
            return None
        
        ke_candidate = KnowledgeEvolutionCandidate.from_review_candidate(candidate)
        
        existing = self._km.resolver.resolve(ke_candidate.entity_id)
        confidence = 0.8 if existing else 0.7
        
        lc = self._km.add_candidate(
            source=ke_candidate.entity_id,
            canonical=ke_candidate.expected_translation,
            entity_type=ke_candidate.entity_type,
            confidence=confidence,
            context_hints=[
                f"source_form:{ke_candidate.source_form}",
                f"form_type:{ke_candidate.form_type.value}",
                f"actual_translation:{ke_candidate.actual_translation}",
                f"evidence_rule:{ke_candidate.evidence.rule}",
                f"provenance:{ke_candidate.provenance.get('source', 'ENTITY_CONSISTENCY')}",
            ],
        )
        
        self._exported_ids.add(candidate_id)
        return lc

    def get_pending_export(self) -> List[KnowledgeEvolutionCandidate]:
        """Get ACCEPTED candidates not yet exported."""
        all_accepted = self._review.get_accepted_ke_candidates()
        return [c for c in all_accepted if c.source_candidate_id not in self._exported_ids]

    def get_exported_count(self) -> int:
        """Get count of exported candidates."""
        return len(self._exported_ids)

    def clear_exported(self) -> None:
        """Clear exported tracking (for re-export)."""
        self._exported_ids.clear()


def export_to_knowledge_evolution(
    review_engine: Optional[ReviewEngine] = None,
    knowledge_manager: Optional[KnowledgeManager] = None,
) -> List[LearningCandidate]:
    """Convenience function to export all accepted candidates."""
    exporter = KnowledgeEvolutionExporter(
        knowledge_manager=knowledge_manager,
        review_engine=review_engine,
    )
    return exporter.export_accepted()


class ReviewReportExporter:
    """Export review candidates and actions for reporting/audit."""
    
    def __init__(self, review_engine: Optional[ReviewEngine] = None) -> None:
        self._review = review_engine or get_review_engine()

    def to_json(self, filepath: Optional[str] = None) -> str:
        """Export all candidates and actions as JSON."""
        data = {
            "candidates": [c.to_dict() for c in self._review.list_all()],
            "actions": [a.to_dict() for a in self._review.get_actions()],
            "stats": self._review.stats(),
            "generated_at": utc_now_iso(),
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        if filepath:
            Path(filepath).write_text(json_str, encoding="utf-8")
        
        return json_str

    def to_markdown(self, filepath: Optional[str] = None) -> str:
        """Export review report as Markdown."""
        candidates = self._review.list_all()
        actions = self._review.get_actions()
        
        lines = [
            "# Entity Consistency Review Report",
            f"**Generated:** {utc_now_iso()[:19]}",
            f"**Total Candidates:** {len(candidates)}",
            "",
            "## Summary",
            f"- OPEN: {len(self._review.list_open())}",
            f"- ACCEPTED: {len(self._review.list_accepted())}",
            f"- REJECTED: {len(self._review.list_rejected())}",
            f"- Total Actions: {len(actions)}",
            "",
            "## Candidates",
        ]
        
        for c in candidates:
            lines.append(f"### `{c.candidate_id}` — {c.status.value}")
            lines.append(f"- **Entity:** {c.entity_id} ({c.entity_type.value})")
            lines.append(f"- **Form:** {c.form_type.value}")
            lines.append(f"- **Expected:** {c.expected_translation}")
            lines.append(f"- **Actual:** {c.actual_translation}")
            lines.append(f"- **Severity:** {c.severity.value}")
            lines.append(f"- **Source:** {c.source_form}")
            lines.append(f"- **Evidence Rule:** {c.evidence.rule}")
            lines.append(f"- **Created:** {c.created_at[:19]}")
            if c.status != ReviewStatus.OPEN:
                lines.append(f"- **Updated:** {c.updated_at[:19]}")
            lines.append("")
        
        if actions:
            lines.append("## Review Actions")
            for a in actions:
                lines.append(f"- `{a.candidate_id}` → **{a.action.value}** by {a.reviewer} at {a.timestamp[:19]}")
                if a.reason:
                    lines.append(f"  Reason: {a.reason}")
            lines.append("")
        
        md = "\n".join(lines)
        
        if filepath:
            Path(filepath).write_text(md, encoding="utf-8")
        
        return md


__all__ = [
    "KnowledgeEvolutionExporter",
    "ReviewReportExporter",
    "export_to_knowledge_evolution",
]
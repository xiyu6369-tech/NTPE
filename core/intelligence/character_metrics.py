# =====================================================
# NTPE 1.2 Professional
# Stage-16.3 Character Relationship Intelligence
# =====================================================

from __future__ import annotations

from typing import Dict

from .character_result import CharacterIntelligenceResult


def build_character_metrics(result: CharacterIntelligenceResult) -> Dict[str, object]:
    severities: Dict[str, int] = {}
    for finding in result.findings:
        severities[finding.severity] = severities.get(finding.severity, 0) + 1
    return {
        "character_count": result.character_count,
        "mention_count": result.mention_count,
        "relationship_count": len(result.relationships),
        "pronoun_resolution_count": len(result.pronoun_candidates),
        "finding_count": len(result.findings),
        "findings_by_severity": severities,
    }

# =====================================================
# NTPE 1.2 Professional
# Stage-16.4 Semantic Consistency Engine
# =====================================================

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, Iterable, List, Sequence

from .semantic_result import SemanticFinding, SemanticUnit

_CONCEPT_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{2,}|[\u4e00-\u9fff]{2,}")
_EVENT_MARKERS = ("到達", "離開", "發現", "失去", "得到", "知道", "死亡", "回來", "remember", "arrive", "leave", "discover")
_NEGATION_MARKERS = ("沒有", "不是", "未", "不", "never", "not", "no ")


def extract_concepts(text: str, *, limit: int = 12) -> List[str]:
    seen: List[str] = []
    for match in _CONCEPT_RE.findall(text or ""):
        token = match.strip()
        if token and token not in seen:
            seen.append(token)
        if len(seen) >= limit:
            break
    return seen


def extract_events(text: str) -> List[str]:
    lowered = (text or "").lower()
    return [marker for marker in _EVENT_MARKERS if marker.lower() in lowered or marker in text]


def has_negation(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in _NEGATION_MARKERS)


def build_semantic_units(texts: Sequence[str], *, segment_prefix: str = "sem") -> List[SemanticUnit]:
    units: List[SemanticUnit] = []
    for index, text in enumerate(texts, start=1):
        clean = (text or "").strip()
        if not clean:
            continue
        units.append(SemanticUnit(
            unit_id=f"{segment_prefix}_{index}",
            segment_id=f"{segment_prefix}_{index}",
            text=clean,
            concepts=extract_concepts(clean),
            events=extract_events(clean),
            metadata={"has_negation": has_negation(clean)},
        ))
    return units


def build_concept_map(units: Iterable[SemanticUnit]) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = defaultdict(list)
    for unit in units:
        for concept in unit.concepts:
            mapping[concept].append(unit.unit_id)
    return dict(mapping)


def build_event_map(units: Iterable[SemanticUnit]) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = defaultdict(list)
    for unit in units:
        for event in unit.events:
            mapping[event].append(unit.unit_id)
    return dict(mapping)


def detect_semantic_contradictions(units: Sequence[SemanticUnit]) -> List[SemanticFinding]:
    findings: List[SemanticFinding] = []
    by_concept: Dict[str, List[SemanticUnit]] = defaultdict(list)
    for unit in units:
        for concept in unit.concepts:
            by_concept[concept].append(unit)
    for concept, concept_units in by_concept.items():
        negated = [u for u in concept_units if u.metadata.get("has_negation")]
        affirmed = [u for u in concept_units if not u.metadata.get("has_negation")]
        if negated and affirmed and len(concept_units) > 1:
            findings.append(SemanticFinding(
                category="semantic_contradiction",
                severity="warning",
                concept=concept,
                segment_id=negated[0].segment_id,
                message=f"Concept '{concept}' appears in both affirmative and negated contexts.",
            ))
    return findings


def detect_continuity_gaps(units: Sequence[SemanticUnit]) -> List[SemanticFinding]:
    findings: List[SemanticFinding] = []
    for previous, current in zip(units, units[1:]):
        if previous.events and current.events and not set(previous.concepts).intersection(current.concepts):
            findings.append(SemanticFinding(
                category="semantic_continuity_gap",
                severity="info",
                segment_id=current.segment_id,
                message="Adjacent event-bearing segments have no shared semantic concepts.",
            ))
    return findings

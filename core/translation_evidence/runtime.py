from __future__ import annotations

from .detector import (
    detect_dialogue_evidence,
    detect_narrative_evidence,
    detect_paragraph_evidence,
    detect_sentence_evidence,
    detect_terminology_evidence,
)
from .registry import EvidenceRegistry
from .report import TranslationEvidenceResult

EVIDENCE_ENGINE_VERSION = "6.0.0-stage11.1"


def build_default_registry() -> EvidenceRegistry:
    registry = EvidenceRegistry()
    registry.register("paragraph", detect_paragraph_evidence)
    registry.register("sentence", detect_sentence_evidence)
    registry.register("dialogue", detect_dialogue_evidence)
    registry.register("terminology", detect_terminology_evidence)
    registry.register("narrative", detect_narrative_evidence)
    return registry


def build_translation_evidence(source_text: str, translated_text: str, *, registry: EvidenceRegistry | None = None) -> TranslationEvidenceResult:
    active = registry or build_default_registry()
    evidence = tuple(item for _name, detector in active.items() for item in detector(source_text, translated_text))
    confidence = max((item.confidence for item in evidence), default=1.0)
    reliable = bool(evidence) and all(item.reliable for item in evidence)
    type_counts: dict[str, int] = {}
    for item in evidence:
        type_counts[item.evidence_type] = type_counts.get(item.evidence_type, 0) + 1
    return TranslationEvidenceResult(
        evidence=evidence,
        confidence=confidence,
        reliable=reliable,
        statistics={"evidence_count": len(evidence), "type_counts": type_counts, "detector_count": len(active.names())},
        metadata={"engine_version": EVIDENCE_ENGINE_VERSION, "detectors": list(active.names()), "runtime_integrated": False},
    )

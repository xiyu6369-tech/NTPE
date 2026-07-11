from .alignment import (
    ALIGNMENT_ENGINE_VERSION,
    ALIGNMENT_SCHEMA_VERSION,
    AlignmentSpan,
    SemanticAlignmentResult,
    build_source_translation_alignment,
)
from .alignment_evidence import ALIGNMENT_EVIDENCE_VERSION, build_alignment_evidence
from .detector import (
    detect_dialogue_evidence,
    detect_narrative_evidence,
    detect_paragraph_evidence,
    detect_sentence_evidence,
    detect_terminology_evidence,
)
from .evidence import (
    DialogueEvidence,
    EVIDENCE_SCHEMA_VERSION,
    NarrativeEvidence,
    ParagraphEvidence,
    SentenceEvidence,
    TerminologyEvidence,
    TranslationEvidence,
)
from .locator import TextUnit, locate_dialogues, locate_paragraphs, locate_sentences
from .registry import EvidenceRegistry
from .report import TranslationEvidenceResult
from .runtime import EVIDENCE_ENGINE_VERSION, build_default_registry, build_translation_evidence
from .scorer import coverage_ratio, evidence_reliability

__all__ = [
    "DialogueEvidence", "EVIDENCE_ENGINE_VERSION", "EVIDENCE_SCHEMA_VERSION", "EvidenceRegistry",
    "NarrativeEvidence", "ParagraphEvidence", "SentenceEvidence", "TerminologyEvidence", "TextUnit",
    "TranslationEvidence", "TranslationEvidenceResult", "build_default_registry", "build_translation_evidence",
    "coverage_ratio", "detect_dialogue_evidence", "detect_narrative_evidence", "detect_paragraph_evidence",
    "detect_sentence_evidence", "detect_terminology_evidence", "evidence_reliability", "locate_dialogues",
    "locate_paragraphs", "locate_sentences",
    "ALIGNMENT_ENGINE_VERSION", "ALIGNMENT_SCHEMA_VERSION", "ALIGNMENT_EVIDENCE_VERSION",
    "AlignmentSpan", "SemanticAlignmentResult", "build_source_translation_alignment",
    "build_alignment_evidence",
]

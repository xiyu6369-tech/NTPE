from __future__ import annotations

import re

from .evidence import TranslationEvidence
from .locator import locate_dialogues, locate_paragraphs, locate_sentences
from .scorer import coverage_ratio


def detect_paragraph_evidence(source_text: str, translated_text: str):
    source = locate_paragraphs(source_text)
    translated = locate_paragraphs(translated_text)
    ratio = coverage_ratio(len(source), len(translated))
    if len(source) >= 2 and ratio < 0.60:
        yield TranslationEvidence(
            code="PARAGRAPH_COVERAGE_LOW",
            evidence_type="paragraph",
            confidence=min(0.95, 1.0 - ratio + 0.35),
            reliable=False,
            detector="paragraph_coverage",
            metadata={"source_count": len(source), "translated_count": len(translated), "coverage_ratio": ratio},
        )


def detect_sentence_evidence(source_text: str, translated_text: str):
    source = locate_sentences(source_text)
    translated = locate_sentences(translated_text)
    ratio = coverage_ratio(len(source), len(translated))
    if len(source) >= 3 and ratio < 0.55:
        yield TranslationEvidence(
            code="SENTENCE_COVERAGE_LOW",
            evidence_type="sentence",
            confidence=min(0.95, 1.0 - ratio + 0.35),
            reliable=False,
            detector="sentence_coverage",
            metadata={"source_count": len(source), "translated_count": len(translated), "coverage_ratio": ratio},
        )


def detect_dialogue_evidence(source_text: str, translated_text: str):
    source_count = len(re.findall(r"[\"“‘「『]", source_text or ""))
    translated = locate_dialogues(translated_text)
    if source_count and not translated:
        yield TranslationEvidence(
            code="DIALOGUE_COVERAGE_LOW",
            evidence_type="dialogue",
            confidence=0.75,
            reliable=False,
            detector="dialogue_coverage",
            metadata={"source_markers": source_count, "translated_dialogues": 0},
        )


def detect_terminology_evidence(source_text: str, translated_text: str):
    return ()


def detect_narrative_evidence(source_text: str, translated_text: str):
    source_len = len((source_text or "").strip())
    translated_len = len((translated_text or "").strip())
    if source_len and translated_len / source_len < 0.28:
        yield TranslationEvidence(
            code="NARRATIVE_COVERAGE_LOW",
            evidence_type="narrative",
            confidence=0.85,
            reliable=False,
            detector="narrative_length_coverage",
            metadata={"source_length": source_len, "translated_length": translated_len},
        )

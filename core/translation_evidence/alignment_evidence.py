from __future__ import annotations

from .alignment import SemanticAlignmentResult
from .evidence import TranslationEvidence
from .locator import locate_paragraphs

ALIGNMENT_EVIDENCE_VERSION = "6.0.0-stage11.2"


def build_alignment_evidence(source_text: str, translated_text: str, alignment: SemanticAlignmentResult):
    evidence: list[TranslationEvidence] = []
    for item in alignment.paragraph_alignments:
        evidence.append(
            TranslationEvidence(
                code="PARAGRAPH_ALIGNMENT" if item.reliable else "AMBIGUOUS_PARAGRAPH_ALIGNMENT",
                evidence_type="paragraph",
                confidence=item.confidence,
                reliable=item.reliable,
                source_start=item.source_start,
                source_end=item.source_end,
                translated_start=item.translated_start,
                translated_end=item.translated_end,
                source_evidence=source_text[item.source_start:item.source_end],
                translated_evidence=translated_text[item.translated_start:item.translated_end],
                paragraph_indexes=item.source_indexes,
                detector="semantic_alignment_v611_stage112",
                metadata={
                    "alignment_operation": item.operation,
                    "translated_paragraph_indexes": list(item.translated_indexes),
                    "alignment_version": ALIGNMENT_EVIDENCE_VERSION,
                },
            )
        )
    for item in alignment.sentence_alignments:
        evidence.append(
            TranslationEvidence(
                code="SENTENCE_ALIGNMENT",
                evidence_type="sentence",
                confidence=item.confidence,
                reliable=item.reliable,
                source_start=item.source_start,
                source_end=item.source_end,
                translated_start=item.translated_start,
                translated_end=item.translated_end,
                source_evidence=source_text[item.source_start:item.source_end],
                translated_evidence=translated_text[item.translated_start:item.translated_end],
                sentence_indexes=item.source_indexes,
                detector="semantic_alignment_v611_stage112",
                metadata={
                    "alignment_operation": item.operation,
                    "translated_sentence_indexes": list(item.translated_indexes),
                    "alignment_version": ALIGNMENT_EVIDENCE_VERSION,
                },
            )
        )

    source_paragraphs = locate_paragraphs(source_text)
    mapped = {index for item in alignment.paragraph_alignments for index in item.source_indexes}
    translated_offsets = sorted(
        (item.source_indexes[0], item.translated_start, item.translated_end, item.reliable)
        for item in alignment.paragraph_alignments
        if item.source_indexes
    )
    for index in alignment.unaligned_source_paragraphs:
        unit = source_paragraphs[index]
        previous = [entry for entry in translated_offsets if entry[0] < index]
        following = [entry for entry in translated_offsets if entry[0] > index]
        insertion: int | None = None
        anchor_reliable = False
        if previous and following:
            prev = previous[-1]
            nxt = following[0]
            if prev[2] <= nxt[1] and prev[3] and nxt[3]:
                insertion = prev[2]
                anchor_reliable = True
        elif previous and previous[-1][3]:
            insertion = previous[-1][2]
        elif following and following[0][3]:
            insertion = following[0][1]

        evidence.append(
            TranslationEvidence(
                code="UNALIGNED_SOURCE_PARAGRAPH",
                evidence_type="paragraph",
                confidence=0.88 if anchor_reliable else 0.62,
                reliable=bool(anchor_reliable and insertion is not None),
                source_start=unit.start,
                source_end=unit.end,
                translated_start=insertion,
                translated_end=insertion,
                source_evidence=unit.text,
                translated_evidence="",
                paragraph_indexes=(index,),
                detector="semantic_alignment_v611_stage112",
                metadata={
                    "alignment_version": ALIGNMENT_EVIDENCE_VERSION,
                    "bounded_insertion": insertion is not None,
                    "anchor_reliable": anchor_reliable,
                    "fail_closed": not anchor_reliable,
                },
            )
        )
    return tuple(evidence)

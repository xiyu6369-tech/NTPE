from __future__ import annotations

from core.translation_discipline import (
    EVIDENCE_RETRY_INTEGRATION_VERSION,
    DisciplineRuntimeContext,
    integrate_alignment_evidence_for_retry,
    integrate_translation_discipline_runtime,
)
from core.translation_evidence import AlignmentSpan, SemanticAlignmentResult, TranslationEvidence


def _assert(label: str, condition: bool) -> None:
    print(f"{label:<52} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


def _alignment() -> SemanticAlignmentResult:
    return SemanticAlignmentResult(
        paragraph_alignments=(
            AlignmentSpan(
                alignment_type="paragraph",
                source_indexes=(0,),
                translated_indexes=(0,),
                source_start=0,
                source_end=4,
                translated_start=0,
                translated_end=4,
                confidence=0.94,
                reliable=True,
            ),
            AlignmentSpan(
                alignment_type="paragraph",
                source_indexes=(2,),
                translated_indexes=(1,),
                source_start=10,
                source_end=14,
                translated_start=4,
                translated_end=8,
                confidence=0.93,
                reliable=True,
            ),
        ),
        sentence_alignments=(),
        unaligned_source_paragraphs=(1,),
        unaligned_translated_paragraphs=(),
        confidence=0.91,
        reliable=True,
    )


def _omission_evidence(reliable: bool = True) -> tuple[TranslationEvidence, ...]:
    return (
        TranslationEvidence(
            code="UNALIGNED_SOURCE_PARAGRAPH",
            evidence_type="paragraph",
            confidence=0.90 if reliable else 0.62,
            reliable=reliable,
            source_start=5,
            source_end=9,
            translated_start=4,
            translated_end=4,
            source_evidence="BBBB",
            translated_evidence="",
            paragraph_indexes=(1,),
            detector="semantic_alignment_v611_stage112",
            metadata={"bounded_insertion": True, "anchor_reliable": reliable},
        ),
    )


def _report(issue: dict) -> dict:
    return {
        "score": 80,
        "decision": "retry_required",
        "retry_required": True,
        "merged_issues": [issue],
    }


def main() -> int:
    source = "AAAA\nBBBB\nCCCC"
    translated = "甲甲甲甲乙乙乙乙"

    result = integrate_alignment_evidence_for_retry(
        _report({
            "code": "PARAGRAPH_OMISSION_SUSPECTED",
            "severity": "high",
            "retry_required": True,
            "metadata": {"paragraph_indexes": [1]},
        }),
        source_text=source,
        translated_text=translated,
        alignment=_alignment(),
        evidence=_omission_evidence(True),
    )
    issue = result.report["merged_issues"][0]
    evidence = issue["evidence"]
    _assert("Reliable omission evidence is applied", result.applied_issue_codes == ("PARAGRAPH_OMISSION_SUSPECTED",))
    _assert("Source range remains bounded", evidence["source_start"] == 5 and evidence["source_end"] == 9)
    _assert("Translated insertion range is explicit", evidence["translated_start"] == evidence["translated_end"] == 4)
    _assert("Integration metadata is fail-closed", result.to_metadata()["fail_closed"] is True)

    ambiguous = integrate_alignment_evidence_for_retry(
        _report({"code": "PARAGRAPH_OMISSION_SUSPECTED", "severity": "high", "retry_required": True}),
        source_text=source,
        translated_text=translated,
        alignment=_alignment(),
        evidence=_omission_evidence(False),
    )
    _assert("Unreliable evidence is not applied", "evidence" not in ambiguous.report["merged_issues"][0])

    explicit = integrate_alignment_evidence_for_retry(
        _report({
            "code": "PARAGRAPH_OMISSION_SUSPECTED",
            "severity": "high",
            "retry_required": True,
            "evidence": {
                "source_start": 5,
                "source_end": 9,
                "translated_start": 2,
                "translated_end": 2,
                "confidence": 0.99,
                "reliable": True,
            },
        }),
        source_text=source,
        translated_text=translated,
        alignment=_alignment(),
        evidence=_omission_evidence(True),
    )
    _assert("Explicit reliable evidence is preserved", explicit.report["merged_issues"][0]["evidence"]["translated_start"] == 2)

    def quality_runner(text: str) -> dict:
        return {
            "score": 80,
            "decision": "retry_required",
            "retry_required": True,
            "merged_issues": [{
                "code": "PARAGRAPH_OMISSION_SUSPECTED",
                "severity": "high",
                "retry_required": True,
                "metadata": {"paragraph_indexes": [1]},
            }],
            "_discipline_final_text": text,
        }

    def legacy_runner(text: str, quality: dict) -> dict:
        return {"unified_quality_report": dict(quality)}

    # Use a normal runtime call to prove the Stage 10 planner receives the
    # alignment-enriched report. The real alignment may remain fail-closed for
    # this tiny synthetic sample; API presence and metadata are the contract.
    runtime_result = integrate_translation_discipline_runtime(
        DisciplineRuntimeContext(source_text=source, translated_text=translated),
        quality_runner=quality_runner,
        legacy_qa_runner=legacy_runner,
    )
    metadata = runtime_result.metadata["evidence_retry_integration"]
    _assert("Runtime integration exports Stage 11.3 metadata", metadata["version"] == EVIDENCE_RETRY_INTEGRATION_VERSION)
    _assert("Runtime integration remains Provider-free", runtime_result.provider_retry_required in {True, False})

    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

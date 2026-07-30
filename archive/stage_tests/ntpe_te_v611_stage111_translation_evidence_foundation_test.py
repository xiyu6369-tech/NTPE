from __future__ import annotations

from importlib import import_module
from pathlib import Path

from core.translation_evidence import (
    EvidenceRegistry,
    TranslationEvidence,
    build_translation_evidence,
    locate_dialogues,
    locate_paragraphs,
    locate_sentences,
)


def main() -> int:
    item = TranslationEvidence(
        code="paragraph_omission",
        evidence_type="paragraph",
        confidence=0.91,
        reliable=True,
        source_start=2,
        source_end=8,
        translated_start=1,
        translated_end=4,
    )
    assert item.code == "PARAGRAPH_OMISSION" and item.has_source_range and item.has_translated_range
    assert item.to_dict()["schema_version"] == "6.0.0-stage11.1"

    source = '第一段。\n\n「對話。」\n\n第三段。'
    translated = '第一段。'
    assert len(locate_paragraphs(source)) == 3
    assert len(locate_sentences(source)) >= 3
    assert len(locate_dialogues(source)) == 1

    result = build_translation_evidence(source, translated)
    codes = {e.code for e in result.evidence}
    assert "PARAGRAPH_COVERAGE_LOW" in codes
    assert result.metadata["runtime_integrated"] is False
    assert result.statistics["detector_count"] == 5

    registry = EvidenceRegistry()
    registry.register("custom", lambda _s, _t: [item])
    custom = build_translation_evidence("a", "b", registry=registry)
    assert custom.evidence == (item,)

    package = import_module("core.translation_evidence")
    for name in ("TranslationEvidence", "TranslationEvidenceResult", "build_translation_evidence", "EvidenceRegistry"):
        assert getattr(package, name)
    for path in (
        "core/translation_evidence/evidence.py",
        "core/translation_evidence/registry.py",
        "core/translation_evidence/locator.py",
        "core/translation_evidence/scorer.py",
        "core/translation_evidence/detector.py",
        "core/translation_evidence/report.py",
        "core/translation_evidence/runtime.py",
    ):
        assert Path(path).is_file()
    assert "requests" not in Path("core/translation_evidence/runtime.py").read_text(encoding="utf-8")

    print("NTPE TE v6.1.1 Stage 11.1 Translation Evidence Foundation")
    print("==========================================================")
    print("Unified evidence model                  PASS")
    print("Paragraph/sentence/dialogue locators    PASS")
    print("Detector registry and offline runtime   PASS")
    print("Import/export and packaging             PASS")
    print("No Provider client or HTTP request      PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

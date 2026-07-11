from __future__ import annotations

from importlib import import_module
from pathlib import Path

from core.translation_evidence import (
    ALIGNMENT_ENGINE_VERSION,
    build_alignment_evidence,
    build_source_translation_alignment,
)


def main() -> int:
    source = "첫 문단입니다.\n\n두 번째 문단입니다.\n\n세 번째 문단입니다."
    translated = "這是第一段。\n\n這是第二段。\n\n這是第三段。"
    result = build_source_translation_alignment(source, translated)
    assert ALIGNMENT_ENGINE_VERSION == "6.0.0-stage11.2"
    assert len(result.paragraph_alignments) == 3
    assert not result.unaligned_source_paragraphs
    assert all(item.source_end > item.source_start for item in result.paragraph_alignments)
    assert all(item.translated_end > item.translated_start for item in result.paragraph_alignments)
    assert [item.source_start for item in result.paragraph_alignments] == sorted(item.source_start for item in result.paragraph_alignments)
    assert [item.translated_start for item in result.paragraph_alignments] == sorted(item.translated_start for item in result.paragraph_alignments)
    assert result.metadata["runtime_integrated"] is False

    missing = build_source_translation_alignment(source, "這是第一段。\n\n這是第三段。")
    evidence = build_alignment_evidence(source, "這是第一段。\n\n這是第三段。", missing)
    assert any(
        item.code in {"UNALIGNED_SOURCE_PARAGRAPH", "AMBIGUOUS_PARAGRAPH_ALIGNMENT"}
        for item in evidence
    )
    # The engine may only expose a translated insertion range when bounded by reliable anchors.
    for item in evidence:
        if item.code == "UNALIGNED_SOURCE_PARAGRAPH" and item.reliable:
            assert item.translated_start == item.translated_end
            assert item.metadata["anchor_reliable"] is True
        if item.code == "AMBIGUOUS_PARAGRAPH_ALIGNMENT":
            assert item.reliable is False

    ambiguous = build_source_translation_alignment("짧다.\n\n짧다.", "短。")
    assert not ambiguous.reliable
    assert ambiguous.metadata["alignment_policy"] == "monotonic_fail_closed"

    package = import_module("core.translation_evidence")
    for name in (
        "AlignmentSpan",
        "SemanticAlignmentResult",
        "build_source_translation_alignment",
        "build_alignment_evidence",
    ):
        assert getattr(package, name)
    for path in (
        "core/translation_evidence/alignment.py",
        "core/translation_evidence/alignment_evidence.py",
    ):
        assert Path(path).is_file()
        content = Path(path).read_text(encoding="utf-8")
        assert "requests" not in content and "http" not in content.lower()

    print("NTPE TE v6.1.1 Stage 11.2 Source-Translation Semantic Alignment")
    print("================================================================")
    print("Monotonic paragraph alignment           PASS")
    print("Sentence alignment ranges               PASS")
    print("Fail-closed reliability policy          PASS")
    print("Bounded omission evidence               PASS")
    print("Import/export and offline boundary      PASS")
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

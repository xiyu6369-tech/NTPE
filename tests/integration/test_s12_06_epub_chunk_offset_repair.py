"""S12-06 — EPUB chunk offset contract minimal repair regression.

Verifies the validator repair without weakening validation:

- A canonical multi-chapter EPUB with extraction marker prefixes produces chunks whose
  ``body_*_offset`` (chapter-body-relative) differ numerically from their
  ``extracted_*_offset`` (absolute in extracted_text). The repaired
  ``validate_epub_translation_chunk`` accepts them and the REAL
  ``translate_epub_translation_input`` proceeds past the offset gate.
- The adapter / input / chunk / validator are all real; only the provider execution
  boundary (``RuntimeOrchestrator.execute``) is a deterministic echo.
- Genuinely invalid offsets are still rejected (negative, reversed, wrong space,
  range mismatch, out-of-owning-text).

No provider, no network, no real translation, no glossary. Placed under
``tests/integration`` (non-UI) to avoid the pre-existing shared Qt E2E session issue.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.adapters.epub_extraction_boundary import (
    EpubExtractionBoundary,
    ExtractedTextIntakeRequest,
)
from core.adapters.canonical_book_intake_adapter import CanonicalBookIntakeAdapter
from core.epub_translation.contract import (
    EpubTranslationInput,
    EpubMetadata,
    EpubChapterBoundary,
    EpubTranslationChunk,
    ResourceRef,
    ExtractionManifest,
)
from core.epub_translation.contract.validation import (
    validate_epub_translation_chunk,
    validate_chunk_ownership,
    ContractValidationError,
)
from core.epub_translation.chunking import ChunkingOptions
from core.epub_translation.runtime.adapter import (
    EpubTranslationOptions,
    translate_epub_translation_input,
)

_ORCH_EXECUTE = "core.runtime_orchestrator.manager.RuntimeOrchestrator.execute"

# Simple single-paragraph bodies (no blank lines) so each chapter is one chunk and
# chunk.source_text equals both its extracted slice and its chapter-body slice exactly.
_CHAPTER_TITLES = ("Chapter One", "Chapter Two", "Chapter Three")


def _chapter_body(i: int) -> str:
    return f"제{i}장 본문입니다. " + ("문장입니다. " * 40)


def _make_epub(path: Path) -> Path:
    manifest = "".join(
        f'<item id="ch{i}" href="ch{i}.xhtml" media-type="application/xhtml+xml"/>'
        for i in range(1, 4)
    )
    spine = "".join(f'<itemref idref="ch{i}"/>' for i in range(1, 4))
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="b">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:title>Offset Book</dc:title>'
        '<dc:identifier id="b">urn:uuid:offset-repair-book</dc:identifier>'
        '<dc:language>ko</dc:language></metadata>'
        f"<manifest>{manifest}</manifest><spine>{spine}</spine></package>"
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?>'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
            '<rootfiles><rootfile full-path="OEBPS/content.opf" '
            'media-type="application/oebps-package+xml"/></rootfiles></container>',
        )
        zf.writestr("OEBPS/content.opf", opf)
        for i in range(1, 4):
            zf.writestr(
                f"OEBPS/ch{i}.xhtml",
                '<html xmlns="http://www.w3.org/1999/xhtml"><head></head>'
                f"<body><h1>{_CHAPTER_TITLES[i - 1]}</h1><p>{_chapter_body(i)}</p></body></html>",
            )
    return path


def _build_input(epub_path: Path):
    """Full real extraction -> intake -> EpubTranslationInput (production bridge)."""
    extraction = EpubExtractionBoundary().extract(epub_path)
    request = ExtractedTextIntakeRequest(
        source_path=extraction.source_path,
        source_format="epub",
        extracted_text=extraction.extracted_text,
        original_file_hash=extraction.original_hash,
        extracted_text_hash=extraction.extracted_hash,
        epub_metadata=dict(extraction.metadata.raw) if extraction.metadata.raw else {},
        chapter_map=extraction.chapter_map,
        extraction_manifest=extraction.extraction_manifest,
        extractor_version=extraction.extraction_manifest.extractor_version,
        status=extraction.status,
        warnings=extraction.warnings,
    )
    intake = CanonicalBookIntakeAdapter().ingest_extracted(request)
    assert intake.submission_eligible

    chapter_map = tuple(
        EpubChapterBoundary(
            index=c.index, spine_position=c.spine_position, title=c.title,
            source_href=c.source_href, start_offset=c.start_offset, end_offset=c.end_offset,
            is_linear=c.is_linear, word_count=c.word_count,
            body_start_offset=c.body_start_offset, body_end_offset=c.body_end_offset,
            landmark_type=c.landmark_type, status=c.status, toc_level=c.toc_level,
        )
        for c in (intake.chapter_map or ())
    )
    resources = tuple(
        ResourceRef(type=r.type, href=r.href, chapter_index=r.chapter_index,
                    metadata=MappingProxyType(dict(r.metadata)))
        for r in (intake.resource_refs or ())
    )
    md = intake.epub_metadata or {}
    raw = md.get("raw", {})
    input_data = EpubTranslationInput(
        source_epub_path=epub_path,
        original_hash=extraction.original_hash,
        extraction_status=extraction.status,
        warnings=extraction.warnings,
        metadata=EpubMetadata(
            title=md.get("title"), author=md.get("author"), language=md.get("language"),
            identifier=md.get("identifier"), publisher=md.get("publisher"), date=md.get("date"),
            raw=MappingProxyType(dict(raw)),
        ),
        chapter_map=chapter_map,
        resources=resources,
        toc_entries=(),
        fixed_layout_info=None,
        extraction_manifest=None,
    )
    return extraction, intake, input_data


def _chunks(input_data: EpubTranslationInput, extracted_text: str):
    from core.epub_translation.chunking import chunk_epub_translation_input

    return chunk_epub_translation_input(input_data, extracted_text, ChunkingOptions())


def _fake_orchestrator_execute(self, chunk_text="", **kwargs):
    """Deterministic echo at the provider-execution boundary only."""
    metadata = kwargs.get("metadata") or {}
    source = metadata.get("source", {}).get("chunk_text", chunk_text)
    return SimpleNamespace(
        response={"status": "success", "translation": source},
        metadata=None,
        session=None,
        request=None,
    )


def _options(input_data: EpubTranslationInput, chunks, tmp_path: Path):
    return EpubTranslationOptions(
        translation_input=input_data,
        chunks=chunks,
        dry_run=False,
        progress_enabled=False,
        character_memory_path=tmp_path / "cm.json",
    )


# ===========================================================================
# 1. Marker-prefixed multi-chapter: two coordinate spaces, real adapter proceeds
# ===========================================================================

def test_s12_06_marker_chunks_have_distinct_spaces_and_validate(tmp_path):
    epub = _make_epub(tmp_path / "book.epub")
    extraction, _intake, input_data = _build_input(epub)
    chunks = _chunks(input_data, extraction.extracted_text)

    assert len(input_data.chapter_map) == 3
    assert len(chunks) == 3

    # At least one chunk must prove the two spaces differ numerically.
    differing = [
        c for c in chunks
        if c.body_start_offset != c.extracted_start_offset
    ]
    assert differing, "expected body-relative vs extracted-absolute to differ"

    first = chunks[0]
    ch1 = input_data.chapter_map[0]
    marker = f"=== CHAPTER {ch1.index}: {ch1.title} ===\n"
    # Explicit S12-05 relationship: body-relative 0 vs extracted-absolute marker end.
    assert first.body_start_offset == 0
    assert first.extracted_start_offset == ch1.body_start_offset == len(marker)
    assert first.body_start_offset != first.extracted_start_offset

    # Every chunk validates (repaired validator).
    for c in chunks:
        validate_epub_translation_chunk(c)
    validate_chunk_ownership(input_data, chunks)


def test_s12_06_content_mapping_proof(tmp_path):
    epub = _make_epub(tmp_path / "book.epub")
    extraction, _intake, input_data = _build_input(epub)
    text = extraction.extracted_text
    chunks = _chunks(input_data, text)

    by_chapter = {}
    for c in chunks:
        by_chapter.setdefault(c.chapter_id, []).append(c)

    for ch in input_data.chapter_map:
        body = text[ch.body_start_offset:ch.body_end_offset]
        for c in by_chapter[ch.chapter_id]:
            # extracted range maps to the same content ...
            assert text[c.extracted_start_offset:c.extracted_end_offset] == c.source_text
            # ... as the chapter-body-relative range does.
            assert body[c.body_start_offset:c.body_end_offset] == c.source_text
            # ranges describe the same segment length.
            assert (c.body_end_offset - c.body_start_offset) == (
                c.extracted_end_offset - c.extracted_start_offset
            )


def test_s12_06_real_adapter_proceeds_past_offset_gate(tmp_path):
    epub = _make_epub(tmp_path / "book.epub")
    extraction, _intake, input_data = _build_input(epub)
    chunks = _chunks(input_data, extraction.extracted_text)
    options = _options(input_data, chunks, tmp_path)

    # Real adapter / input / chunk / validator. Provider boundary stubbed only.
    with patch(_ORCH_EXECUTE, _fake_orchestrator_execute):
        result = translate_epub_translation_input(options, root=tmp_path / "root")

    assert result.total_chapters == 3
    assert result.total_chunks == 3
    assert result.success_count == 3
    # No glossary involved: the defect is offset-only.
    assert options.glossary_path is None
    assert options.glossary_hash is None


# ===========================================================================
# 2. Marker-free / compatible offsets: existing behavior preserved
# ===========================================================================

def test_s12_06_marker_free_compatible_case_passes(tmp_path):
    body = "가나다라마바사 " * 200
    ch = EpubChapterBoundary(
        index=1, spine_position=1, title="NoMarker", source_href="x.xhtml",
        start_offset=0, end_offset=len(body),
        body_start_offset=0, body_end_offset=len(body),
        word_count=len(body.split()),
    )
    input_data = EpubTranslationInput(
        source_epub_path=tmp_path / "nomarker.epub",
        original_hash="a" * 64,
        extraction_status="success",
        warnings=(),
        metadata=EpubMetadata("t", None, "ko", "id", None, None, MappingProxyType({})),
        chapter_map=(ch,), resources=(), toc_entries=(), fixed_layout_info=None,
    )
    chunks = _chunks(input_data, body)
    assert chunks
    for c in chunks:
        validate_epub_translation_chunk(c)
        assert c.body_start_offset == c.extracted_start_offset
    validate_chunk_ownership(input_data, chunks)


# ===========================================================================
# 3. Negative validation is still enforced (repair != disable)
# ===========================================================================

def _chunk_stub(**overrides) -> Any:
    base = dict(
        chunk_id="ch0001:chunk0000", chapter_id="ch0001", chapter_order=1,
        chunk_sequence=0, source_text="x",
        extracted_start_offset=10, extracted_end_offset=20,
        body_start_offset=0, body_end_offset=10,
        source_href=None, fragment=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_s12_06_negative_body_offset_rejected():
    with pytest.raises(ContractValidationError, match="non-negative"):
        validate_epub_translation_chunk(_chunk_stub(body_start_offset=-1, body_end_offset=9))


def test_s12_06_reversed_body_range_rejected():
    with pytest.raises(ContractValidationError, match="body_end_offset"):
        validate_epub_translation_chunk(_chunk_stub(body_start_offset=8, body_end_offset=3))
    # The model also rejects it at construction time.
    with pytest.raises(ValueError):
        EpubTranslationChunk(
            chunk_id="ch0001:chunk0000", chapter_id="ch0001", chapter_order=1,
            chunk_sequence=0, source_text="x",
            extracted_start_offset=0, extracted_end_offset=10,
            body_start_offset=8, body_end_offset=3,
            source_href=None, fragment=None,
        )


def test_s12_06_invalid_extracted_range_rejected():
    with pytest.raises(ContractValidationError, match="extracted_end_offset"):
        validate_epub_translation_chunk(
            _chunk_stub(extracted_start_offset=20, extracted_end_offset=10)
        )
    with pytest.raises(ValueError):
        EpubTranslationChunk(
            chunk_id="ch0001:chunk0000", chapter_id="ch0001", chapter_order=1,
            chunk_sequence=0, source_text="x",
            extracted_start_offset=20, extracted_end_offset=10,
            body_start_offset=0, body_end_offset=10,
            source_href=None, fragment=None,
        )


def test_s12_06_range_mismatch_rejected():
    # body range (10) != extracted range (5): same-contract invariant still enforced.
    with pytest.raises(ContractValidationError, match="must equal extracted range"):
        validate_epub_translation_chunk(
            _chunk_stub(extracted_start_offset=0, extracted_end_offset=5)
        )


def test_s12_06_range_exceeds_owning_text_rejected():
    ch = EpubChapterBoundary(
        index=1, spine_position=1, title="Ch", source_href="x.xhtml",
        start_offset=0, end_offset=50, body_start_offset=10, body_end_offset=45,
        word_count=10,
    )
    input_data = EpubTranslationInput(
        source_epub_path=Path("x.epub"),
        original_hash="a" * 64,
        extraction_status="success",
        warnings=(),
        metadata=EpubMetadata("t", None, "ko", "id", None, None, MappingProxyType({})),
        chapter_map=(ch,), resources=(), toc_entries=(), fixed_layout_info=None,
    )
    # extracted range ends at 60 > chapter.end_offset (50) -> owning-text bound violated.
    chunk = EpubTranslationChunk(
        chunk_id="ch0001:chunk0000", chapter_id="ch0001", chapter_order=1,
        chunk_sequence=0, source_text="x" * 20,
        extracted_start_offset=40, extracted_end_offset=60,
        body_start_offset=0, body_end_offset=20,
        source_href="x.xhtml", fragment=None,
    )
    validate_epub_translation_chunk(chunk)  # range-equality holds
    with pytest.raises(ContractValidationError, match="after chapter end_offset"):
        validate_chunk_ownership(input_data, (chunk,))


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])

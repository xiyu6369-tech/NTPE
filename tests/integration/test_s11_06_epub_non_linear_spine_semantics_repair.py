"""S11-06 — EPUB non-linear spine semantics repair regression.

Locks DEF-1 (S11-05): the packaged EPUB must re-emit ``linear="no"`` for source
non-linear spine items, while ordering / identity / resources are unchanged.

Real production path, no ordering-critical mocking:

  EPUB fixture -> extraction -> intake -> EpubTranslationInput -> chunking
  -> deterministic injected runtime -> real packaging -> persisted EPUB
  -> fresh reopen + OPF spine parse.

Provider = 0, network = 0, real translation = 0.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from types import MappingProxyType
from xml.etree import ElementTree as ET

from core.adapters.canonical_book_intake_adapter import CanonicalBookIntakeAdapter
from core.adapters.epub_extraction_boundary import (
    EpubExtractionBoundary,
    ExtractedTextIntakeRequest,
)
from core.epub_translation.chunking import ChunkingOptions, chunk_epub_translation_input
from core.epub_translation.contract import (
    EpubChapterBoundary,
    EpubChapterResult,
    EpubChunkResult,
    EpubMetadata,
    EpubTranslationInput,
    EpubTranslationResult,
    ResourceRef,
)
from core.epub_translation.reader_chapter_map import build_epub_reader_chapter_map_with_metadata
from core.epub_translation.runtime.epub_packager import (
    EpubPackagingInput,
    pack_epub_resource_aware,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_TITLE = "S11-06 Semantics Book"
_AUTHOR = "S11-06 Author"
_LANGUAGE = "en"
_IDENTIFIER = "urn:uuid:s11-06-fixture"

# Manifest declaration order deliberately differs from spine order.
MANIFEST_ORDER = ["item2", "item0", "item4", "item1", "item3"]
# Canonical spine: linear / non-linear / linear / non-linear / linear.
SPINE = [
    ("item0", "yes"),
    ("item1", "no"),
    ("item2", "yes"),
    ("item3", "no"),
    ("item4", "yes"),
]
EXPECTED_POSITIONS = [1, 2, 3, 4, 5]
EXPECTED_IDS = ["ch0001", "ch0002", "ch0003", "ch0004", "ch0005"]
EXPECTED_IS_LINEAR = [True, False, True, False, True]
EXPECTED_BASENAMES = ["item0.xhtml", "item1.xhtml", "item2.xhtml", "item3.xhtml", "item4.xhtml"]
# ebooklib omits `linear` for linear items; `None` == default yes.
EXPECTED_FINAL_LINEAR = [None, "no", None, "no", None]


def make_interspersed_epub(tmp_path: Path, name: str = "semantics_book.epub") -> Path:
    epub_path = tmp_path / name
    manifest_items = "".join(
        f'    <item id="{iid}" href="{iid}.xhtml" media-type="application/xhtml+xml"/>'
        for iid in MANIFEST_ORDER
    )
    manifest_items += '\n    <item id="img" href="img.png" media-type="image/png"/>'
    spine_items = "".join(
        f'    <itemref idref="{iid}" linear="{linear}"/>' for iid, linear in SPINE
    )
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{_TITLE}</dc:title>
    <dc:creator>{_AUTHOR}</dc:creator>
    <dc:language>{_LANGUAGE}</dc:language>
    <dc:identifier id="bookid">{_IDENTIFIER}</dc:identifier>
  </metadata>
  <manifest>
{manifest_items}
  </manifest>
  <spine>
{spine_items}
  </spine>
</package>""",
        )
        for iid, _linear in SPINE:
            image = '<img src="img.png" alt="figure"/>' if iid == "item0" else ""
            body = (
                f"This chapter item is identified by the unique marker "
                f"CHAPTER_{iid.upper()} and continues with several ordinary English "
                f"words of prose."
            )
            zf.writestr(
                f"OEBPS/{iid}.xhtml",
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<html xmlns="http://www.w3.org/1999/xhtml">'
                f"<head><title>{iid}</title></head>"
                f"<body><h1>{iid}</h1><p>{body}</p>{image}</body></html>",
            )
        zf.writestr("OEBPS/img.png", b"\x89PNG\r\n\x1a\ns11-06")
    return epub_path


def extract_and_intake(epub_path: Path):
    result = EpubExtractionBoundary().extract(epub_path)
    request = ExtractedTextIntakeRequest(
        source_path=result.source_path,
        source_format="epub",
        extracted_text=result.extracted_text,
        original_file_hash=result.original_hash,
        extracted_text_hash=result.extracted_hash,
        epub_metadata=dict(result.metadata.raw) if result.metadata.raw else {},
        chapter_map=result.chapter_map,
        extraction_manifest=result.extraction_manifest,
        extractor_version=result.extraction_manifest.extractor_version,
        status=result.status,
        warnings=result.warnings,
    )
    intake = CanonicalBookIntakeAdapter().ingest_extracted(request)
    return result, intake


def build_translation_input(epub_path: Path, result, intake) -> EpubTranslationInput:
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
    return EpubTranslationInput(
        source_epub_path=epub_path,
        original_hash=result.original_hash,
        extraction_status=result.status,
        warnings=result.warnings,
        metadata=EpubMetadata(
            title=md.get("title"), author=md.get("author"), language=md.get("language"),
            identifier=md.get("identifier"), publisher=md.get("publisher"), date=md.get("date"),
            raw=MappingProxyType(dict(md.get("raw", {}))),
        ),
        chapter_map=chapter_map,
        resources=resources,
        toc_entries=(),
        fixed_layout_info=None,
    )


def deterministic_epub_runtime(options, root=None, engine=None) -> EpubTranslationResult:
    by_chapter: dict[str, list] = {}
    for chunk in options.chunks:
        by_chapter.setdefault(chunk.chapter_id, []).append(chunk)

    chapter_results = []
    for order, chapter in enumerate(options.translation_input.chapter_map, start=1):
        chapter_chunks = sorted(by_chapter.get(chapter.chapter_id, []), key=lambda c: c.chunk_sequence)
        chunk_results = []
        texts = []
        for chunk in chapter_chunks:
            translated = f"[ZH:{chapter.chapter_id}] {chunk.source_text}"
            texts.append(translated)
            chunk_results.append(EpubChunkResult(
                chunk_id=chunk.chunk_id, status="success", translated_text=translated,
                error=None, attempt=1, qa_report=MappingProxyType({}),
                metadata=MappingProxyType({}),
            ))
        assembled = "\n\n".join(texts).strip()
        if assembled:
            assembled += "\n"
        chapter_results.append(EpubChapterResult(
            chapter_id=chapter.chapter_id, chapter_order=order,
            chunk_results=tuple(chunk_results), aggregate_status="success",
            success_count=len(chunk_results), failed_count=0, skipped_count=0,
            assembled_text=assembled,
        ))

    return EpubTranslationResult(
        aggregate_status="success",
        chapter_results=tuple(chapter_results),
        success_count=sum(c.success_count for c in chapter_results),
        failed_count=0,
        skipped_count=0,
        session_id="s11-06-deterministic",
        resume_state_path=None,
    )


def run_direct_pipeline(tmp_path: Path) -> Path:
    """Real extraction -> intake -> input -> chunking -> injected runtime -> packaging."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = make_interspersed_epub(tmp_path)
    result, intake = extract_and_intake(source)
    ti = build_translation_input(source, result, intake)
    chunks = chunk_epub_translation_input(ti, result.extracted_text, ChunkingOptions(chunk_size=1000))
    translation_result = deterministic_epub_runtime(
        type("O", (), {"chunks": chunks, "translation_input": ti})()
    )
    reader = build_epub_reader_chapter_map_with_metadata(
        translation_result=translation_result, translation_input=ti
    )
    output = tmp_path / "out" / "semantics_book_zh.epub"
    output.parent.mkdir(parents=True, exist_ok=True)
    packaging = pack_epub_resource_aware(
        packaging_input=EpubPackagingInput(
            reader_chapter_map_result=reader,
            translation_input=ti,
            translation_result=translation_result,
        ),
        output_path=output,
    )
    assert packaging.success, packaging.validation_errors
    assert output.is_file()
    return output


def read_final_spine(path: Path) -> list[tuple[str, str | None, str | None]]:
    """Fresh reopen; return [(chapter_basename, linear_attr, marker)] in spine order."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        by_base = {Path(n).name: n for n in names}
        opf_name = next(n for n in names if n.endswith(".opf"))
        root = ET.fromstring(zf.read(opf_name))
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        manifest = {it.get("id"): it.get("href") for it in root.findall(".//opf:manifest/opf:item", ns)}
        entries: list[tuple[str, str | None, str | None]] = []
        for ir in root.findall(".//opf:spine/opf:itemref", ns):
            idref = ir.get("idref")
            href = manifest.get(idref)
            if not href or not href.endswith(".xhtml"):
                continue
            base = Path(href).name
            if idref == "nav" or base == "nav.xhtml":
                continue
            content = zf.read(by_base[base]).decode("utf-8")
            match = re.search(r"\[ZH:(ch\d{4})\]", content)
            entries.append((base, ir.get("linear"), match.group(1) if match else None))
        return entries


def test_s11_06_source_and_input_preserve_linear_semantics(tmp_path: Path) -> None:
    source = make_interspersed_epub(tmp_path)
    result = EpubExtractionBoundary().extract(source)
    assert [c.is_linear for c in result.chapter_map] == EXPECTED_IS_LINEAR
    assert [c.spine_position for c in result.chapter_map] == EXPECTED_POSITIONS

    _result, intake = extract_and_intake(source)
    ti = build_translation_input(source, result, intake)
    assert [c.is_linear for c in ti.chapter_map] == EXPECTED_IS_LINEAR
    assert [c.status for c in ti.chapter_map] == ["linear", "supplementary", "linear", "supplementary", "linear"]


def test_s11_06_final_epub_preserves_non_linear_semantics(tmp_path: Path) -> None:
    output = run_direct_pipeline(tmp_path)
    entries = read_final_spine(output)

    # B. final EPUB declares linear semantics: None (default yes) vs explicit "no".
    assert [linear for _base, linear, _marker in entries] == EXPECTED_FINAL_LINEAR

    # C. ordering unchanged by the semantics repair.
    assert [base for base, _linear, _marker in entries] == EXPECTED_BASENAMES

    # D. chapter identity unchanged.
    assert [marker for _base, _linear, marker in entries] == EXPECTED_IDS

    # A sanity check: supplementary items are explicitly "no", not merely None.
    assert entries[1][1] == "no" and entries[3][1] == "no"


def test_s11_06_final_epub_resource_mapping_unaffected(tmp_path: Path) -> None:
    output = run_direct_pipeline(tmp_path)
    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
    assert any(Path(n).name == "img.png" for n in names)

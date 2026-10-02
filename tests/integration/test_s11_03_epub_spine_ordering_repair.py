"""S11-03 — EPUB spine ordering repair regression.

Deterministic, offline. Provider = 0, network = 0, real translation = 0.

Locks the canonical extraction contract established by S11-02:

  * canonical reading order = ``<spine><itemref>`` document order
    (``spine_position``, 1-based);
  * interspersed ``linear="no"`` items are retained at their spine position and
    marked ``is_linear=False`` (never dropped, never moved to the end);
  * ``chapter_id = ch{spine_position:04d}`` is stable and spine-derived;
  * manifest declaration order does not control chapter order.

The defect (before the repair) emitted ``linear_items + supplementary_items``,
producing ``spine_position = 1,3,5,2,4`` for the fixture below.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

from core.adapters.epub_extraction_boundary import EpubExtractionBoundary
from core.epub_translation.chunking import (
    ChunkingOptions,
    chunk_epub_translation_input,
)
from core.epub_translation.contract import (
    EpubChapterBoundary,
    EpubMetadata,
    EpubTranslationInput,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


_CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

# Manifest declaration order deliberately differs from the spine order, to prove
# manifest insertion order is not the canonical ordering source.
_MANIFEST_ORDER = ["item2", "item0", "item4", "item1", "item3"]

# Canonical spine: linear / non-linear / linear / non-linear / linear.
_SPINE = [
    ("item0", "yes"),
    ("item1", "no"),
    ("item2", "yes"),
    ("item3", "no"),
    ("item4", "yes"),
]

_EXPECTED_TITLES = ["item0", "item1", "item2", "item3", "item4"]
_EXPECTED_SPINE_POSITIONS = [1, 2, 3, 4, 5]
_EXPECTED_CHAPTER_IDS = ["ch0001", "ch0002", "ch0003", "ch0004", "ch0005"]
_EXPECTED_IS_LINEAR = [True, False, True, False, True]
_EXPECTED_STATUS = ["linear", "supplementary", "linear", "supplementary", "linear"]


def _build_opf() -> str:
    manifest_items = "".join(
        f'    <item id="{iid}" href="{iid}.xhtml" media-type="application/xhtml+xml"/>'
        for iid in _MANIFEST_ORDER
    )
    spine_items = "".join(
        f'    <itemref idref="{iid}" linear="{linear}"/>'
        for iid, linear in _SPINE
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Ordering Book</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">urn:uuid:s11-03-fixture</dc:identifier>
  </metadata>
  <manifest>
{manifest_items}
  </manifest>
  <spine>
{spine_items}
  </spine>
</package>"""


def make_interspersed_epub(tmp_path: Path) -> Path:
    """Deterministic EPUB3 fixture with interspersed linear="no" spine items."""
    epub_path = tmp_path / "ordering.epub"
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", _CONTAINER)
        zf.writestr("OEBPS/content.opf", _build_opf())
        for iid, _linear in _SPINE:
            zf.writestr(
                f"OEBPS/{iid}.xhtml",
                (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<html xmlns="http://www.w3.org/1999/xhtml">'
                    f"<head><title>{iid}</title></head>"
                    f"<body><h1>{iid}</h1><p>Body of {iid}.</p></body></html>"
                ),
            )
    return epub_path


def _extract(tmp_path: Path):
    return EpubExtractionBoundary().extract(make_interspersed_epub(tmp_path))


def _build_translation_input(result) -> EpubTranslationInput:
    chapter_map = tuple(
        EpubChapterBoundary(
            index=c.index,
            spine_position=c.spine_position,
            title=c.title,
            source_href=c.source_href,
            start_offset=c.start_offset,
            end_offset=c.end_offset,
            is_linear=c.is_linear,
            word_count=c.word_count,
            body_start_offset=c.body_start_offset,
            body_end_offset=c.body_end_offset,
            landmark_type=c.landmark_type,
            status=c.status,
            toc_level=c.toc_level,
        )
        for c in result.chapter_map
    )
    valid_statuses = {"success", "partial", "manual_review_required", "blocked"}
    metadata = result.metadata
    return EpubTranslationInput(
        source_epub_path=result.source_path,
        original_hash=result.original_hash,
        extraction_status=result.status if result.status in valid_statuses else "success",
        warnings=result.warnings,
        metadata=EpubMetadata(
            title=metadata.title,
            author=metadata.author,
            language=metadata.language,
            identifier=metadata.identifier,
            publisher=metadata.publisher,
            date=metadata.date,
            raw=metadata.raw,
        ),
        chapter_map=chapter_map,
        resources=(),
        toc_entries=(),
        fixed_layout_info=None,
        extraction_manifest=None,
    )


def test_interspersed_non_linear_items_preserve_canonical_spine_order(tmp_path: Path) -> None:
    """A. canonical order, B. non-linear preservation, C. chapter identity."""
    result = _extract(tmp_path)
    cm = result.chapter_map

    # A. canonical order == spine_position ascending.
    assert [c.spine_position for c in cm] == _EXPECTED_SPINE_POSITIONS
    assert [c.index for c in cm] == _EXPECTED_SPINE_POSITIONS
    assert [c.title for c in cm] == _EXPECTED_TITLES

    # Insufficient to check length: assert the exact interspersed order.
    assert [c.spine_position for c in cm] != [1, 3, 5, 2, 4]

    # B. non-linear items retained and marked.
    assert len(cm) == 5
    assert [c.is_linear for c in cm] == _EXPECTED_IS_LINEAR
    assert [c.status for c in cm] == _EXPECTED_STATUS

    # C. identity stays spine-derived (no renumbering). The extraction boundary
    # exposes `spine_position`; `chapter_id` is derived from it at the contract
    # layer (asserted in test_downstream_chunking_accepts_canonical_order_...).
    assert [c.spine_position for c in cm] == _EXPECTED_SPINE_POSITIONS

    # Offsets remain contiguous and cover the extracted text.
    for prev, cur in zip(cm, cm[1:]):
        assert prev.end_offset == cur.start_offset
    assert cm[0].start_offset == 0
    assert cm[-1].end_offset == len(result.extracted_text)

    # Extracted text is emitted in canonical spine order.
    marker_titles = re.findall(r"=== CHAPTER \d+: (.+?) ===", result.extracted_text)
    assert marker_titles == _EXPECTED_TITLES


def test_canonical_order_independent_of_manifest_declaration_order(tmp_path: Path) -> None:
    """D. manifest declaration order does not control chapter order."""
    result = _extract(tmp_path)

    # Manifest declares item2,item0,item4,item1,item3; canonical order must still
    # follow the spine (item0..item4).
    assert _MANIFEST_ORDER != _EXPECTED_TITLES
    assert [c.title for c in result.chapter_map] == _EXPECTED_TITLES


def test_extraction_is_deterministic(tmp_path: Path) -> None:
    """E. repeated extraction yields identical order, identity, classification."""
    first = _extract(tmp_path)
    second = _extract(tmp_path)

    def signature(result):
        return [
            (
                c.index,
                c.spine_position,
                c.title,
                c.is_linear,
                c.status,
                c.start_offset,
                c.end_offset,
                c.body_start_offset,
                c.body_end_offset,
            )
            for c in result.chapter_map
        ]

    assert signature(first) == signature(second)
    assert first.extracted_text == second.extracted_text
    assert first.extracted_hash == second.extracted_hash


def test_downstream_chunking_accepts_canonical_order_without_compensation(
    tmp_path: Path,
) -> None:
    """Extraction output is accepted downstream; no compensating sort is needed."""
    result = _extract(tmp_path)
    translation_input = _build_translation_input(result)

    # C. chapter identity is spine-derived and stable across the repair.
    assert [c.chapter_id for c in translation_input.chapter_map] == _EXPECTED_CHAPTER_IDS
    assert [c.spine_position for c in translation_input.chapter_map] == _EXPECTED_SPINE_POSITIONS

    chunks = chunk_epub_translation_input(
        translation_input,
        result.extracted_text,
        ChunkingOptions(chunk_size=1000),
    )

    chapter_order: list[str] = []
    for chunk in chunks:
        if chunk.chapter_id not in chapter_order:
            chapter_order.append(chunk.chapter_id)

    assert chapter_order == _EXPECTED_CHAPTER_IDS

    # Each chunk's chapter_order matches its chapter's canonical spine_position;
    # no downstream compensating sort is required.
    spine_position_by_chapter = {
        c.chapter_id: c.spine_position for c in translation_input.chapter_map
    }
    assert all(
        chunk.chapter_order == spine_position_by_chapter[chunk.chapter_id]
        for chunk in chunks
    )

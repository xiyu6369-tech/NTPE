# P0 RM-8.4 Packaging Contract Report

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b

---

## Packaging Architecture

```
RM-8.3 Final TXT (Source of Truth)
    ����
Chapter Mapping (core/translation_release/reader_structure/chapter_mapper.py)
    ����
ReaderChapterMap (immutable)
    ����
EPUB Packaging (core/translation_release/reader_structure/epub_packager.py)
    ����
EPUB File (optional, non-blocking)
```

---

## Chapter Mapper

**File**: `core/translation_release/reader_structure/chapter_mapper.py`  
**Function**: `build_reader_chapter_map()`

### Signature

```python
def build_reader_chapter_map(
    *,
    txt_body: str,
    translated_chunks: list[str],
    chunk_records: list[dict],
    skip_assembly_validation: bool = False,
) -> ReaderChapterMap:
```

### Inputs

| Parameter | Source | Purpose |
|-----------|--------|---------|
| `txt_body` | RM-8.3 polished TXT | **Source of Truth** — not modified |
| `translated_chunks` | List of chunk translations | Used to align chunk boundaries to TXT |
| `chunk_records` | Runtime chunk records | Contains QA, metadata, context_state |
| `skip_assembly_validation` | Bool | If True, skips `reconstructed == txt_body` check |

### Output: ReaderChapterMap (Immutable Dataclass)

```python
@dataclass(frozen=True)
class ReaderChapterMap:
    chapters: tuple[ChapterBoundary, ...]
    assembly_validated: bool
    txt_body_hash: str  # SHA256 of txt_body
```

### ChapterBoundary (Immutable Dataclass)

```python
@dataclass(frozen=True)
class ChapterBoundary:
    chapter_id: str
    chapter_title: str
    start_position: int      # 0-based, inclusive
    end_position: int        # 0-based, exclusive
    chunk_indices: tuple[int, ...]  # Which runtime chunks map to this chapter
```

### Mapping Algorithm

1. **Explicit markers**: Scans `txt_body` for chapter patterns (`第N章`, `Chapter N`, etc.)
2. **Fallback**: If no markers, creates single chapter covering entire text
3. **Chunk alignment**: Maps runtime chunks to chapter boundaries by character position
4. **Validation**: Unless `skip_assembly_validation=True`, verifies reconstructed text == `txt_body`

---

## EPUB Packager

**File**: `core/translation_release/reader_structure/epub_packager.py`  
**Function**: `pack_epub()`

### Signature

```python
def pack_epub(
    *,
    txt_body: str,
    reader_chapter_map: ReaderChapterMap,
    novel_id: str,
    output_path: Path,
    metadata: dict[str, Any] | None = None,
) -> bool:
```

### Contract Guarantees

| Guarantee | Implementation |
|-----------|----------------|
| **Read-only** | `txt_body` is NOT modified (line 221: "This is a READ-ONLY packaging operation") |
| **Source of Truth** | `txt_body` = RM-8.3 final TXT (line 224) |
| **Validation** | `_validate_chapter_map_integrity()` — fails fast on gaps/overlaps (lines 90-132) |
| **Content preservation** | Reconstructs text from chapters, verifies == `txt_body` (lines 126-131) |
| **Non-blocking** | Returns `False` on failure (ImportError, OSError, ValueError) — never raises |
| **Graceful degradation** | Core delivery (TXT + Manifest + QC) succeeds even if EPUB fails |

### EPUB Structure

- **Chapters**: One `.xhtml` per `ChapterBoundary` (sliced from `txt_body`)
- **Navigation**: `nav.xhtml` with TOC links
- **Styling**: `style.css` with CJK-appropriate typography
- **Metadata**: DC title, author, translator, date, pipeline version
- **Spine/TOC**: Ordered chapters + nav

### Validation (Deterministic Failure)

```python
def _validate_chapter_map_integrity(chapters, txt_body):
    # 1. First chapter starts at 0
    # 2. Last chapter ends at len(txt_body)
    # 3. No gaps/overlaps between adjacent chapters
    # 4. Reconstructed text == txt_body (CONTENT PRESERVATION INVARIANT)
    # Raises ValueError on any violation
```

---

## TXT as Source of Truth — Verified

### Evidence from epub_packager.py

```python
# Line 219-225: Docstring
"""Package EPUB from RM-8.3 TXT body using Phase 1 ReaderChapterMap.

This is a READ-ONLY packaging operation. The txt_body is NOT modified.
...
txt_body: The final RM-8.3 TXT body (source of truth, not modified)
"""

# Line 243: Validation uses txt_body as reference
_validate_chapter_map_integrity(chapters, txt_body)

# Line 269: Chapter text SLICED from txt_body (not reconstructed)
chapter_text = _slice_chapter_text(txt_body, chapter)

# Line 307: Content preservation invariant
if reconstructed != txt_body:
    raise ValueError("Content preservation invariant violated...")
```

### Evidence from delivery_pipeline.py

```python
# Line 200-205: build_reader_chapter_map called with polished_text as txt_body
reader_chapter_map = build_reader_chapter_map(
    txt_body=polished_text,  # RM-8.3 polished TXT
    translated_chunks=translated_chunks,
    chunk_records=chunk_records,
    skip_assembly_validation=True,  # Already validated by polish/canonicalization
)
```

---

## Optional / Non-Blocking — Verified

### delivery_pipeline.py Lines 196-226

```python
if "epub" in formats:
    try:
        reader_chapter_map = build_reader_chapter_map(...)
        if pack_epub(...):
            epub_path = str(epub_candidate)
    except (ImportError, AttributeError, ValueError, OSError):
        # EPUB packaging failure MUST NOT break Core Delivery
        pass  # graceful: format unavailable, validation failed, or I/O error
```

### epub_packager.py Lines 236-239, 304-307

```python
try:
    from ebooklib import epub
except ImportError:
    return False  # graceful: format unavailable

# ...

try:
    epub.write_epub(str(output_path), book)
except OSError:
    return False  # graceful: I/O error
```

---

## Contract Compliance Matrix

| Requirement | Status | Evidence |
|-------------|--------|----------|
| TXT is Source of Truth | ������ PASS | `txt_body` never modified, only sliced |
| EPUB optional | ������ PASS | Gated by `formats` tuple, try/except |
| Explicit opt-in | ������ PASS | `--quality-delivery-formats-v83 epub` |
| Non-blocking | ������ PASS | Delivery continues on EPUB failure |
| Cannot modify TXT | ������ PASS | Read-only slicing, validation against original |
| Packaging failure ���� invalidate TXT | ������ PASS | Core delivery returns success before EPUB attempt |

---

## DRIFT_FOUND: None

RM-8.4 packaging contract fully compliant with specification:
- TXT is immutable Source of Truth
- EPUB is optional, explicit opt-in, non-blocking
- Content preservation invariant enforced
- Graceful degradation on missing dependency / I/O error / validation failure
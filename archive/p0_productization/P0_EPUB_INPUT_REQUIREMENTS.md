# P0 EPUB Input Gap Analysis

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b

---

## Current State

**NO EPUB INPUT EXTRACTION EXISTS IN REPOSITORY**

- Search for "epub.*extract", "extract.*epub", "EPUB.*input" → **0 results**
- No `EpubExtractionBoundary` or similar abstraction exists
- No EPUB → TXT conversion pipeline
- `ui/translation_launcher/app.py` line 106 shows planned support in file dialog: `("Planned formats", "*.epub *.docx *.pdf")` but no implementation

---

## Required Contract: EPUB Input Extraction

### Boundary Definition

```
EPUB Input
    ��
EpubExtractionBoundary (NEW — P0)
    ��
Extracted TXT (canonical input)
    ��
Canonical Book Intake (core/book_intake/) — EXISTING, FROZEN
    ��
TranslationRuntime / LTS Runtime
```

### EpubExtractionBoundary Contract (to be implemented in P0)

#### Input
- EPUB file path
- Optional: extraction options (chapter detection, metadata preservation)

#### Output
- **Extracted TXT** — canonical text body for translation
- **Extraction Manifest** — immutable record of extraction process

#### Must Preserve

| Artifact | Description |
|----------|-------------|
| Original EPUB hash | SHA256 of source EPUB file |
| Original metadata | Title, author, language, publisher, ISBN, etc. |
| Extraction manifest | Chapter map, extraction method, warnings |
| Extracted TXT identity | Content fingerprint (SHA256 of extracted text) |
| Extraction errors | Any parsing failures, missing chapters, encoding issues |

#### Extraction Requirements

1. **Chapter-ordered text** — Concatenate chapters in reading order
2. **Metadata extraction** — DC metadata (title, creator, language, identifier)
3. **Structure preservation** — Chapter boundaries marked for downstream mapping
4. **Graceful degradation** — Skip unreadable chapters, log warnings, continue
5. **No translation** — Pure extraction, no provider calls
6. **Deterministic** — Same EPUB → same extracted TXT + manifest

#### Interface (Proposed)

```python
@dataclass(frozen=True)
class EpubExtractionResult:
    source_path: Path
    original_hash: str           # SHA256 of EPUB
    extracted_text: str          # Canonical TXT body
    extracted_hash: str          # SHA256 of extracted text
    metadata: EpubMetadata       # DC metadata
    chapter_map: list[ChapterBoundary]  # For RM-8.4 packaging alignment
    extraction_manifest: ExtractionManifest
    status: str                  # "success" | "partial" | "failed"
    warnings: tuple[str, ...]
```

---

## Critical Separation

> **EPUB Input Extraction �� EPUB Output Packaging**

| Aspect | EPUB Input Extraction | EPUB Output Packaging (RM-8.4) |
|--------|----------------------|--------------------------------|
| Direction | EPUB → TXT | TXT → EPUB |
| Timing | Pre-translation | Post-translation |
| Source of Truth | Original EPUB | RM-8.3 TXT |
| Abstraction | `EpubExtractionBoundary` | `pack_epub()` / `ReaderChapterMap` |
| Can share code? | **NO** | **NO** |

**Rationale**: 
- Input extraction must preserve original author intent, metadata, structure
- Output packaging consumes translated TXT as SoT, adds reader affordances
- Different failure modes, different validation, different stakeholders
- Mixing them creates circular dependencies and contract confusion

---

## P0 Implementation Note

**Do NOT implement in Stage 0.**  
Only create `P0_EPUB_INPUT_REQUIREMENTS.md` (this file) to define the gap.

Implementation belongs in P0 Productization as `CanonicalBookIntakeAdapter` + `EpubExtractionBoundary` adapter pair.
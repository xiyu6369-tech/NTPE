# P0 Stage 3 Implementation Specification

**Generated**: 2026-08-15  
**Baseline Commit**: ca1c36fabe80e6b9c3d761ba86b7c39fce43e863 (P0 Stage 2 Complete)  
**Phase**: Stage 3 Preflight / Specification Review  

---

## Scope

This specification defines the complete implementation requirements for **P0 Stage 3: EPUB Input Extraction** (`EpubExtractionBoundary` implementation). The implementation must satisfy all 16 specification requirements below and pass the governance gate defined in `P0_STAGE_EXECUTION_GOVERNANCE_CONTRACT.md`.

**Status**: ⏳ SPECIFICATION PHASE — Awaiting review approval before implementation authorization.

---

## Architectural Non-Expansion Rule

> **This Stage Must Not Expand System Architecture**
>
> P0 Stage 3 implements **exactly one new abstraction**: `EpubExtractionBoundary` (EPUB → TXT extraction).
>
> **Prohibited Expansions**:
> - No new runtime, launcher, or pipeline
> - No new checkpoint SoT or resume contract
> - No new provider integration or prompt modification
> - No new translation algorithm or chunking strategy
> - No new delivery format beyond wiring existing RM-8.4 EPUB packager
> - No new UI beyond Reader Web App Import page (already scaffolded in Stage 2)
> - No new configuration schema beyond optional `[epub-extraction]` dependencies
> - No modifications to `core/book_intake/`, `core/translation_runtime/`, `core/translation_release/`
> - No shared code between EPUB input extraction and EPUB output packaging (§12)
> - No modification of pre-existing dirty worktree files outside explicit Stage 3 scope
>
> **Allowed**: Implementation of `EpubExtractionBoundary.extract()`, its dataclasses, security-hardened ZIP handling, XHTML parsing, and integration with existing `CanonicalBookIntakeAdapter.ingest_extracted()`.
>
> **Enforcement**: `ntpe_validate` + architecture review. Any architectural expansion = Stage failure.
>
> **Stage 3 MUST NOT modify `BookIntakeProcessor` or the canonical Book Intake core contract.**
>
> `CanonicalBookIntakeAdapter.ingest_extracted()` is an adapter-level translation boundary. EPUB-specific provenance MUST remain at the adapter/result boundary and MUST NOT require changes to `core/book_intake/`.
>
> If the existing frozen Book Intake contract cannot accept the specified EPUB provenance without modification, Stage 3 MUST stop and report a contract incompatibility rather than modifying Book Intake.
>
> **Adapter Boundary — Hard Constraint**:
>
> `EpubExtractionBoundary` output MUST flow ONLY through:
> ```
> EPUB
>  ↓
> EpubExtractionBoundary
>  ↓
> ExtractedTextIntakeRequest
>  ↓
> CanonicalBookIntakeAdapter
>  ↓
> existing BookIntakeProcessor
> ```
>
> `EpubExtractionBoundary` MUST NOT directly connect to or invoke:
> - `TranslationRuntime`
> - Any provider integration
> - Chunk engine / chunking strategy
> - Resume / checkpoint engine
> - Delivery pipeline
> - Any translation or post-extraction processing
>
> This prevents Stage 3 from establishing a parallel pipeline that bypasses the canonical intake contract.

---

## 1. EPUB Supported Versions & Format Scope

| Parameter | Specification |
|-----------|---------------|
| **EPUB Version** | EPUB 3.0, 3.0.1, 3.1, 3.2, 3.3 (OPS 3.x) — primary target |
| **Legacy Support** | EPUB 2.0.1 (NCX + OPF) — best-effort, warnings on legacy-only features |
| **Container** | OCF ZIP container (uncompressed or deflate). No encrypted containers (AES-256, RSA). |
| **Media Overlays** | SMIL-based Media Overlays (EPUB 3) — skipped with warning; not extracted to text |
| **Fixed Layout** | Fixed-layout EPUB — extracted in spine reading order; viewport metadata preserved in manifest (see **Fixed-Layout Viewport Schema** below) |
| **Remote Resources** | External resources (HTTP/HTTPS) — blocked; extraction fails with `manual_review_required` |
| **Data URIs** | `data:` URIs — not fetched; handled by resource type (image → placeholder, others → warning) |
| **Scripts** | JavaScript in XHTML — stripped with warning; never executed |
| **Fonts** | Embedded fonts (WOFF, WOFF2, TTF, OTF) — preserved in manifest; not extracted to text |
| **MathML** | MathML in XHTML — preserved as text with `[MATHML]` markers; no rendering |
| **SVG** | SVG images — referenced in manifest; not inlined in extracted text |

**Out of Scope**: Encrypted EPUB (Adobe DRM, Readium LCP), EPUB 3.3+ features not yet stabilized, comic/fixed-layout as primary format.

### Fixed-Layout Viewport Schema (Manifest Entry)

When a fixed-layout EPUB is detected (`rendition:layout="pre-paginated"` in OPF metadata), the following viewport metadata is recorded in the extraction manifest:

```json
{
  "fixed_layout": {
    "viewport": {
      "width": 1200,
      "height": 1600,
      "orientation": "portrait"
    },
    "spread": "auto",
    "orientation": "auto",
    "page_progression_direction": "ltr"
  }
}
```

| Field | Source | Required |
|-------|--------|----------|
| `viewport.width` | `rendition:viewport` width or `<meta name="viewport" content="width=...">` | Yes |
| `viewport.height` | `rendition:viewport` height | Yes |
| `viewport.orientation` | `rendition:orientation` | Yes |
| `spread` | `rendition:spread` | No (default: "auto") |
| `orientation` | `rendition:orientation` | No (default: "auto") |
| `page_progression_direction` | `page-progression-direction` in spine or OPF metadata | No (default: "ltr") |

All values recorded as-is from publication metadata; no inference or defaulting beyond explicit EPUB 3 spec defaults.

**Dependency Boundary**:
> **ZIP container security MUST be implemented directly using Python `zipfile` and explicit validation.**
>
> `ebooklib` MUST NOT be used as the security boundary and MUST NOT perform uncontrolled extraction.
>
> If `ebooklib` is retained, its use MUST be limited to EPUB structural interpretation (OPF/NCX/NAV parsing) **after** the ZIP security gate has passed.

---

## 2. EPUB Container / ZIP Security Restrictions

| Restriction | Rule | Violation Result |
|-------------|------|------------------|
| **Max Archive Size** | 500 MB uncompressed | `blocked` |
| **Max Entry Count** | 10,000 entries | `blocked` |
| **Path Traversal** | No `../`, absolute paths, symlinks, UNC paths, drive-letter paths | `blocked` |
| **Zip Slip** | **Do not use `ZipFile.extractall()` directly.** Entries read via controlled `ZipFile.open()`/`read()` after validating every `ZipInfo` member. No archive member may be extracted to disk unless its normalized destination path is proven to remain within the designated temporary extraction root. | `blocked` |
| **Compression Ratio** | Reject entries with > 100:1 ratio (zip bomb) | `blocked` |
| **Nested Archives** | No nested ZIP/EPUB within | `blocked` |
| **Executable Extensions** | `.exe`, `.dll`, `.so`, `.sh`, `.bat`, `.ps1` in archive | `blocked` |
| **Encryption** | Any encrypted entry (`encryption.xml` or per-entry) | `blocked` |
| **Signatures** | `signatures.xml` — ignored with warning | `manual_review_required` |

**Path Validation Rules** (Windows-safe):
- Split `ZipInfo.filename` by POSIX `/` into components. Reject if **any component == `..`** (parent directory traversal).
- Reject absolute paths: Unix (`/...`), Windows drive-letter (`C:\...`, `D:/...`), UNC (`\\server\...`).
- Reject drive-letter prefixes (`C:`, `D:`) and symlink entries (`ZipInfo.is_symlink()` if available).
- Normalize path with `posixpath.normpath` (EPUB uses POSIX paths internally) then verify the resolved path stays within extraction root.
- Canonicalize path (POSIX, lowercased on Windows) and reject duplicate canonical paths.

**Nested Archive Detection**:
- Scan archive members for extensions `.zip`, `.epub`, `.jar`, `.war`, `.ear` or magic signatures (`PK\x03\x04`, `PK\x05\x06`, `PK\x07\x08`).
- **Prohibited**: Extraction, recursive opening, or processing of nested archives. Detection → `blocked`.

**Implementation**: Use `zipfile.ZipFile` with per-member validation. Read entry content via `zf.read(member)` or `zf.open(member)` after all validations pass. No uncontrolled extraction to filesystem.

**Security Invariant**: The extractor MUST NEVER perform network requests. Remote resource references (HTTP/HTTPS) are detected during parsing and result in `manual_review_required`; no fetch is attempted.

---

## 3. XHTML/HTML Chapter Extraction Rules

| Rule | Detail |
|------|--------|
| **Parser** | `lxml.html` with `recover=True`, `remove_comments=True`, `remove_blank_text=True` |
| **Namespace Handling** | XHTML (`http://www.w3.org/1999/xhtml`), HTML5, EPUB namespaces (`epub:`, `opf:`, `dc:`) all supported |
| **Content Selection** | Extract from `<body>` only; ignore `<head>`, `<script>`, `<style>`, `<template>`, `<noscript>` |
| **Block Elements** | `<p>`, `<div>`, `<section>`, `<article>`, `<blockquote>`, `<pre>`, `<ul>`, `<ol>`, `<li>`, `<table>`, `<h1>`-`<h6>` → paragraph-separated text |
| **Structural Elements** | `<header>`, `<footer>`, `<aside>`, `<nav>` — structurally extractable but MAY be excluded when clearly identified as navigation, advertising, site chrome, or non-publication content. Stage 3 MUST NOT implement content classification heuristics beyond available publication structure. |
| **Inline Elements** | `<span>`, `<em>`, `<strong>`, `<i>`, `<b>`, `<u>`, `<sub>`, `<sup>`, `<code>`, `<a>`, `<ruby>`, `<rt>`, `<rp>` → inline text preserved |
| **Ruby/Annotations** | `<ruby>` → `base(rt)` format preserved |
| **Images** | `<img>` → `[IMAGE: src="..." alt="..."]` placeholder; `src` recorded in manifest |
| **Links** | `<a href="...">` → text only; `href` recorded in manifest if internal |
| **Tables** | Linearized row-by-row; headers prefixed with `[TH]` |
| **MathML** | `<math>` → `[MATHML]` + text content; MUST NOT attempt rendering or semantic conversion |
| **SVG** | Inline `<svg>...</svg>` → `[SVG]` placeholder. External `<img src="x.svg">` → `[IMAGE: ...]` + manifest resource. MUST NOT attempt rendering. |
| **Unknown Elements** | Text content extracted; tag name logged in warnings |

**Encoding**: Detect from XML declaration, `<meta charset>`, or BOM. Default UTF-8. Errors → replacement char + warning.

**Entity Decoding**: Single-pass decode only. Example: `&lt;` → `<` (not `<`). Double-encoded entities MUST NOT be fully decoded.

---

## 4. TOC / Spine / Reading-Order Processing

| Source | Priority | Processing |
|--------|----------|------------|
| **EPUB 3 `nav.xhtml` (`<nav epub:type="toc">`)** | 1 (highest) | Parse `<ol>` hierarchy → chapter order + titles |
| **EPUB 3 `nav.xhtml` (`<nav epub:type="landmarks">`)** | 2 | Landmarks (cover, titlepage, toc, chapters) for **semantic classification only** — MUST NOT alter reading order |
| **OPF `<spine>`** | 3 (fallback) | Linear `itemref` order; `linear="no"` items excluded from main text |
| **EPUB 2 NCX (`toc.ncx`)** | 4 (legacy) | `<navPoint>` hierarchy → chapter order |
| **File System Order** | 5 (last resort) | Alphabetical by `href` — warning: unreliable, deterministic fallback only |

**Reading Order Principle**:
> **Spine determines reading order. TOC determines publication chapter metadata. Landmarks determine semantic classification only. Filesystem order is a last-resort deterministic fallback.**

**Chapter Map Construction**:
1. Resolve spine itemrefs to manifest items (by `idref` → `href`), recording original **spine position** (1-based index in OPF spine).
2. For each spine item in **spine order**, parse XHTML → extract text + chapter boundary.
3. If `nav` TOC exists, map TOC entries to spine items by `href` fragment for `title` and `toc_level`.
4. **Chapter Title Precedence** (deterministic, first match wins):
   - Mapped nav/NCX TOC title (from `href` fragment match)
   - First publication heading: `<h1>` → `<h2>` (in document order)
   - Document `<title>` element (from XHTML `<head>`)
   - Generated fallback: `Chapter N` (where N = final `index`)
5. **Final Extraction Order**:
   - All linear spine items (`linear="yes"`) in **original spine order**
   - Then all supplementary spine items (`linear="no"`) in **original spine order**

**Output**: Ordered `tuple[ChapterBoundary, ...]` with `index` (1-based position in final extraction order above), `spine_position` (original OPF spine position, 1-based), `title`, `start_offset`/`end_offset` in extracted text, `source_href`, `landmark_type`.

> **Stage 3 MUST preserve spine reading order but MUST NOT infer literary chapter semantics beyond available publication structure.**
>
> The extractor provides structural metadata (`toc_level`, `landmark_type`, `is_linear`) for downstream consumers (Book Intake, Reader UI) to classify content. Cover, title page, copyright, dedication, TOC, and author notes appear in spine order with their structural classification intact.

---

## 5. Encoding & HTML Entity Handling

| Aspect | Rule |
|--------|------|
| **Detection Order** | 1. XML declaration (`<?xml encoding="...">`) 2. BOM (UTF-8/16/32) 3. `<meta charset="...">` / `<meta http-equiv="Content-Type">` 4. Default UTF-8 |
| **Entity Decoding** | `html.entities.html5` (full HTML5 named entities) + numeric (`&#nnn;`, `&#xhhhh;`) |
| **Invalid Entities** | Unknown named entities → kept as-is + warning |
| **Malformed Numeric** | Out of Unicode range → replacement char (U+FFFD) + warning |
| **Double Encoding** | Detect `<` patterns → single decode pass only |
| **Character Normalization** | NFC normalization applied to extracted text |
| **Newline Normalization** | All newline sequences (CRLF, CR, LF) MUST be normalized to `\n` (LF) before chapter offsets are calculated. |
| **Control Characters** | C0/C1 (except `\n`, `\t`, `\r`) → stripped + warning |

**Entity Decoding Test Case**: `&lt;` → decode once → `<` (NOT `<`). This MUST be verified in deterministic fidelity tests.

---

## 6. Chapter Boundary Definition

```python
@dataclass(frozen=True)
class ChapterBoundary:
    index: int                    # 1-based final chapter_map order (linear items first in spine order, then supplementary items in original spine order)
    spine_position: int           # Original OPF spine position (1-based, matches OPF itemref order)
    title: str | None             # From TOC title precedence (§4); fallback "Chapter N"
    start_offset: int             # Unicode character offset in extracted_text (0-based)
    end_offset: int               # Unicode character offset (exclusive)
    source_href: str | None       # OPF manifest href (e.g., "ch01.xhtml")
    toc_level: int = 0            # TOC nesting depth (0 = top-level)
    is_linear: bool = True        # From spine linear="yes|no"
    word_count: int = 0           # For downstream chunking hints
    landmark_type: str | None = None  # From nav landmarks: cover, titlepage, toc, chapter, etc.
    status: str = "linear"        # "linear" | "supplementary"
```

**Boundary Markers in Extracted Text**:
- Each chapter prepended with `=== CHAPTER {index}: {title or "Untitled"} ===\n`
- Marker included in `start_offset`/`end_offset` calculation
- Offsets are **Unicode code point counts** (not bytes), enabling correct alignment across encodings and RM-8.4 round-trip mapping
- `extracted_text[start_offset:end_offset]` MUST exactly equal the complete chapter segment represented by that `ChapterBoundary`, including the marker and the trailing newline (`\n`) separator.
- **Chapter title** follows deterministic precedence (§4): TOC title → first h1 → first h2 → document <title> → generated `Chapter N`.

**Separator Contract**:
- Every chapter segment (including the last) MUST end with a single `\n` (LF)
- The chapter marker line and all extracted content for that chapter are followed by exactly one `\n`
- No additional blank lines between consecutive chapters

**Offset Invariants**:
- `start_offset` = index of first character of chapter marker
- `end_offset` = index immediately after the trailing `\n` of the chapter segment
- All offsets calculated on extracted_text AFTER newline normalization to `\n`
- **Contiguity**: `chapter[i].end_offset == chapter[i+1].start_offset` for ALL consecutive chapters (linear + supplementary)
- No gaps, overlaps, or negative offsets in the final chapter map

---

## 7. Non-Text Resource Handling (Images, CSS, Fonts, Scripts)

| Resource Type | Handling | Manifest Entry |
|---------------|----------|----------------|
| **Images** (`<img>`, `<image>`) | Placeholder `[IMAGE: src="..."]` in text; `src` + `alt` + dimensions recorded | `{"type": "image", "href": "...", "alt": "...", "chapter_index": N}` |
| **CSS** (`<link rel="stylesheet">`, `<style>`, `@import`, `background-image`) | Ignored for text extraction; `href` recorded for packaging reference; **CSS `background-image` NOT parsed** | `{"type": "css", "href": "...", "media": "..."}` |
| **Fonts** (`@font-face`, `<link rel="preload" as="font">`) | Ignored; font files listed for RM-8.4 packaging | `{"type": "font", "href": "...", "format": "woff2"}` |
| **Scripts** (`<script>`, `onclick`, JS event handlers) | Stripped entirely; `src` logged as warning | `{"type": "script", "href": "...", "stripped": true}` |
| **Audio/Video** (`<audio>`, `<video>`, `<source>`) | Placeholder `[MEDIA: type="audio/video" src="..."]` | `{"type": "media", "href": "...", "mime": "..."}` |
| **SMIL/Media Overlays** | Skipped; `href` recorded | `{"type": "smil", "href": "...", "skipped": true}` |
| **HTTP/HTTPS Resources** | **Never fetched** → extraction status = `manual_review_required` | `href` recorded with `"remote": true` in manifest; no download attempted |
| **Data URIs** (`data:`) | **Not fetched**; image → placeholder + manifest entry with `data_uri: true`; other types → warning only | `href` = `"data:"` (not a downloadable resource); `data_uri: true` flag |

**Resource Manifest Schema** (in `ExtractionManifest`):
```json
{
  "resources": [
    {"type": "image", "href": "images/ch1_illustration.jpg", "alt": "Map", "chapter_index": 1},
    {"type": "css", "href": "styles/main.css", "media": "all"},
    {"type": "font", "href": "fonts/SourceSerif.woff2", "format": "woff2"},
    {"type": "image", "href": "data:", "alt": "inline", "chapter_index": 2, "data_uri": true}
  ]
}
```

> **The extractor MUST NEVER perform network requests.** Remote resource references (HTTP/HTTPS) are detected during parsing and result in `manual_review_required`; no fetch is attempted. Data URIs are handled inline without network I/O.

---

## 8. Malformed EPUB: Failure Status Judgment

| Condition | Status | Reason |
|-----------|--------|--------|
| Missing `META-INF/container.xml` | `blocked` | Not a valid OCF container |
| Missing OPF (`package` element) | `blocked` | No publication metadata |
| OPF parse failure (XML syntax) | `blocked` | Cannot determine structure |
| No spine items | `blocked` | No reading order |
| All spine items `linear="no"` | `manual_review_required` | No primary content — requires user intent decision |
| Encrypted container (`encryption.xml`) | `blocked` | DRM/encryption unsupported |
| Zip bomb detected | `blocked` | Security |
| Path traversal in ZIP | `blocked` | Security |
| Executable archive member | `blocked` | Security |
| Duplicate archive paths (canonicalized) | `blocked` | Security |
| Unsupported encryption metadata | `blocked` | Cannot silently ignore |
| Remote resources referenced (HTTP/HTTPS) | `manual_review_required` | Cannot fetch external content — requires user decision |
| Unreadable XHTML (XML parse error) | `partial` + warning per chapter | Graceful degradation |
| Missing `nav.xhtml` + `toc.ncx` | `partial` | Fallback to spine order |
| Duplicate `id` in spine | `partial` + warning | Use first occurrence (deterministic) |
| Circular `nav` references | `partial` + warning | Break cycle, use spine order |

**Status Enum**: `"success" | "partial" | "manual_review_required" | "blocked"`

### Failure Status Semantics (Hard Contract)

| Status | Meaning | Auto-proceed to Translation | User Action Required |
|--------|---------|----------------------------|---------------------|
| `success` | Complete extraction, no issues | ✅ | No |
| `partial` | Deterministic extraction with known degradations (missing TOC, parse recovery, fallback order) | ✅ | No (warnings preserved) |
| `manual_review_required` | System CAN parse but CANNOT safely decide user intent (remote resources, all-supplementary spine) | ❌ | **Explicit user confirmation in Reader Web App** |
| `blocked` | Security violation or fundamental structural failure | ❌ | **NEVER** (no override possible) |

### Override Boundary

**NEVER Overridable** (always `blocked`, no user override):
- Path traversal, zip bomb, encryption, executable archive member, duplicate canonicalized paths, invalid OCF structure, missing OPF, unsupported encryption metadata.

**Overridable with Explicit User Action** (require `manual_review_required` + explicit user confirmation in Reader Web App):
- Remote resource references (HTTP/HTTPS)
- All spine items `linear="no"` (ambiguous primary content)

**NOT Overridable** (these are `partial`, proceed with warnings):
- Missing TOC (nav + NCX) → `partial` (spine order used)
- Partial XHTML parse errors → `partial` (graceful degradation)
- Duplicate spine ID / circular nav → `partial` (deterministic resolution)

> `manual_review_required` MUST NOT automatically continue into translation. User override MUST be an explicit user action in the Reader Web App and MUST NOT bypass blocked security conditions.

---

## 9. Original EPUB Hash & Extraction Manifest Schema

### Original EPUB Hash
- **Algorithm**: SHA-256
- **Scope**: Entire EPUB file bytes (as read from disk)
- **Format**: Lowercase hex, 64 chars
- **Field**: `EpubExtractionResult.original_hash`

### Extraction Manifest Schema
```python
@dataclass(frozen=True)
class ExtractionManifest:
    extractor_version: str          # e.g., "epub-extraction-v1.0.0"
    extracted_at: str               # ISO 8601 UTC — EXCLUDED from deterministic identity
    chapter_count: int              # Total chapters in chapter_map
    total_characters: int           # Length of extracted_text (Unicode code points)
    total_words: int                # Approximate word count
    warnings: tuple[str, ...]       # All warnings during extraction (deterministic order)
    resources: tuple[ResourceRef, ...]  # Non-text resources (see §7, deterministic order)
    spine_item_count: int           # OPF spine linear items
    nav_toc_entries: int            # TOC entries from nav/NCX
    encoding_used: str              # Detected encoding (e.g., "utf-8")
    parsing_duration_ms: int        # Performance metric — EXCLUDED from deterministic identity
```

**Deterministic Manifest Identity Fields** (used for `Manifest Identity` in §11):
- `extractor_version`, `chapter_count`, `total_characters`, `total_words`
- `warnings`, `resources`, `spine_item_count`, `nav_toc_entries`, `encoding_used`
- **Excluded**: `extracted_at`, `parsing_duration_ms` (non-deterministic runtime values)

**Deterministic Ordering Requirements** (MUST be enforced for reproducible manifest identity):
- `warnings` → emitted in deterministic generation order (spine order, then TOC order, then resource order)
- `resources` → sorted by `(type, href, chapter_index)` lexicographically
- All tuple/dict serialization MUST use canonical JSON with sorted object keys

### ResourceRef
```python
@dataclass(frozen=True)
class ResourceRef:
    type: str                       # "image" | "css" | "font" | "script" | "media" | "smil"
    href: str                       # Relative path in EPUB
    chapter_index: int | None       # Associated chapter (None = global)
    metadata: Mapping[str, Any]     # type-specific (alt, mime, format, etc.) — immutable/canonical
```

> `metadata` MUST be converted to an immutable/canonical representation (e.g., `types.MappingProxyType` or sorted tuple of items) before inclusion in the final manifest. JSON serialization uses canonical key ordering.

---

## 10. Extracted TXT Re-entry into Canonical Book Intake

### 10.1 CanonicalBookIntakeAdapter.ingest_extracted() Contract

```python
@dataclass(frozen=True)
class ExtractedTextIntakeRequest:
    source_path: Path                          # Original EPUB file path
    source_format: str                         # "epub" (literal)
    extracted_text: str                        # Full chapter-concatenated text
    original_file_hash: str                    # SHA256(original EPUB bytes) — 64 hex chars
    extracted_text_hash: str                   # SHA256(extracted_text) — 64 hex chars
    epub_metadata: dict[str, Any]              # DC metadata (title, creator, language, identifier, publisher, date)
    chapter_map: tuple[ChapterBoundary, ...]   # Ordered chapters with Unicode character offsets
    extraction_manifest: ExtractionManifest    # Full manifest (JSON-serializable)
    extractor_version: str                     # e.g., "epub-extraction-v1.0.0"
```

**Method Signature**:
```python
def ingest_extracted(self, request: ExtractedTextIntakeRequest) -> IntakeResult:
    """
    Ingest pre-extracted EPUB text into canonical book intake pipeline.
    
    Preconditions:
    - request.extracted_text_hash == sha256(request.extracted_text)
    - request.original_file_hash == sha256(read_bytes(request.source_path))
    - request.chapter_map offsets are Unicode character offsets into request.extracted_text
    - request.extraction_manifest.chapter_count == len(request.chapter_map)
    
    Postconditions:
    - Returns IntakeResult with status ∈ {"ready", "ready_with_warnings", "manual_review_required", "blocked"}
    - On success: book_id = f"book_{request.original_file_hash[:16]}"
    """
```

### 10.2 Intake Flow

```
EpubExtractionBoundary.extract(epub_path)
    → EpubExtractionResult (extracted_text, chapter_map, manifest)
    → CanonicalBookIntakeAdapter.ingest_extracted(ExtractedTextIntakeRequest(...))
    → Adapter translates EPUB-specific provenance into canonical intake input form
    → BookIntakeProcessor.process()  # Frozen Stage 2.8 — NO CHANGES
    → IntakeResult (status, warnings, book_id)
```

### 10.3 Adapter Mapping Table — Frozen Core Contract

| ExtractedTextIntakeRequest Field | Passed to BookIntakeProcessor | Notes |
|----------------------------------|------------------------------|-------|
| `source_path` | ✅ `source_path` | Required |
| `source_format` | ✅ `source_format` | `"epub"` literal |
| `extracted_text` | ✅ `source_text` | Canonical text payload |
| `original_file_hash` | ✅ `original_file_hash` | Identity derivation |
| `extracted_text_hash` | ✅ `source_text_hash` | Determinism verification |
| `epub_metadata` | ✅ `metadata` | DC metadata dict (existing field) |
| `chapter_map` | ❌ | **Adapter boundary only** — for RM-8.4 alignment |
| `extraction_manifest` | ❌ | **Adapter boundary only** — for provenance audit |
| `extractor_version` | ❌ | **Adapter boundary only** — for reproducibility |

> **HARD GATE**: `BookIntakeProcessor` receives **exactly the same input form** as TXT intake. No EPUB-specific fields (`chapter_map`, `extraction_manifest`, `extractor_version`) are added to the frozen core contract. EPUB-specific provenance is preserved at the **adapter/result boundary** for downstream consumers (Reader UI, delivery pipeline) without touching `core/book_intake/`.

### 10.4 Contract Incompatibility Protocol

If the existing frozen `BookIntakeProcessor` contract cannot accept the required canonical input form:
1. **STOP** — Do not modify `core/book_intake/`
2. Report **CONTRACT INCOMPATIBILITY** with specific missing/conflicting fields
3. Stage 3 implementation halts pending architecture decision

**Identity**: `book_id = f"book_{request.original_file_hash[:16]}"` — same derivation as `ProductionSubmissionAdapter` job identity.

---

## 11. Source Identity Construction Post-Extraction

| Identity Layer | Construction |
|----------------|--------------|
| **Source Identity** | `sha256(original_epub_bytes)[:16]` — immutable, content-addressed |
| **Extraction Identity** | `sha256(extracted_text)[:16]` — verifies extraction determinism |
| **Job Identity** | `job_{source_identity}_{config_fingerprint_16}` — matches `ProductionSubmissionAdapter` |
| **Book Identity** | `book_{source_identity}` — used by `BookIntakeProcessor` for deduplication |
| **Manifest Identity** | `sha256(canonical_json(deterministic_manifest_fields))[:16]` — for manifest versioning |

**Deterministic Manifest Fields** (excludes `extracted_at`, `parsing_duration_ms`):
- `extractor_version`, `chapter_count`, `total_characters`, `total_words`
- `warnings`, `resources`, `spine_item_count`, `nav_toc_entries`, `encoding_used`

**Canonical JSON Serialization** (for Manifest Identity):
- Object keys sorted lexicographically
- Arrays serialized in deterministic order (as defined in §9)
- No whitespace, no trailing commas
- UTF-8 encoding

**Determinism Guarantee**: Same EPUB + same extractor version + same options → identical `extracted_text`, `extracted_hash`, `chapter_map`, `extraction_manifest` (deterministic fields only).

---

## Canonical Data Flow — Stage 3 Responsibility Boundary

```
EPUB file
   │
   ├── SHA-256 original bytes (Source Identity)
   │
   ▼
ZIP Security Gate (fail-closed)
   │
   ├── blocked → STOP (no extraction)
   │
   ▼
OCF / OPF / NAV / NCX structural parsing
   │
   ▼
Spine reading order (deterministic)
   │
   ▼
XHTML extraction (per spine item)
   │
   ├── remote resource (HTTP/HTTPS) → manual_review_required
   ├── malformed chapter → partial + warning
   └── unsupported security → blocked
   │
   ▼
ExtractedText (canonical text payload)
   │
   ├── newline normalized (CRLF/CR → LF)
   ├── NFC normalized
   └── Unicode code-point offsets
   │
   ▼
EpubExtractionResult
   │
   ├── extracted_text
   ├── extracted_hash (Extraction Identity)
   ├── chapter_map (contiguous Unicode offsets)
   ├── extraction_manifest (deterministic fields only)
   ├── original_hash (Source Identity)
   └── status ∈ {success, partial, manual_review_required, blocked}
   │
   ▼
ExtractedTextIntakeRequest
   │
   ▼
CanonicalBookIntakeAdapter.ingest_extracted()
   │
   ▼
Existing BookIntakeProcessor (FROZEN)
   │
   ▼
Existing translation pipeline
```

> **Stage 3 responsibility ends at `EpubExtractionResult`.**
>
> Any translation, chunking, resume, provider, delivery, or post-extraction processing is **NOT part of Stage 3**. Stage 3 delivers a deterministic `EpubExtractionResult` to the adapter boundary; the adapter translates to the frozen canonical intake contract. No parallel pipeline is established.

---

## 12. EPUB Input vs RM-8.4 EPUB Output: Contract Separation

| Dimension | EPUB Input Extraction (P0 Stage 3) | EPUB Output Packaging (RM-8.4) |
|-----------|-----------------------------------|--------------------------------|
| **Direction** | EPUB → TXT | TXT → EPUB |
| **Timing** | Pre-translation | Post-translation |
| **Source of Truth** | Original EPUB file | RM-8.3 TXT + QC Manifest |
| **Abstraction** | `EpubExtractionBoundary` | `pack_epub()`, `ReaderChapterMap` |
| **Code Location** | `core/adapters/epub_extraction_boundary.py` | `core/translation_release/reader_structure/` |
| **Dependencies** | `lxml`, `zipfile` (stdlib); `ebooklib` optional, ONLY for OPF/NCX/NAV parsing AFTER security gate | `ebooklib`, `jinja2`, `css_inline` |
| **Failure Mode** | `blocked` / `manual_review_required` / `partial` | Non-blocking fallback to TXT-only |
| **Stakeholder** | Reader Web App Import | Reader Web App Export / Delivery |
| **Validation** | Structure, security, readability | Reader compliance, rendering |

**Enforcement**: 
- Zero shared code between input extraction and output packaging
- Separate test suites (`tests/unit/adapters/test_epub_extraction_boundary.py` vs `tests/unit/translation_release/test_reader_structure.py`)
- Separate dependency declarations (optional `ebooklib` for input; required for output)

---

## 13. Extraction Failure vs Translation Failure: Error Boundaries

| Layer | Failure Type | Handling | Propagation |
|-------|--------------|----------|-------------|
| **Extraction** | `blocked` (security, corrupt, DRM) | Raise `EpubExtractionError(blocked=True)` | Web App Import UI: show error, no job created |
| **Extraction** | `manual_review_required` (remote resources, ambiguous structure) | Return `EpubExtractionResult(status="manual_review_required", warnings=...)` | Web App Import UI: show review dialog, allow explicit user override |
| **Extraction** | `partial` (some chapters unreadable) | Return `EpubExtractionResult(status="partial", warnings=...)` | Proceed to intake with warnings; user can accept |
| **Extraction** | `success` | Normal flow | — |
| **Intake** | Validation failure (hash mismatch, empty text) | `IntakeResult(status="blocked", errors=...)` | No job submitted |
| **Translation** | Provider/timeout/QC failure | `TranslationRuntime` error handling | Job status `failed`; resume supported |
| **Delivery** | EPUB packaging failure | Non-blocking; TXT delivery continues | Job status `delivered_txt_only` |

**Error Classes**:
```python
class EpubExtractionError(Exception):
    def __init__(self, message: str, blocked: bool = False, warnings: tuple[str, ...] = ()):
        self.blocked = blocked
        self.warnings = warnings
        super().__init__(message)
```

### Override Boundary (Reiterated — Aligned with §8)

**NEVER Overridable** (always `blocked`, no user override):
- Path traversal, zip bomb, encryption, executable archive member, duplicate canonicalized paths, invalid OCF structure, missing OPF, unsupported encryption metadata.

**Overridable with Explicit User Action** (require `manual_review_required`):
- Remote resource references (HTTP/HTTPS)
- All spine items `linear="no"` (ambiguous primary content)

**NOT Overridable — These are `partial` (auto-proceed with warnings)**:
- Missing TOC (nav + NCX) → `partial` (spine order used)
- Partial XHTML parse errors → `partial` (graceful degradation)
- Duplicate spine ID / circular nav → `partial` (deterministic resolution)

> `manual_review_required` MUST NOT automatically continue into translation. User override MUST be an explicit user action in the Reader Web App and MUST NOT bypass blocked security conditions.

---

## 14. Test Matrix

| Category | Test Cases | Target |
|----------|------------|--------|
| **Container Security** | Zip slip, path traversal, zip bomb, nested archive, executable entries, encryption, oversize, duplicate paths, UNC paths, drive-letter paths | 100% blocked |
| **Format Support** | EPUB 3.0/3.1/3.2/3.3, EPUB 2.0.1, fixed-layout, media overlays | All parse |
| **Structure Parsing** | nav TOC, NCX TOC, spine-only, mixed linear/non-linear, landmarks | Correct order |
| **XHTML Extraction** | Block/inline elements, ruby, tables, MathML, SVG, images, links, unknown tags | Text fidelity |
| **Encoding** | UTF-8, UTF-16, ISO-8859-1, Windows-1252, BOM, XML decl, meta charset, double-encoded | Correct decode |
| **Entities** | Named (HTML5), numeric (dec/hex), invalid, out-of-range | Correct handling |
| **Chapter Boundaries** | TOC mapping, auto-titles, supplementary items, offset accuracy | Exact offsets |
| **Resources** | Images, CSS, fonts, scripts, media, SMIL, remote refs, data URIs | Manifest complete |
| **Malformed** | Missing container.xml, missing OPF, bad XML, empty spine, duplicate IDs, circular nav | Correct status |
| **Determinism** | Same EPUB × N runs → identical output | 100% |
| **Integration** | Extract → Intake → Job Identity → Resume | End-to-end |
| **Performance** | 50MB EPUB < 5s, 200MB < 15s | Benchmark targets only — **performance failure cannot block functional acceptance unless benchmark gate is explicitly activated** |
| **Edge Cases** | Zero chapters, whitespace-only, huge single chapter, deep TOC nesting | Handled |
| **Security Invariants** | Provider Requests = 0, Network Requests = 0 in all tests; remote URL detection → no HTTP request performed | 100% |

**Test Location**: `tests/unit/adapters/test_epub_extraction_boundary.py` (expanded) + `tests/integration/test_epub_extraction_e2e.py` (new)

### Fixture Requirements

```
tests/fixtures/epub/
├── valid_epub3/
├── valid_epub2/
├── nav_epub/
├── ncx_epub/
├── spine_only/
├── malformed/
├── security/
├── encoding/
├── resources/
└── golden/
```

Each important fixture MUST have golden outputs:
- `expected.txt` — exact extracted text (newline-normalized)
- `expected_manifest.json` — canonical JSON of ExtractionManifest
- `expected_chapter_map.json` — ChapterBoundary list with offsets

Determinism tests MUST verify: same EPUB × N runs → identical `expected.txt`, `expected_manifest.json`, `expected_chapter_map.json`.

---

## 15. Governance / Root Hygiene Gate

### Baseline Definitions

| Baseline | Reference |
|----------|-----------|
| **Git Baseline** | Commit `ca1c36fabe80e6b9c3d761ba86b7c39fce43e863` (P0 Stage 2 Complete) |
| **Worktree Baseline** | `P0_STAGE3_PREFLIGHT` snapshot (captured before Stage 3 begins) |

Stage 3 acceptance compares:
```
POST_STAGE3_WORKTREE
        vs
PRE_STAGE3_WORKTREE (P0_STAGE3_PREFLIGHT)
```
NOT merely `git diff ca1c36fabe80e6b9c3d761ba86b7c39fce43e863` — pre-existing dirty worktree files must not be conflated with Stage 3 changes.

### Pre-Stage Check (mandatory)

```bash
# Verify validator supports --root-only before Stage 3 begins
python -m ntpe_validate --help | grep -- '--root-only'
# If unsupported, Stage 3 MUST use existing validator interface and existing
# project-layout audit tool rather than modifying the validator solely for Stage 3.

# Capture preflight ROOT ENTRY snapshot (repository root only, not full worktree)
Get-ChildItem -Force | Select-Object -ExpandProperty Name | Sort-Object | Set-Content artifacts/p0_productization/P0_STAGE3_PREFLIGHT_ROOT_ENTRIES.txt
```

**Allowed Root Items** (no additions):
> **Source of Truth**: The following governance documents are the sole authority for repository root structure, allowed root items, artifact placement, and directory ownership:
> - `docs/governance/repository/ROOT_POLICY.md`
> - `docs/governance/repository/REPOSITORY_STRUCTURE_SPEC.md`
> - `docs/governance/repository/DIRECTORY_OWNERSHIP.md`
> - `config/project_layout_policy.json`
>
> The list below is informational only and does not override the governance documents.

- Entry Points: `main.py`, `run.py` (if exist)
- Metadata: `.gitignore`, `.gitattributes`, `LICENSE`, `README.md`
- VCS: `.git/`
- Minimal Config: `pyproject.toml`, `requirements.txt`
- Directories: `docs/`, `src/`, `tools/`, `artifacts/`, `tests/`, `archive/`, `config/`, `.kilo/`

### Dirty Worktree Isolation

> **Do not modify, delete, move, rename, stage, commit, reset, restore, or clean any pre-existing dirty worktree item outside the explicit Stage 3 scope.**
>
> Any pre-existing dirty file accidentally modified by Stage 3 MUST be restored before acceptance, without altering its original content.

### Implementation Location

- All new code: `core/adapters/epub_extraction_boundary.py` (replace stub)
- Tests: `tests/unit/adapters/test_epub_extraction_boundary.py` (expand)
- Integration: `tests/integration/test_epub_extraction_e2e.py` (new)
- Fixtures: `tests/fixtures/epub/` (new, under `tests/`)

### Prohibited

- Any file/directory at repository root
- Modifications to `core/book_intake/`, `core/translation_runtime/`, `core/translation_release/`
- New dependencies not in `pyproject.toml` optional group `[epub-extraction]`

### Post-Stage Validation

```bash
python -m ntpe_validate              # ALL PASS
python -m compileall                 # 0 errors
git diff --check                     # PASS

# GATE A — Root Hygiene: Root Entry Set MUST remain identical
Get-ChildItem -Force | Select-Object -ExpandProperty Name | Sort-Object | Set-Content artifacts/p0_productization/P0_STAGE3_POSTFLIGHT_ROOT_ENTRIES.txt
Compare-Object `
    (Get-Content artifacts/p0_productization/P0_STAGE3_PREFLIGHT_ROOT_ENTRIES.txt) `
    (Get-Content artifacts/p0_productization/P0_STAGE3_POSTFLIGHT_ROOT_ENTRIES.txt)
# MUST produce NO DIFFERENCES (zero root entry changes)

# GATE B — Git Scope: Changed paths MUST be subset of approved Stage 3 scope (§16)
git status --short
git diff --name-only
git diff --cached --name-only
# ALL changed paths ⊆ approved scope list
```

> **Evidence Scope Clarification**: `P0_STAGE3_PREFLIGHT_ROOT_ENTRIES.txt` and `P0_STAGE3_POSTFLIGHT_ROOT_ENTRIES.txt` are **acceptance-only untracked evidence** — created during validation gate execution for comparison purposes only. They are NOT committed as part of Stage 3 deliverables (§16 commit scope). They reside in `artifacts/p0_productization/` and serve as audit trail for the root hygiene gate. GATE A comparison is performed at acceptance time; the files themselves are not source-controlled.

```bash
pytest tests/unit/adapters/test_epub_extraction_boundary.py -v  # All pass
pytest tests/integration/test_epub_extraction_e2e.py -v        # All pass
```

### Commit Scope Audit (Pre-Commit Gate)

Before any commit, verify every changed path belongs to approved Stage 3 scope:

```bash
git status --short
git diff --name-only
git diff --cached --name-only
```

> Every changed path MUST belong to the approved Stage 3 commit scope (§16).
> Any path outside scope → MUST NOT be committed.

---

## 16. Commit Scope

**Single Commit** (or minimal atomic commits) containing:

| File | Action |
|------|--------|
| `core/adapters/epub_extraction_boundary.py` | Replace stub with full implementation |
| `tests/unit/adapters/test_epub_extraction_boundary.py` | Expand contract tests → implementation tests |
| `tests/integration/test_epub_extraction_e2e.py` | New integration test |
| `tests/fixtures/epub/` | Test EPUB fixtures (minimal, valid, malformed) + golden outputs |
| `pyproject.toml` | Add optional dependency group `[epub-extraction]` → `ebooklib`, `lxml` (ONLY if not already available through existing approved dependency group) |
| `docs/governance/rm5/` (if needed) | Architecture decision record for EPUB input contract |

> `pyproject.toml` MAY be modified only if the required EPUB extraction dependency is not already available through an existing approved dependency group.
> No unrelated dependency changes are permitted.

**Commit Message Format**:
```
P0 Stage 3: Implement EpubExtractionBoundary (EPUB → TXT extraction)

- Implement EPUB 3.x/2.0.1 extraction with security-hardened ZIP handling
- Support nav/NCX/spine reading order, XHTML chapter extraction, resource manifest
- Integrate with CanonicalBookIntakeAdapter for intake pipeline
- Deterministic extraction: same EPUB → same text + manifest
- Add comprehensive unit + integration tests with fixture EPUBs + golden outputs
- Governance: zero root changes, ntpe_validate ALL PASS
```

---

## Review Checklist — 11 Hard Gates

Before implementation authorization, ALL gates MUST PASS. Any FAIL → Stage 3 does not enter implementation acceptance.

| Gate | Requirement | Evidence |
|------|-------------|----------|
| **1. Baseline** | Git baseline fixed to `ca1c36fabe80e6b9c3d761ba86b7c39fce43e863` | Spec header matches |
| **2. Architecture** | Zero architecture expansion — only `EpubExtractionBoundary` added | No new runtime/launcher/checkpoint/provider/prompt/chunking/delivery/UI/config/SoT |
| **3. Security** | All ZIP security violations → `blocked`, fail-closed, NEVER overridable | Path traversal, zip bomb, encryption, executable, duplicate paths, UNC, drive-letter, symlink, nested archive, oversize, malformed ZIP |
| **4. Network** | Zero network requests in extraction and all tests | Provider Requests = 0, Network Requests = 0; HTTP/HTTPS → `manual_review_required`, no fetch |
| **5. Determinism** | Same EPUB × N runs → identical `extracted_text`, `extracted_hash`, `chapter_map`, deterministic manifest fields | Golden fixtures verify exact match |
| **6. Intake** | EPUB extraction ONLY enters canonical intake via `CanonicalBookIntakeAdapter.ingest_extracted()` | No direct TranslationRuntime/Provider/Chunk/Resume/Delivery coupling |
| **7. Boundary** | Chapter offsets are Unicode code points, newline-normalized, no gaps/overlaps | `extracted_text[start:end]` exact; invariants verified in tests |
| **8. Golden Fixtures** | All key fixtures have `expected.txt`, `expected_manifest.json`, `expected_chapter_map.json` | Determinism tests verify byte-for-byte match |
| **9. Governance** | Root snapshot Before/After → ZERO new root files/directories | `diff PREFLIGHT POSTFLIGHT` = empty; dirty worktree isolated |
| **10. Git Scope** | Commit contains ONLY Stage 3 authorized files | `git status/diff/cached` paths ⊆ approved scope list (§16) |
| **11. Data Flow** | Extraction responsibility ends at `EpubExtractionResult`; no parallel pipeline | Canonical Data Flow diagram followed; adapter boundary respected |

---

**Next Step**: Upon specification approval, Kilo will implement the full `EpubExtractionBoundary` per this specification and execute the validation gate.
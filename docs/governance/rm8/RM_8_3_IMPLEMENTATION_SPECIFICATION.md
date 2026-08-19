# RM-8.3 Implementation Specification
## Output Polish & Delivery ??Minimal, Explicit, Backward-Compatible

---

### 1. SCOPE & PRINCIPLES

**Objective**: Add a post-translation polish stage and final validation gate after all chunks are translated and assembled. Produce a single deliverable artifact per novel with quality certificate and optional publication formats.

**Non-Objectives**:
- No chunking modification
- No re-translation
- No new provider/LLM calls
- No new quality models
- No RM-7/RM-8.1/RM-8.2 pipeline changes
- No re-assembly of translated chunks (input is already-assembled text)

| Principle | Decision |
|---|---|
| Polish | Reuse `runtime_formatter.py` functions + add paragraph-level normalization |
| Validation | Deterministic gate (PASS/FAIL) on full novel ??no LLM judge |
| TOC | Use RM-8.2 `scene_id`/`chapter_id` from chunk metadata only; no heuristic chapter title inference |
| Metadata | Inject title, author, translator, date, model, pipeline version, quality cert |
| Delivery Package | 3 core files (TXT, manifest, QC cert) + optional EPUB/PDF (P2, non-blocking) |
| Compatibility | Feature-gated (`quality_delivery_v83` default OFF); existing `translate_txt()` unchanged |
| Provider Cost | Zero additional requests |

---

### 2. ARCHITECTURE OVERVIEW

```
translate_txt() (lts/txt_translation_runtime.py)
    ??    ?ú‚? existing: chunk loop ??translated_chunks[] ??final assembly
    ??          (split_text, translation loop, QA, locked-dict, canonicalization)
    ??          ??assembled_text = "\n\n".join(translated_chunks).strip() + "\n"
    ??    ?î‚? [RM-8.3 EXTENSION ??feature-gated]
        if options.quality_delivery_v83:
            # Input: already-assembled text + chunk_records (metadata only)
            # Does NOT re-run split_text, translation loop, or any runtime stage
            delivery_result = run_delivery_pipeline(
                assembled_text=assembled_text,       # already assembled by existing pipeline
                translated_chunks=translated_chunks, # for TOC word-count only
                chunk_records=records,               # from runtime, contains context_state_metadata
                locked_dictionary=locked_dictionary,
                options=options,
                input_path=input_path,
                output_dir=output_dir,
            )
            # delivery_result: {status, output_path, manifest_path, qc_path, epub_path?, pdf_path?}
```

**New Module**: `core/translation_release/` (feature-gated, no import by runtime unless flag enabled)

---

### 3. DATA STRUCTURES

#### 3.1 Delivery Manifest (extends existing translation manifest)

```python
# core/translation_release/models.py

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass(frozen=True)
class DeliveryManifest:
    """Delivery package manifest ??extends translation manifest with delivery metadata."""
    # Core identification
    novel_id: str                          # input_path.stem
    generated_at: str                      # ISO timestamp
    pipeline_version: str                  # "NTPE_RM83_v1"

    # Source & translation config
    input_path: str
    output_path: str                       # primary TXT
    chunk_total: int
    chunk_size: int
    model: str
    speed: str
    quality_profile: str

    # RM-8.1 Literary Quality Aggregate
    literary_quality: dict                 # {hits, errors, warnings, passed, issue_codes}

    # RM-8.2 Cross-Chunk Context Aggregate
    context_continuity: dict               # {scene_count, chapter_count, scene_transitions: int}

    # Delivery QC Results
    qc_result: dict                        # {status: "PASS"/"FAIL", checks: {...}, score: float}

    # Output artifacts
    artifacts: dict                        # {"txt": path, "manifest": path, "qc_certificate": path, "epub"?: path, "pdf"?: path}

    # TOC (from RM-8.2 metadata)
    table_of_contents: list[dict]          # [{"chapter_id": "ch_1", "title": "Á¨?Á´?, "scene_count": 3, "start_chunk": 1, "end_chunk": 3}, ...]

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class QualityCertificate:
    """Quality certificate for delivery ??human-readable + machine-parseable."""
    novel_id: str
    issued_at: str
    pipeline_version: str

    # Overall verdict
    overall_status: str                    # "PASS" | "FAIL"
    overall_score: float                   # 0.0-100.0

    # Dimension scores
    literary_quality_score: float
    format_consistency_score: float
    term_lock_compliance_score: float
    completeness_score: float
    context_continuity_score: float

    # Detailed checks
    checks: dict                           # {"paragraph_structure": {...}, "punctuation_consistency": {...}, ...}

    # RM-8.1 traceability
    literary_quality_aggregate: dict

    # RM-8.2 traceability
    context_continuity_aggregate: dict

    def to_dict(self) -> dict: ...

@dataclass(frozen=True)
class DeliveryResult:
    """Return value from delivery pipeline ??fully immutable, constructed once."""
    status: str                            # "success" | "failed"
    output_path: str                       # polished TXT
    manifest_path: str                     # DeliveryManifest JSON
    qc_certificate_path: str               # QualityCertificate JSON
    epub_path: Optional[str] = None
    pdf_path: Optional[str] = None
    error: Optional[str] = None
```

#### 3.2 TOC Entry (from RM-8.2 metadata)

```python
# core/translation_release/models.py

@dataclass(frozen=True)
class TOCEntry:
    chapter_id: str
    chapter_title: str                     # e.g., "Á¨?Á´? or extracted from marker
    scene_count: int
    start_chunk_index: int                 # 1-based
    end_chunk_index: int
    scene_ids: list[str]
    word_count_estimate: int               # sum of chunk chars in range
```

---

### 4. POLISH PIPELINE (core/translation_release/polish.py)

#### 4.1 Function Signatures

```python
# core/translation_release/polish.py

from core.translation_runtime.runtime_formatter import (
    clean_provider_output,
    normalize_punctuation_for_zh_tw,
    normalize_taiwan_traditional,
)

def normalize_paragraphs(text: str) -> tuple[str, dict]:
    """
    Normalize paragraph structure across full novel.

    Returns: (polished_text, metrics_dict)
    metrics_dict = {
        "paragraphs_before": int,
        "paragraphs_after": int,
        "empty_paragraphs_removed": int,
        "excessive_breaks_consolidated": int,
        "whitespace_normalized": int,
    }
    """
    # 1. Split on double newline
    # 2. Remove empty paragraphs (only whitespace)
    # 3. Consolidate 3+ consecutive newlines ??2
    # 4. Ensure single trailing newline at EOF
    # 5. Normalize internal whitespace (tabs ??spaces, multiple spaces ??single)
    pass

def unify_quote_style(text: str) -> tuple[str, dict]:
    """
    Unify quotation marks to CJK corner brackets CONSERVATIVELY.

    Rules:
    - Only convert ASCII double quotes "..." that form clear quotation pairs
    - Only convert ASCII single quotes '...' that form clear quotation pairs
    - Do NOT convert apostrophes in contractions (don't, won't, it's) or possessives
    - Do NOT convert quotes that are clearly code, measurement, or non-dialogue
    - Preserve already-correct CJK quotes ??..????..??
    Returns: (polished_text, metrics_dict)
    metrics_dict = {
        "double_quotes_converted": int,
        "single_quotes_converted": int,
        "mixed_quotes_resolved": int,
        "skipped_apostrophes": int,
    }
    """
    # Conservative algorithm:
    # 1. Find balanced pairs of "..." not containing unpaired quotes
    # 2. Find balanced pairs of '...' not containing unpaired quotes
    # 3. Skip if content looks like code/measurement (contains {, }, =, :, digits+units)
    # 4. Skip if it's a contraction (n't, 's, 're, 've, 'll, 'd, 'm)
    pass

def polish_full_novel(
    text: str,
    *,
    taiwan_traditional_normalization: bool = True,
    enabled: bool = True,
) -> tuple[str, dict]:
    """
    Main polish entry point ??runs full pipeline on assembled novel.

    Pipeline order:
    1. clean_provider_output()          # remove preambles, normalize line endings
    2. normalize_paragraphs()           # paragraph structure
    3. unify_quote_style()              # quote consistency
    4. normalize_punctuation_for_zh_tw() # ASCII ??CJK punctuation
    5. normalize_taiwan_traditional()   # if enabled
    6. clean_provider_output()          # final cleanup

    Returns: (final_text, aggregate_metrics)
    aggregate_metrics = {
        "paragraphs": {...},
        "quotes": {...},
        "punctuation": {...},
        "traditional_normalization": {...},
        "total_changes": int,
    }
    """
    pass
```

#### 4.2 Integration with Existing Formatters

```python
# Reuses (no duplication):
from core.translation_runtime.runtime_formatter import (
    clean_provider_output,           # step 1, 6
    normalize_punctuation_for_zh_tw, # step 4
    normalize_taiwan_traditional,    # step 5
)

# New (paragraph-level, full-novel scope):
def normalize_paragraphs(text: str) -> tuple[str, dict]: ...
def unify_quote_style(text: str) -> tuple[str, dict]: ...
```

---

### 5. VALIDATION GATE (core/translation_release/validator.py)

#### 5.1 Function Signatures

```python
# core/translation_release/validator.py

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    score: float                     # 0.0-100.0
    details: dict                    # check-specific details
    severity: str                    # "critical" | "major" | "minor" | "info"

@dataclass(frozen=True)
class ValidationResult:
    overall_passed: bool
    overall_score: float             # weighted average
    checks: list[ValidationCheck]
    failed_critical: list[str]       # names of failed critical checks
    failed_major: list[str]

def validate_final_novel(
    text: str,
    *,
    locked_dictionary: dict[str, str],
    chunk_records: list[dict],       # from runtime, contains context_state_metadata
    literary_quality_aggregate: dict, # from manifest
    options: TxtTranslationOptions,
) -> ValidationResult:
    """
    Deterministic validation gate ??no LLM, no provider calls.

    Checks (all deterministic):
    1. paragraph_structure          ??critical
       - No empty paragraphs
       - No 3+ consecutive newlines
       - Paragraph count > 0

    2. punctuation_consistency      ??major
       - CJK punctuation ratio > 95%
       - Quote style unified (corner brackets)

    3. korean_residue_global        ??critical
       - Total Korean chars < options.max_korean_chars * chunk_total * 0.5

    4. locked_term_compliance       ??critical
       - All locked terms present in final text (global check)
       - No locked aliases present

5. length_ratio_global          ??major
       - Total translated / total source ??[options.min_length_ratio, 2.0]
       - **Source length MUST come from existing chunk_records**: each record.source.char_count (from prompt package) or record.metadata.source.char_count. If unavailable, check is marked "unverifiable" and excluded from scoring.

    6. locked_term_compliance       ??major (downgraded from critical)
       - Only validate locked terms that **actually appear in source chunks** (matched_locked_terms from runtime)
       - No FAIL for glossary entries not present in this novel
       - Check: all matched locked terms present in final text; no locked aliases present

    Weighted scoring:
    - critical: weight 3.0
    - major: weight 2.0
    - minor: weight 1.0
    - info: weight 0.5

    PASS threshold: overall_score >= 70.0 AND no failed critical checks
    """
    pass
```

#### 5.2 Check Implementation Details

```python
# Each check returns ValidationCheck

def _check_paragraph_structure(text: str) -> ValidationCheck:
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    empty_count = text.count("\n\n\n")
    excessive = sum(1 for p in text.split("\n") if not p.strip())
    return ValidationCheck(
        name="paragraph_structure",
        passed=(len(paragraphs) > 0 and empty_count == 0),
        score=100.0 if empty_count == 0 else max(0.0, 100.0 - empty_count * 10),
        details={"paragraphs": len(paragraphs), "empty_removed": empty_count, "excessive_newlines": excessive},
        severity="critical",
    )

def _check_korean_residue(text: str, max_allowed: int) -> ValidationCheck:
    import re
    korean_count = len(re.findall(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]", text))
    return ValidationCheck(
        name="korean_residue_global",
        passed=korean_count <= max_allowed,
        score=100.0 if korean_count <= max_allowed else max(0.0, 100.0 - (korean_count - max_allowed) * 5),
        details={"korean_chars": korean_count, "max_allowed": max_allowed},
        severity="critical",
    )

def _check_locked_terms(text: str, locked_dict: dict, matched_terms: dict) -> ValidationCheck:
    """
    Only validate locked terms that were actually matched in source chunks.
    matched_terms = {src: target for src, target in locked_dict.items() if src in source_text}
    """
    from lts.txt_translation_runtime import build_translation_alias_map
    missing = [t for t in matched_terms.values() if t and t not in text]
    aliases = build_translation_alias_map(matched_terms)
    alias_hits = [a for a in aliases if a in text]
    return ValidationCheck(
        name="locked_term_compliance",
        passed=(len(missing) == 0 and len(alias_hits) == 0),
        score=100.0 if len(missing) == 0 and len(alias_hits) == 0 else max(0.0, 100.0 - len(missing) * 10 - len(alias_hits) * 5),
        details={"missing_terms": missing, "alias_violations": alias_hits, "validated_terms": list(matched_terms.values())},
        severity="major",  # downgraded from critical
    )

def _check_length_ratio(text: str, chunk_records: list[dict], min_ratio: float) -> ValidationCheck:
    """
    Compute length ratio from existing chunk_records source metadata.
    Each record should have: record.get("source", {}).get("char_count") or
    record.get("metadata", {}).get("source", {}).get("char_count")
    """
    source_total = 0
    verifiable_chunks = 0
    for rec in chunk_records:
        src = rec.get("source") or rec.get("metadata", {}).get("source")
        if isinstance(src, dict):
            char_count = src.get("char_count")
            if isinstance(char_count, int) and char_count > 0:
                source_total += char_count
                verifiable_chunks += 1

    if verifiable_chunks == 0:
        return ValidationCheck(
            name="length_ratio_global",
            passed=True,  # unverifiable ??neutral
            score=100.0,
            details={"verifiable": False, "reason": "no source char_count in chunk_records"},
            severity="info",  # info when unverifiable
        )

    translated_total = len(text.replace("\n", "").replace(" ", ""))
    ratio = translated_total / source_total if source_total > 0 else 0
    passed = min_ratio <= ratio <= 2.0
    return ValidationCheck(
        name="length_ratio_global",
        passed=passed,
        score=100.0 if passed else max(0.0, 100.0 - abs(ratio - min_ratio) * 50),
        details={"translated_chars": translated_total, "source_chars": source_total, "ratio": round(ratio, 3), "min_ratio": min_ratio, "verifiable_chunks": verifiable_chunks},
        severity="major",
    )
```

---

### 6. METADATA INJECTION (core/translation_release/metadata.py)

#### 6.1 Function Signatures

```python
# core/translation_release/metadata.py

from core.translation_release.models import DeliveryManifest, QualityCertificate, TOCEntry
from typing import Optional

def build_toc_from_chunk_records(
    chunk_records: list[dict],
    translated_chunks: list[str],
) -> list[TOCEntry]:
    """
    Build TOC from RM-8.2 context_state_metadata in chunk records.

    Each record.metadata.context_state contains:
    - scene_id, scene_version, chapter_id
    - boundary.type (scene_transition, chapter_transition, same_scene)

    Algorithm:
    1. Iterate records in order
    2. Detect chapter transitions (boundary.type == "chapter_transition" or new chapter_id)
    3. Group chunks by chapter_id
    4. Count scenes per chapter (unique scene_id)
    5. Estimate word count per chapter (sum of chunk lengths)
    6. **Chapter title**: ONLY from explicit marker in first chunk of chapter
       - Scan chunk text for patterns: `Á¨¨NÁ´†`, `Á¨?N Á´†`, `Chapter N`, `CHAPTER N`
       - If found: use as title (e.g., "Á¨?Á´??ùÈ?")
       - If NOT found: deterministic fallback "Á¨¨NÁ´? (no heuristic inference)
    """
    pass

def inject_metadata_into_text(
    text: str,
    *,
    title: str,
    author: str = "?™Áü•‰ΩúËÄ?,
    translator: str = "NTPE Translation Engine",
    date: str,                    # ISO date
    model: str,
    pipeline_version: str,
    toc: list[TOCEntry],
    quality_cert_summary: str,    # one-line summary
) -> str:
    """
    Inject metadata as structured header + TOC at start of novel.

    Format:
    ```
    ?êÊõ∏Ë™åË?Ë®ä„Ä?    ?∏Â?Ôºö{title}
    ‰ΩúËÄÖÔ?{author}
    Ë≠ØËÄÖÔ?{translator}
    ÁøªË≠Ø?•Ê?Ôºö{date}
    ÁøªË≠ØÊ®°Â?Ôºö{model}
    ÁÆ°Á??àÊú¨Ôºö{pipeline_version}
    ?ÅË≥™?Ä?ãÔ?{quality_cert_summary}

    ?êÁõÆ?Ñ„Ä?    Á¨?Á´?Á´†Á?Ê®ôÈ? .......... 3 ?¥ÊôØ (Chunk 1-3)
    Á¨?Á´?Á´†Á?Ê®ôÈ? .......... 2 ?¥ÊôØ (Chunk 4-5)
    ...

    ?Ä?Ä?Ä
    {original_novel_text}
    ```

    Returns: text with metadata header prepended
    """
    pass

def generate_delivery_manifest(
    *,
    novel_id: str,
    input_path: str,
    output_path: str,
    chunk_records: list[dict],
    translated_chunks: list[str],
    locked_dictionary: dict,
    options: TxtTranslationOptions,
    literary_quality_aggregate: dict,
    qc_result: ValidationResult,
    toc: list[TOCEntry],
    artifact_paths: dict,
) -> DeliveryManifest:
    """Build complete DeliveryManifest from all pipeline data."""
    pass

def generate_quality_certificate(
    *,
    novel_id: str,
    qc_result: ValidationResult,
    literary_quality_aggregate: dict,
    context_continuity_aggregate: dict,
) -> QualityCertificate:
    """Build QualityCertificate from validation results."""
    pass
```

---

### 7. DELIVERY PACKAGE (core/translation_release/package.py)

#### 7.1 Function Signatures

```python
# core/translation_release/package.py

from core.translation_release.models import DeliveryResult
from pathlib import Path

def write_delivery_package(
    *,
    polished_text: str,
    delivery_manifest: DeliveryManifest,
    quality_certificate: QualityCertificate,
    output_dir: Path,
    novel_id: str,
    formats: tuple[str, ...] = ("txt",),  # "txt", "epub", "pdf"
) -> DeliveryResult:
    """
    Write all delivery artifacts to output_dir.

    Core artifacts (always):
    - {novel_id}_zh.txt                    # polished novel with metadata header
    - {novel_id}_delivery_manifest.json    # DeliveryManifest
    - {novel_id}_quality_certificate.json  # QualityCertificate

    Optional artifacts (if format in formats):
    - {novel_id}.epub                      # via epub_exporter
    - {novel_id}.pdf                       # via pdf_exporter

    Returns: DeliveryResult with all paths
    """
    pass

def write_txt_delivery(
    polished_text: str,
    output_dir: Path,
    novel_id: str,
) -> str:
    """Write primary TXT artifact."""
    path = output_dir / f"{novel_id}_zh.txt"
    path.write_text(polished_text, encoding="utf-8")
    return str(path)

def write_json_delivery(
    obj: object,
    output_dir: Path,
    novel_id: str,
    suffix: str,
) -> str:
    """Write JSON artifact (manifest or certificate)."""
    import json
    path = output_dir / f"{novel_id}_{suffix}.json"
    path.write_text(json.dumps(obj.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
```

---

### 8. EXPORTERS (Optional ??core/translation_release/exporters/)

#### 8.1 Base Interface

```python
# core/translation_release/exporters/base.py

from abc import ABC, abstractmethod
from core.translation_release.models import DeliveryManifest, TOCEntry
from pathlib import Path

class BaseExporter(ABC):
    @property
    @abstractmethod
    def format_name(self) -> str: ...

    @property
    @abstractmethod
    def file_extension(self) -> str: ...

    @abstractmethod
    def export(
        self,
        *,
        polished_text: str,
        manifest: DeliveryManifest,
        toc: list[TOCEntry],
        output_path: Path,
    ) -> bool:
        """Returns True on success, False on failure."""
        pass
```

#### 8.2 EPUB Exporter (Minimal Scope)

```python
# core/translation_release/exporters/epub_exporter.py

class EpubExporter(BaseExporter):
    format_name = "epub"
    file_extension = ".epub"

    def export(self, *, polished_text, manifest, toc, output_path) -> bool:
        """
        Minimal EPUB 3.0 generation:
        - Uses polished_text as single chapter or splits by TOC
        - Embeds metadata from manifest
        - Includes TOC navigation
        - No CSS styling beyond basic readability
        - Dependencies: ebooklib (optional, graceful fallback)
        """
        try:
            from ebooklib import epub
        except ImportError:
            return False  # graceful: format unavailable

        book = epub.EpubBook()
        book.set_identifier(manifest.novel_id)
        book.set_title(manifest.table_of_contents[0]["chapter_title"] if manifest.table_of_contents else manifest.novel_id)
        book.set_language("zh-TW")
        book.add_author(manifest.metadata.get("author", "?™Áü•‰ΩúËÄ?))

        # Add metadata
        book.add_metadata("DC", "translator", "NTPE Translation Engine")
        book.add_metadata("DC", "date", manifest.generated_at)
        book.add_metadata("DC", "pipeline", manifest.pipeline_version)

        # Create chapters from TOC
        # Split polished_text by TOC boundaries or use as single chapter
        # ...

        epub.write_epub(str(output_path), book)
        return True
```

#### 8.3 PDF Exporter (Minimal Scope)

```python
# core/translation_release/exporters/pdf_exporter.py

class PdfExporter(BaseExporter):
    format_name = "pdf"
    file_extension = ".pdf"

    def export(self, *, polished_text, manifest, toc, output_path) -> bool:
        """
        Minimal PDF generation:
        - Uses polished_text with metadata header
        - Basic pagination, TOC bookmarks
        - No advanced typography
        - Dependencies: reportlab or weasyprint (optional, graceful fallback)
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            return False

        # Register a CJK font (requires font file ??graceful if missing)
        # Build document with TOC bookmarks
        # ...
        return True
```

---

### 9. DELIVERY PIPELINE ORCHESTRATOR (core/translation_release/delivery_pipeline.py)

#### 9.1 Main Entry Point

```python
# core/translation_release/delivery_pipeline.py

from core.translation_release.models import DeliveryResult
from core.translation_release.polish import polish_full_novel
from core.translation_release.validator import validate_final_novel, ValidationResult
from core.translation_release.metadata import (
    build_toc_from_chunk_records,
    inject_metadata_into_text,
    generate_delivery_manifest,
    generate_quality_certificate,
)
from core.translation_release.package import write_delivery_package
from core.translation_release.exporters import EpubExporter, PdfExporter
from lts.txt_translation_runtime import TxtTranslationOptions
from core.translation_naturalness import canonicalize_novel_chinese, apply_literary_collocation_guard
from pathlib import Path

def run_delivery_pipeline(
    *,
    assembled_text: str,               # already assembled by existing pipeline
    translated_chunks: list[str],      # for TOC word-count only
    chunk_records: list[dict],
    locked_dictionary: dict[str, str],
    options: TxtTranslationOptions,
    input_path: Path,
    output_dir: Path,
) -> DeliveryResult:
    """
    Main delivery pipeline ??called from txt_translation_runtime.py after final assembly.

    Feature-gated by: options.quality_delivery_v83
    Input: assembled_text (already finalized by existing pipeline), NOT re-assembled here.
    """
    novel_id = input_path.stem

    # 1. FINAL CANONICALIZATION (reuse existing) ??on already-assembled text
    assembled_text = canonicalize_novel_chinese(assembled_text).text
    assembled_text = apply_literary_collocation_guard(assembled_text).text

    # 2. POLISH (NEW ??full novel scope)
    polished_text, polish_metrics = polish_full_novel(
        assembled_text,
        taiwan_traditional_normalization=options.taiwan_traditional_normalization,
        enabled=options.output_formatter_enabled,
    )

    # 3. VALIDATION GATE (NEW)
    literary_quality_aggregate = _aggregate_literary_quality(chunk_records)
    context_continuity_aggregate = _aggregate_context_continuity(chunk_records)

    # Compute matched locked terms from runtime (already available in chunk_records or options)
    matched_terms = _compute_matched_locked_terms(chunk_records, locked_dictionary)

    qc_result = validate_final_novel(
        text=polished_text,
        locked_dictionary=locked_dictionary,
        chunk_records=chunk_records,
        literary_quality_aggregate=literary_quality_aggregate,
        options=options,
        matched_terms=matched_terms,  # NEW: only validate terms actually in source
    )

    if not qc_result.overall_passed:
        return DeliveryResult(
            status="failed",
            output_path="",
            manifest_path="",
            qc_certificate_path="",
            error=f"Quality gate FAILED: score={qc_result.overall_score:.1f}, critical_failures={qc_result.failed_critical}",
        )

    # 4. METADATA & TOC (NEW ??consumes RM-8.2 metadata)
    toc = build_toc_from_chunk_records(chunk_records, translated_chunks)
    quality_summary = f"PASS (score={qc_result.overall_score:.1f})"

    final_text = inject_metadata_into_text(
        polished_text,
        title=novel_id,
        date=options.completed_at if hasattr(options, "completed_at") else "",
        model=options.model,
        pipeline_version="NTPE_RM83_v1",
        toc=toc,
        quality_cert_summary=quality_summary,
    )

    # 5. GENERATE ARTIFACTS
    delivery_manifest = generate_delivery_manifest(
        novel_id=novel_id,
        input_path=str(input_path),
        output_path="",  # filled after write
        chunk_records=chunk_records,
        translated_chunks=translated_chunks,
        locked_dictionary=locked_dictionary,
        options=options,
        literary_quality_aggregate=literary_quality_aggregate,
        qc_result=qc_result,
        toc=toc,
        artifact_paths={},  # filled after write
    )

    quality_certificate = generate_quality_certificate(
        novel_id=novel_id,
        qc_result=qc_result,
        literary_quality_aggregate=literary_quality_aggregate,
        context_continuity_aggregate=context_continuity_aggregate,
    )

    # 6. WRITE PACKAGE + EXPORTERS (collect all paths BEFORE constructing DeliveryResult)
    formats = getattr(options, "quality_delivery_formats_v83", ("txt",))

    # Write core artifacts
    txt_path = write_txt_delivery(final_text, output_dir, novel_id)
    manifest_path = write_json_delivery(delivery_manifest, output_dir, novel_id, "delivery_manifest")
    qc_path = write_json_delivery(quality_certificate, output_dir, novel_id, "quality_certificate")

    epub_path = None
    pdf_path = None

    # Optional exporters (non-blocking)
    if "epub" in formats:
        exporter = EpubExporter()
        epub_candidate = output_dir / f"{novel_id}.epub"
        if exporter.export(polished_text=final_text, manifest=delivery_manifest, toc=toc, output_path=epub_candidate):
            epub_path = str(epub_candidate)

    if "pdf" in formats:
        exporter = PdfExporter()
        pdf_candidate = output_dir / f"{novel_id}.pdf"
        if exporter.export(polished_text=final_text, manifest=delivery_manifest, toc=toc, output_path=pdf_candidate):
            pdf_path = str(pdf_candidate)

    # 7. CONSTRUCT IMMUTABLE DeliveryResult ONCE with all paths
    return DeliveryResult(
        status="success",
        output_path=txt_path,
        manifest_path=manifest_path,
        qc_certificate_path=qc_path,
        epub_path=epub_path,
        pdf_path=pdf_path,
        error=None,
    )

def _compute_matched_locked_terms(chunk_records: list[dict], locked_dictionary: dict[str, str]) -> dict[str, str]:
    """
    Compute locked terms that were actually matched in source chunks.
    Uses existing runtime logic: collect from chunk source metadata or prompt packages.
    """
    # In practice, this comes from runtime's matched_locked_dictionary() or
    # collect_matched_locked_terms() which are already computed during translation.
    # For delivery pipeline, we can reconstruct from chunk_records source metadata.
    matched = {}
    for rec in chunk_records:
        src = rec.get("source") or rec.get("metadata", {}).get("source")
        if isinstance(src, dict):
            chunk_text = src.get("chunk_text", "")
            for k, v in locked_dictionary.items():
                if k and k in chunk_text and v:
                    matched[k] = v
    return matched

def _aggregate_literary_quality(chunk_records: list[dict]) -> dict:
    """Aggregate literary_quality_* metrics from all chunk records."""
    hits = errors = warnings = 0
    passed = True
    issue_codes = []
    for rec in chunk_records:
        qa = rec.get("qa") if isinstance(rec.get("qa"), dict) else {}
        metrics = qa.get("metrics") if isinstance(qa.get("metrics"), dict) else {}
        if metrics:
            hits += int(metrics.get("literary_quality_hits", 0))
            errors += int(metrics.get("literary_quality_errors", 0))
            warnings += int(metrics.get("literary_quality_warnings", 0))
            if not metrics.get("literary_quality_passed", True):
                passed = False
            issue_codes.extend(metrics.get("literary_quality_issue_codes", []))
    return {
        "hits": hits,
        "errors": errors,
        "warnings": warnings,
        "passed": passed,
        "issue_codes": list(dict.fromkeys(issue_codes)),
    }

def _aggregate_context_continuity(chunk_records: list[dict]) -> dict:
    """Aggregate scene/chapter info from RM-8.2 context_state_metadata."""
    scenes = set()
    chapters = set()
    scene_transitions = 0
    prev_scene = None
    for rec in chunk_records:
        ctx = rec.get("metadata", {}).get("context_state")
        if ctx:
            scenes.add(ctx.get("scene_id"))
            chapters.add(ctx.get("chapter_id"))
            if prev_scene and ctx.get("scene_id") != prev_scene:
                scene_transitions += 1
            prev_scene = ctx.get("scene_id")
    return {
        "scene_count": len(scenes),
        "chapter_count": len(chapters),
        "scene_transitions": scene_transitions,
    }
```

---

### 10. INTEGRATION POINT (lts/txt_translation_runtime.py)

#### 10.1 Feature Flag Addition

```python
# In TxtTranslationOptions (lts/txt_translation_runtime.py:94-143)

@dataclass(frozen=True)
class TxtTranslationOptions:
    # ... existing fields ...

    # RM-8.3 Delivery
    quality_delivery_v83: bool = False              # Default OFF
    quality_delivery_formats_v83: tuple[str, ...] = ("txt",)  # "epub", "pdf" optional
```

#### 10.2 Integration in translate_txt()

```python
# In translate_txt() ??after final assembly (around line 2380-2449)

# ... existing final assembly ...
final_output = output_dir / f"{input_path.stem}{DEFAULT_OUTPUT_SUFFIX}.txt"
if not options.dry_run and any(translated_chunks):
    final_text = "\n\n".join(translated_chunks).strip() + "\n"
    if options.strict_lock_terms and locked_dictionary:
        final_text = apply_locked_dictionary(final_text, locked_dictionary)
    save_text(final_output, final_text)
    if character_memory_path:
        update_character_memory(character_memory_path, matched_terms_for_memory)

# [RM-8.3 EXTENSION ??feature-gated]
if getattr(options, "quality_delivery_v83", False) and not options.dry_run:
    from core.translation_release.delivery_pipeline import run_delivery_pipeline
    delivery_result = run_delivery_pipeline(
        assembled_text=final_text,              # already assembled by existing pipeline
        translated_chunks=translated_chunks,    # for TOC word-count only
        chunk_records=records,                  # contains context_state_metadata from RM-8.2
        locked_dictionary=locked_dictionary,
        options=options,
        input_path=input_path,
        output_dir=output_dir,
    )
    if delivery_result.status == "success":
        # Delivery output includes metadata header; existing final_output kept as-is
        pass
    else:
        emit_progress(f"Delivery pipeline failed: {delivery_result.error}", options=options)

# ... existing manifest generation ...
```

---

### 11. ACCEPTANCE TESTS

#### 11.2 Acceptance Tests

```python
# tests/acceptance/rm8_delivery_test.py

import pytest
from pathlib import Path
from core.translation_release.delivery_pipeline import run_delivery_pipeline
from core.translation_release.polish import polish_full_novel
from core.translation_release.validator import validate_final_novel
from core.translation_release.metadata import build_toc_from_chunk_records
from lts.txt_translation_runtime import TxtTranslationOptions

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "rm8_delivery"

@pytest.fixture
def sample_chunks():
    """3 chunks with RM-8.2 metadata simulating scene/chapter transitions."""
    return [
        "Á¨¨‰?ÊÆµÂÖßÂÆπ„ÄÇ\n\n?ôÊòØ?¥ÊôØ‰∏Ä??,
        "***\n\nÁ¨¨‰?ÊÆµÂÖßÂÆπ„ÄÇ\n\n?¥ÊôØ‰∫åÈ?Âßã„Ä?,
        "Á¨?Á´†\n\nÁ¨¨‰?ÊÆµÂÖßÂÆπ„ÄÇ\n\n?∞Á?ÁØÄ??,
    ]

@pytest.fixture
def sample_records():
    """Chunk records with context_state_metadata (RM-8.2 format) and source metadata."""
    return [
        {"source": {"char_count": 50, "chunk_text": "Á¨¨‰?ÊÆµÂÖßÂÆπ„ÄÇ\n\n?ôÊòØ?¥ÊôØ‰∏Ä??}, "metadata": {"context_state": {"scene_id": "Oh, I see the issue. The edits are failing because I'm using the old content.those", "chapter_id": "chapter_1", "boundary": {"type": "same_scene"}}}},
        {"source": {"char_count": 45, "chunk_text": "Á¨¨‰?ÊÆµÂÖßÂÆπ„ÄÇ\n\n?¥ÊôØ‰∫åÈ?Âßã„Ä?}, "metadata": {"context_state": {"scene_id": "scene_2", "chapter_id": "chapter_1", "boundary": {"type": "scene_transition"}}}},
        {"source": {"char_count": 48, "chunk_text": "Á¨?Á´†\n\nÁ¨¨‰?ÊÆµÂÖßÂÆπ„ÄÇ\n\n?∞Á?ÁØÄ??}, "metadata": {"context_state": {"scene_id": "scene_3", "chapter_id": "chapter_2", "boundary": {"type": "chapter_transition"}}}},
    ]

def test_polish_normalizes_paragraphs():
    text = "ÊÆµËêΩ‰∏Ä?Ç\n\n\n\nÊÆµËêΩ‰∫å„ÄÇ\n\n\n\n\nÊÆµËêΩ‰∏â„Ä?
    polished, metrics = polish_full_novel(text, taiwan_traditional_normalization=False)
    assert metrics["paragraphs"]["empty_paragraphs_removed"] >= 2
    assert polished.count("\n\n\n") == 0

def test_polish_unifies_quotes_conservative():
    # Only clear quotation pairs converted; apostrophes preserved
    text = '‰ªñË™™Ôºö„Äå‰?Â•Ω„Äç„ÄÇ\nÂ•πË™™Ôº?‰Ω†Â•Ω"?Ç\n‰∏çË?‰∏çË? don\'t worry.'
    polished, metrics = polish_full_novel(text, taiwan_traditional_normalization=False)
    assert "?å‰?Â•Ω„Ä? in polished
    assert "?é‰?Â•Ω„Ä? in polished
    assert "don't" in polished  # apostrophe preserved
    assert metrics["quotes"]["skipped_apostrophes"] >= 1

def test_validator_passes_clean_text(sample_chunks, sample_records):
    options = TxtTranslationOptions(
        input_path=Path("test.txt"),
        output_dir=Path("out"),
        max_korean_chars=2,
        min_length_ratio=0.1,
        strict_lock_terms=True,
    )
    locked_dict = {"‰∏ªË?": "‰∏ªË?"}
    matched_terms = {"‰∏ªË?": "‰∏ªË?"}  # only terms actually in source
    text = "\n\n".join(sample_chunks)
    result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms)
    assert result.overall_passed is True
    assert result.overall_score >= 70.0

def test_validator_fails_korean_residue(sample_chunks, sample_records):
    options = TxtTranslationOptions(
        input_path=Path("test.txt"),
        output_dir=Path("out"),
        max_korean_chars=0,
        min_length_ratio=0.1,
        strict_lock_terms=True,
    )
    text = "?àÎ??òÏÑ∏?î\n\n" + "\n\n".join(sample_chunks)  # Korean residue
    locked_dict = {}
    matched_terms = {}
    result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms)
    assert result.overall_passed is False
    assert "korean_residue_global" in result.failed_critical

def test_validator_locked_terms_only_validates_matched():
    """Glossary entries not in source should not cause FAIL."""
    options = TxtTranslationOptions(
        input_path=Path("test.txt"),
        output_dir=Path("out"),
        max_korean_chars=2,
        min_length_ratio=0.1,
        strict_lock_terms=True,
    )
    locked_dict = {"‰∏ªË?": "‰∏ªË?", "?™Âá∫?æË???: "?™Âá∫?æË???}  # second term not in source
    matched_terms = {"‰∏ªË?": "‰∏ªË?"}  # only validated term
    text = "‰∏ªË??∫Áèæ‰∫Ü„Ä?  # only ‰∏ªË? appears
    records = [{"source": {"char_count": 10, "chunk_text": "‰∏ªË??∫Áèæ‰∫Ü„Ä?}, "metadata": {"context_state": {"scene_id": "scene_1", "chapter_id": "chapter_1", "boundary": {"type": "same_scene"}}}}]
    result = validate_final_novel(text, locked_dict, records, {"passed": True, "errors": 0}, options, matched_terms)
    assert result.overall_passed is True  # should PASS, ?™Âá∫?æË???not validated

def test_validator_length_ratio_from_source_metadata(sample_chunks, sample_records):
    """Length ratio uses source char_count from chunk_records."""
    options = TxtTranslationOptions(
        input_path=Path("test.txt"),
        output_dir=Path("out"),
        max_korean_chars=2,
        min_length_ratio=0.5,
        strict_lock_terms=True,
    )
    locked_dict = {}
    matched_terms = {}
    text = "\n\n".join(sample_chunks)
    result = validate_final_novel(text, locked_dict, sample_records, {"passed": True, "errors": 0}, options, matched_terms)
    # source_total = 50+45+48 = 143, translated ??40 chars ??ratio ~0.28 < 0.5 ??should fail major
    check = next(c for c in result.checks if c.name == "length_ratio_global")
    assert check.details["verifiable"] is True
    assert check.details["verifiable_chunks"] == 3

def test_toc_generation_deterministic_title(sample_chunks, sample_records):
    toc = build_toc_from_chunk_records(sample_records, sample_chunks)
    assert len(toc) == 2
    assert toc[0].chapter_id == "chapter_1"
    assert toc[0].scene_count == 2
    assert toc[1].chapter_id == "chapter_2"
    assert toc[1].scene_count == 1
    # Chapter 2 has explicit marker "Á¨?Á´?
    assert "Á¨?Á´? in toc[1].chapter_title
    # Chapter 1 has no explicit marker in first chunk ??fallback "Á¨?Á´?
    assert toc[0].chapter_title == "Á¨?Á´?

def test_delivery_pipeline_integration(sample_chunks, sample_records, tmp_path):
    options = TxtTranslationOptions(
        input_path=tmp_path / "novel.txt",
        output_dir=tmp_path / "out",
        quality_delivery_v83=True,
        quality_delivery_formats_v83=("txt",),
        strict_lock_terms=True,
        max_korean_chars=2,
        min_length_ratio=0.1,
    )
    locked_dict = {"‰∏ªË?": "‰∏ªË?"}
    assembled_text = "\n\n".join(sample_chunks).strip() + "\n"

    result = run_delivery_pipeline(
        assembled_text=assembled_text,
        translated_chunks=sample_chunks,
        chunk_records=sample_records,
        locked_dictionary=locked_dict,
        options=options,
        input_path=options.input_path,
        output_dir=options.output_dir,
    )

    assert result.status == "success"
    assert Path(result.output_path).exists()
    assert Path(result.manifest_path).exists()
    assert Path(result.qc_certificate_path).exists()
    # EPUB/PDF not requested ??None
    assert result.epub_path is None
    assert result.pdf_path is None

    # Verify TXT has metadata header
    content = Path(result.output_path).read_text(encoding="utf-8")
    assert "?êÊõ∏Ë™åË?Ë®ä„Ä? in content
    assert "?êÁõÆ?Ñ„Ä? in content
    assert "Á¨?Á´? in content
    assert "Á¨?Á´? in content
```

#### 11.3 Golden Master Test

```python
# tests/acceptance/rm8_delivery_test.py (continued)

def test_delivery_deterministic(tmp_path):
    """Two runs with same input produce identical delivery artifacts (except timestamps)."""
    options = TxtTranslationOptions(
        input_path=tmp_path / "novel.txt",
        output_dir=tmp_path / "out1",
        quality_delivery_v83=True,
        quality_delivery_formats_v83=("txt",),
        strict_lock_terms=True,
    )
    chunks = ["ÊÆµËêΩ‰∏Ä?Ç\n\nÊÆµËêΩ‰∫å„Ä?, "ÊÆµËêΩ‰∏â„ÄÇ\n\nÊÆµËêΩ?õ„Ä?]
    records = [
        {"source": {"char_count": 20, "chunk_text": "ÊÆµËêΩ‰∏Ä?Ç\n\nÊÆµËêΩ‰∫å„Ä?}, "metadata": {"context_state": {"scene_id": "scene_1", "chapter_id": "chapter_1", "boundary": {"type": "same_scene"}}}},
        {"source": {"char_count": 20, "chunk_text": "ÊÆµËêΩ‰∏â„ÄÇ\n\nÊÆµËêΩ?õ„Ä?}, "metadata": {"context_state": {"scene_id": "scene_1", "chapter_id": "chapter_1", "boundary": {"type": "same_scene"}}}},
    ]
    locked_dict = {}
    assembled_text = "\n\n".join(chunks).strip() + "\n"

    result1 = run_delivery_pipeline(assembled_text, chunks, records, locked_dict, options, options.input_path, options.output_dir)
    result2 = run_delivery_pipeline(assembled_text, chunks, records, locked_dict, options, options.input_path, tmp_path / "out2")

    # Compare TXT content (excluding timestamps)
    txt1 = Path(result1.output_path).read_text(encoding="utf-8")
    txt2 = Path(result2.output_path).read_text(encoding="utf-8")

    # Normalize timestamps
    import re
    txt1_norm = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', 'TIMESTAMP', txt1)
    txt2_norm = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', 'TIMESTAMP', txt2)

    assert txt1_norm == txt2_norm
```

#### 11.2 Golden Master Test

```python
# tests/acceptance/rm8_delivery_test.py (continued)

def test_delivery_deterministic(tmp_path):
    """Two runs with same input produce identical delivery artifacts (except timestamps)."""
    options = TxtTranslationOptions(
        input_path=tmp_path / "novel.txt",
        output_dir=tmp_path / "out1",
        quality_delivery_v83=True,
        quality_delivery_formats_v83=("txt",),
        strict_lock_terms=True,
    )
    chunks = ["ÊÆµËêΩ‰∏Ä?Ç\n\nÊÆµËêΩ‰∫å„Ä?, "ÊÆµËêΩ‰∏â„ÄÇ\n\nÊÆµËêΩ?õ„Ä?]
    records = [
        {"metadata": {"context_state": {"scene_id": "scene_1", "chapter_id": "chapter_1", "boundary": {"type": "same_scene"}}}},
        {"metadata": {"context_state": {"scene_id": "scene_1", "chapter_id": "chapter_1", "boundary": {"type": "same_scene"}}}},
    ]
    locked_dict = {}

    result1 = run_delivery_pipeline(chunks, records, locked_dict, options, options.input_path, options.output_dir)
    result2 = run_delivery_pipeline(chunks, records, locked_dict, options, options.input_path, tmp_path / "out2")

    # Compare TXT content (excluding timestamps)
    txt1 = Path(result1.output_path).read_text(encoding="utf-8")
    txt2 = Path(result2.output_path).read_text(encoding="utf-8")

    # Normalize timestamps
    import re
    txt1_norm = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', 'TIMESTAMP', txt1)
    txt2_norm = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', 'TIMESTAMP', txt2)

    assert txt1_norm == txt2_norm
```

---

### 12. FILE EDIT SUMMARY

| File | Priority | Change Type |
|------|----------|-------------|
| `lts/txt_translation_runtime.py` | P0 | Add `quality_delivery_v83`, `quality_delivery_formats_v83` to `TxtTranslationOptions`; invoke `run_delivery_pipeline(assembled_text=final_text, ...)` after final assembly (feature-gated) |
| `core/translation_runtime/runtime_output.py` | P1 | Add `write_txt_delivery()`, `write_json_delivery()` helpers |
| `core/translation_release/delivery_pipeline.py` | P0 | NEW ??Main orchestrator (receives `assembled_text`, not re-assembling) |
| `core/translation_release/polish.py` | P0 | NEW ??Full-novel polish (conservative quote normalization) |
| `core/translation_release/validator.py` | P0 | NEW ??Final QC gate (`matched_terms` param, source length from records) |
| `core/translation_release/metadata.py` | P0 | NEW ??TOC from explicit RM-8.2 metadata only + metadata injection |
| `core/translation_release/package.py` | P0 | NEW ??Artifact writer (constructs immutable DeliveryResult once) |
| `core/translation_release/models.py` | P0 | NEW ??Dataclasses (frozen DeliveryResult, DeliveryManifest, QualityCertificate, TOCEntry) |
| `core/translation_release/exporters/__init__.py` | P2 | NEW ??Exporter registry |
| `core/translation_release/exporters/base.py` | P2 | NEW ??Base interface |
| `core/translation_release/exporters/epub_exporter.py` | P2 | NEW ??Minimal EPUB (optional dependency, graceful fallback) |
| `core/translation_release/exporters/pdf_exporter.py` | P2 | NEW ??Minimal PDF (optional dependency, graceful fallback) |
| `tests/acceptance/rm8_delivery_test.py` | P2 | NEW ??Acceptance + golden master tests |
| `tests/unit/translation_release/test_polish.py` | P2 | NEW ??Unit tests for polish |
| `tests/unit/translation_release/test_validator.py` | P2 | NEW ??Unit tests for validator |
| `tests/unit/translation_release/test_metadata.py` | P2 | NEW ??Unit tests for metadata/TOC |

---

### 13. ROLLOUT PLAN

| Phase | Action | Validation |
|-------|--------|------------|
| **Phase 1** | Implement `polish.py` + unit tests | `pytest tests/unit/translation_release/test_polish.py` |
| **Phase 2** | Implement `validator.py` + unit tests | `pytest tests/unit/translation_release/test_validator.py` |
| **Phase 3** | Implement `metadata.py` + `models.py` + TOC tests | `pytest tests/unit/translation_release/test_metadata.py` |
| **Phase 4** | Implement `package.py` + `delivery_pipeline.py` | Manual run on fixture; verify artifacts |
| **Phase 5** | Implement exporters (optional) | `pytest tests/unit/translation_release/test_exporters.py` |
| **Phase 6** | Wire into `txt_translation_runtime.py` (feature-gated) | Run canary with `quality_delivery_v83=True` |
| **Phase 7** | Full acceptance test suite | `pytest tests/acceptance/rm8_delivery_test.py -v` |
| **Phase 8** | RM-8.3 Specification review ??**then commit** | All tests pass; no production regression |

---

### 14. COMPLIANCE CHECKLIST

| Constraint | Addressed By |
|------------|--------------|
| No `split_text()` modification | ??Not touched; delivery receives already-assembled text |
| No directory-based paragraph splitting | ??TOC uses RM-8.2 metadata only; no filesystem chunking |
| No RM-7 modification | ??Entity/KE modules not imported |
| No provider/LLM calls | ??Zero network; all offline deterministic |
| No re-translation | ??Polish operates on assembled text only |
| No new quality models | ??Reuses existing formatters, locked dict, canonicalization |
| EPUB/PDF minimal scope | ??Basic structure only; graceful fallback if deps missing |
| Feature-gated | ??`quality_delivery_v83` default OFF |
| Backward compatible | ??Existing `translate_txt()` unchanged when flag OFF |
| No assembly pipeline duplication | ??`assembled_text` passed in; no re-join of chunks |
| Locked-term validation only matched | ??`matched_terms` param; glossary entries not in source excluded |
| Length ratio from existing metadata | ??Uses `record.source.char_count`; unverifiable = info |
| TOC only from explicit RM-8.2 metadata | ??No heuristic chapter title inference |
| Quote normalization conservative | ??Apostrophes preserved; only clear quote pairs converted |
| EPUB/PDF non-blocking | ??P2 optional; core delivery completes without them |

---

### 15. NON-GOALS (LOCKED)

- ??New chunking engine or re-chunking
- ??Modifying `split_text()` or `DEFAULT_CHUNK_SIZE`
- ??RM-7 Entity/Review/Learning pipeline changes
- ??Provider/LLM requests
- ??Re-translation of any content
- ??New quality detection models
- ??Auto-learning
- ??Advanced EPUB/PDF styling (CSS, fonts, layout)
- ??Human review interfaces
- ??RM-8.1/8.2 scope creep
- ??Re-assembly of translated chunks
- ??Heuristic chapter title generation
- ??Full glossary validation (only matched terms)
- ??EPUB/PDF as core acceptance criteria

---

### 16. DEFINITION OF DONE

RM-8.3 **Core** is complete when:

1. **All unit tests pass** (polish, validator, metadata, package)
2. **Acceptance tests pass** (golden master, integration, TOC generation, locked-term validation)
3. **Canary runs** with `quality_delivery_v83=True` produce:
   - `{novel}_zh.txt` with metadata header + TOC (deterministic)
   - `{novel}_delivery_manifest.json` (valid schema)
   - `{novel}_quality_certificate.json` (PASS, score ??70)
4. **Regression suite passes**: All RM-7, RM-8.1, RM-8.2 tests PASS
5. **No production behavior change** when `quality_delivery_v83=False` (default)
6. **Zero provider requests** in delivery pipeline
7. **Specification review CLEAR** ??commit authorized

**EPUB/PDF (Optional Extension ??P2):**
- Implemented as separate exporters with graceful fallback
- **NOT required** for Core PASS
- Core acceptance **does not depend** on EPUB/PDF success
- If dependencies missing (`ebooklib`, `reportlab`), TXT + manifest + QC certificate still complete

---

**End of Specification**
**Status**: Ready for review
**Next**: Specification Review / Consistency Audit ??CLEAR ??Phase 1 Implementation

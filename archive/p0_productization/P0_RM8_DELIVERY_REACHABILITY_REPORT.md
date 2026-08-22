# P0 RM-8.3 Delivery Reachability Report

**Generated**: 2026-08-14  
**Baseline Commit**: 1ee85bf80c23f0fb38b783dab2ba3cfd12736d6b

---

## Delivery Pipeline Entry Point

**File**: `lts/txt_translation_runtime.py`  
**Function**: `translate_txt()`  
**Lines**: 2394-2416

```python
# RM-8.3 Delivery Pipeline (Phase 6) — feature-gated
if options.quality_delivery_v83:
    emit_progress("starting RM-8.3 delivery pipeline", options=options)
    try:
        from core.translation_release.delivery_pipeline import run_delivery_pipeline
        delivery_result = run_delivery_pipeline(
            assembled_text=final_text,
            translated_chunks=translated_chunks,
            chunk_records=records,
            locked_dictionary=locked_dictionary,
            options=options,
            input_path=input_path,
            output_dir=output_dir,
        )
        if delivery_result.status == "failed":
            emit_progress(f"RM-8.3 delivery pipeline FAILED: {delivery_result.error}", options=options)
            # Don't fail the whole translation — delivery is optional extension
        else:
            emit_progress(f"RM-8.3 delivery pipeline SUCCESS: {delivery_result.output_path}", options=options)
    except Exception as e:
        emit_progress(f"RM-8.3 delivery pipeline ERROR: {e}", options=options)
        # Delivery pipeline failure is non-blocking for core translation
```

**Gated by**: `options.quality_delivery_v83` (CLI: `--quality-delivery-v83`)

---

## run_delivery_pipeline() Signature

**File**: `core/translation_release/delivery_pipeline.py`  
**Function**: `run_delivery_pipeline()`

```python
def run_delivery_pipeline(
    *,
    assembled_text: str,
    translated_chunks: list[str],
    chunk_records: list[dict],
    locked_dictionary: dict[str, str],
    options: TxtTranslationOptions,
    input_path: Path,
    output_dir: Path,
) -> DeliveryResult:
```

### Inputs from TxtTranslationOptions

| Field | Used By |
|-------|---------|
| `quality_delivery_v83` | Gate check (already checked before call) |
| `quality_delivery_formats_v83` | Line 185: `formats = getattr(options, "quality_delivery_formats_v83", ("txt",))` |
| `taiwan_traditional_normalization` | Line 119: `polish_full_novel()` |
| `output_formatter_enabled` | Line 120: `polish_full_novel()` |
| `model` | Line 156: `inject_metadata_into_text()` |
| `completed_at` | Line 155: `inject_metadata_into_text()` (via getattr) |

### DeliveryResult (Immutable Dataclass)

```python
@dataclass(frozen=True)
class DeliveryResult:
    status: str                    # "success" | "failed"
    output_path: str               # TXT output path
    manifest_path: str             # Delivery manifest JSON
    qc_certificate_path: str       # Quality certificate JSON
    epub_path: str | None          # Optional EPUB
    pdf_path: str | None           # Optional PDF
    error: str | None              # Error message if failed
```

---

## Delivery Pipeline Stages

1. **Final Canonicalization** (reuse existing) — `canonicalize_novel_chinese`, `apply_literary_collocation_guard`
2. **Polish** (NEW) — `polish_full_novel()` — full novel scope
3. **Validation Gate** (NEW) — `validate_final_novel()` — QualityCertificate
4. **Metadata & TOC** (NEW) — `build_toc_from_chunk_records()`, `inject_metadata_into_text()`
5. **Generate Artifacts** — `generate_delivery_manifest()`, `generate_quality_certificate()`
6. **Write Package + Exporters** — `write_txt_delivery()`, `write_json_delivery()`, optional `pack_epub()`, optional `PdfExporter`
7. **Construct DeliveryResult** — Immutable, all paths collected

---

## Reachability Analysis

### From ntpe_production_translate.py

**Path**: `run_txt()` → `TranslationRuntime.translate_txt()` → `lts.txt_translation_runtime.translate_txt()`

```python
# ntpe_production_translate.py:354-388
def run_txt(args):
    runtime = TranslationRuntime(root=ROOT)
    options = TxtTranslationOptions(
        # ... all CLI args mapped
        quality_delivery_v83=args.quality_delivery_v83,  # Line 386
        quality_delivery_formats_v83=tuple(args.quality_delivery_formats_v83) if args.quality_delivery_formats_v83 else ("txt",),  # Need to verify
    )
    return _print_result("NTPE Production TXT Translation", runtime.translate_txt(options))
```

**Gap Found**: `ntpe_production_translate.py` does NOT pass `quality_delivery_formats_v83` to `TxtTranslationOptions`!

The `TxtTranslationOptions` dataclass has:
```python
quality_delivery_formats_v83: tuple[str, ...] = ("txt",)
```

But `run_txt()` builds options without this field. The argparse defines:
```python
txt.add_argument("--quality-delivery-formats-v83", nargs="+", default=["txt"], choices=["txt", "epub", "pdf"])
```

But the value is never passed to `TxtTranslationOptions`.

### From TranslationRuntime

```python
# core/translation_runtime/runtime.py:211-214
def translate_txt(self, options: Any) -> dict[str, Any]:
    from lts.txt_translation_runtime import translate_txt
    return translate_txt(options, root=self.root)
```

**Pass-through** — no modification, just delegation.

### From lts/txt_translation_runtime.translate_txt()

**Gated call** at lines 2394-2416 — correctly passes all required parameters to `run_delivery_pipeline()`.

---

## DRIFT_FOUND: DELIVERY_FORMATS_NOT_WIRED

**Location**: `ntpe_production_translate.py:run_txt()` (and `run_batch()`)

**Issue**: CLI argument `--quality-delivery-formats-v83` is parsed but **not passed** to `TxtTranslationOptions`.

**Impact**: 
- Delivery pipeline always uses default `("txt",)` 
- EPUB/PDF output formats cannot be activated from CLI
- `--quality-delivery-formats-v83 epub` has no effect

**Fix Required** (P0):
```python
# In run_txt() and run_batch():
options = TxtTranslationOptions(
    # ... existing fields ...
    quality_delivery_v83=args.quality_delivery_v83,
    quality_delivery_formats_v83=tuple(args.quality_delivery_formats_v83) if hasattr(args, 'quality_delivery_formats_v83') and args.quality_delivery_formats_v83 else ("txt",),
)
```

---

## Quality Certificate Reachability

**File**: `core/translation_release/validator.py`  
**Function**: `validate_final_novel()` → returns `ValidationResult`

**Consumes**: 
- `chunk_records` (for literary quality aggregate + context continuity)
- `locked_dictionary`
- `options` (for min_length_ratio, etc.)
- `matched_terms` (computed from chunk_records)

**Produces**: `QualityCertificate` via `generate_quality_certificate()`

**Reachable**: YES — called from `run_delivery_pipeline()` line 130-137.

---

## Manifest Reachability

**File**: `core/translation_release/metadata.py`  
**Functions**: `generate_delivery_manifest()`, `generate_quality_certificate()`

**Reachable**: YES — called from `run_delivery_pipeline()` lines 163-182.

---

## TXT Output Reachability

**File**: `core/translation_release/package.py`  
**Functions**: `write_txt_delivery()`, `write_json_delivery()`

**Reachable**: YES — called from `run_delivery_pipeline()` lines 188-190.

---

## Summary

| Component | Reachable? | Notes |
|-----------|------------|-------|
| `quality_delivery_v83` flag | ���� YES | Wired through CLI → options → translate_txt → delivery_pipeline |
| `quality_delivery_formats_v83` | ������ NO | **CLI parsed but not passed to options** |
| `run_delivery_pipeline()` | ���� YES | Called from translate_txt with correct params |
| `ValidationResult` / `QualityCertificate` | ���� YES | Generated and written |
| `DeliveryManifest` | ���� YES | Generated and written |
| TXT output | ���� YES | `write_txt_delivery()` |
| EPUB output | ���� CONDITIONAL | Requires `epub` in formats + `ebooklib` installed |
| PDF output | ���� CONDITIONAL | Requires `pdf` in formats + `PdfExporter` available |

---

## Required P0 Fix

**Minimal wiring fix in `ntpe_production_translate.py`**:
1. `run_txt()`: Pass `quality_delivery_formats_v83` to `TxtTranslationOptions`
2. `run_batch()`: Pass `quality_delivery_formats_v83` to `BatchTranslationOptions` (verify BatchTranslationOptions has this field)

**Verification**: After fix, `ntpe_production_translate.py txt input.txt output --quality-delivery-v83 --quality-delivery-formats-v83 epub` should produce EPUB.
# NTPE S10-01 — EPUB Production Translation Path Repair Design

Status: DESIGN ONLY (no implementation in S10-01)
Companion: `artifacts/NTPE_S10_01_EPUB_PRODUCTION_PATH_AUDIT.md`
Target phase: S10-02 EPUB Minimal Production Repair

---

## 1. Design Objective

Make the canonical EPUB production path retain its single pipeline and become
runnable end-to-end, by repairing the **earliest broken boundary** only:

```
extraction contract
  -> mapping contract
  -> chunking contract (consumes, not changed)
  -> integration wiring (deduplicate)
  -> focused tests
```

Constraints honored: no runtime rewrite, no chunking rewrite, no packaging
rewrite, no Project rewrite, no TXT change, no second EPUB pipeline, no
security relaxation, no schema change, no provider/model change.

---

## 2. Minimal Repair (ordered)

### R1 — Populate body offsets in extraction (primary fix; owner = extraction)

Where: `core/adapters/epub_extraction_boundary.py`, inside the chapter loop
(`extract()`, around lines 202-222), where `marker` and `chapter_text` are known.

Deterministic derivation (already-normalized text; no later normalization
dependency for correctness):

```
marker = f"=== CHAPTER {chapter_index}: {title or 'Untitled'} ===\n"
body_start_offset = start_offset + len(marker)
body_end_offset   = body_start_offset + len(chapter_text)
```

Then pass these into the `ChapterBoundary(...)` constructor. The trailing `"\n"`
appended to `full_chapter_text` stays outside the body span, exactly matching the
S2 test's `make_extracted_text` model (marker, body, trailing newline).

Invariants preserved:
- `body_start >= start_offset`, `body_end <= end_offset`.
- Empty chapter -> `body_start == body_end`; chunking already emits one empty chunk.
- No architecture change; ~2 lines of assignment plus 2 constructor kwargs.

Risk to TXT: none (EPUB extraction only).

### R2 — Restore metadata handoff (fixes S1; classification B)

Where: the EPUB metadata dict handed to `ExtractedTextIntakeRequest`. Prefer a
single shared constructor so the fix is atomic (see R3).

Preferred minimal option: build the friendly dict from the already-parsed fields
rather than from namespaced `metadata.raw`:

```
epub_metadata = {
    "title": result.metadata.title,
    "author": result.metadata.author,
    "language": result.metadata.language,
    "identifier": result.metadata.identifier,
    "publisher": result.metadata.publisher,
    "date": result.metadata.date,
    "raw": dict(result.metadata.raw),
}
```

This preserves `raw` for provenance while giving intake the plain keys it reads
(`canonical_book_intake_adapter.py:146-154`). Alternative (less invasive to call
sites): normalize namespaced keys inside `ingest_extracted` — but doing so would
hide the producer-side bug; prefer the producer fix plus the shared builder.

### R3 — Deduplicate the mapping (fixes S2; prevents divergence)

Where: introduce ONE EPUB options builder and call it from both production sites
(`ui/translation_studio/pages/project_page.py:1035` and
`ui/translation_launcher/controller.py:72`), rather than copying the extraction →
intake → `EpubTranslationInput` → chunking sequence twice.

Placement: a small function in the EPUB adapter/contract layer (not a new
pipeline). It only assembles existing canonical components. This is required so
R1/R2 are applied once and cannot diverge between the two UIs.

### R4 — Order spine items canonically (fixes S3; latent identity)

Where: `epub_extraction_boundary.py` around `all_spine_items = linear_items + supplementary_items`.
Sort by `spine_position` before iterating and assigning `index`, so
`chapter_map` has strictly increasing `spine_position` (required by
`validation.py:146-151`) and `index == i+1`. No behavior change for all-linear
EPUBs (the common case and the fixture).

### R5 — Fix TOC-title fallback lookup (fixes S4; optional, low risk)

Where: `_resolve_chapter_title_fallback` (`epub_extraction_boundary.py:1146-1162`).
It should use the chapter's resolved `href`/`source_href`, not
`spine_item.get("href")` (spine dicts have no `href`). Small correctness fix for
title fidelity; can be folded into R1 since `full_href` is computed there.

---

## 3. Focused Tests (S10-02 deliverable)

1. **Extraction contract test** — after `extract(make_epub(...))`, assert every
   chapter has non-None `body_start_offset/body_end_offset` and that
   `extracted_text[body_start:body_end]` equals the pure chapter body (no marker).
2. **Extraction → chunking integration test** — the missing positive production
   path: `extract -> ingest_extracted -> build EpubTranslationInput -> chunk_epub_translation_input`
   must succeed and round-trip chapter body text. This is the test that was absent.
3. **Metadata handoff test** — production-style metadata dict yields
   `EpubMetadata.title/author/language/identifier` non-None.
4. **Supplementary-spine test** — EPUB with a non-linear middle item yields a
   strictly increasing `chapter_map` (R4).
5. **Regression fence** — the existing S9-07 negative assertion is updated to a
   positive expectation only after R1 lands; TXT tests must remain unchanged.

Test classification to move from GAP toward PASS:
`REAL PRODUCTION PATH` = new integration test (#2); replace fabricated-offset
reliance where it masks the boundary (do not delete unit tests, add the missing
integration evidence).

---

## 4. Explicit Non-Goals / Boundaries

- No change to `core/epub_translation/chunking.py` (it correctly rejects).
- No change to `core/epub_translation/contract/models.py` (fields already exist).
- No change to runtime, providers, model, packaging, Project schema.
- No new EPUB pipeline; R3 reuses existing canonical components.
- No relaxation of `_validate_zip_security`.
- No TXT path modification.

---

## 5. Schema Requirement

None. `body_start_offset/body_end_offset` already exist on `EpubChapterBoundary`
(`models.py:61-62`) and `ReaderProject` schema v1 already carries
`output.artifact_path`/`execution.resume_state_path`. No schema upgrade is needed.

---

## 6. Fixture Requirement

The existing `tests/e2e/conftest.py::make_epub` is sufficient for R1/R2/R5 and
the positive integration test. Add ONE small deterministic fixture variant with a
non-linear spine item for R4. No large EPUB or external book dependency.

---

## 7. Sequencing to S10-02

```
R1 (extraction body offsets)      <- primary, unblocks the pipeline
R2 (metadata handoff)             <- output-contract fidelity
R3 (deduplicate builder)          <- atomicity
R4 (spine ordering)               <- latent identity correctness
R5 (title fallback)               <- optional fidelity
tests #1..#5                      <- prove the canonical positive path
```

Stop if any repair would require runtime/provider/model/schema changes, a second
pipeline, TXT breakage, or security relaxation. None is expected.

Final principle (S10): make the EPUB production contract correct first, then
extend.

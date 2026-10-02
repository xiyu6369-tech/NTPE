# NTPE S10-02 — EPUB Extraction Contract Repair Report

Baseline HEAD: `4a539b8e8f22576398f1c71ef3bfa16d4c15bc4e`
Actual HEAD: `4a539b8e8f22576398f1c71ef3bfa16d4c15bc4e`
Branch: `main`
Tag: `s9-complete`

Status: REPAIR COMPLETE (production contract repaired; no commit/push/tag)

---

## 1. Scope of Change

Production files modified (exactly two):

```
core/adapters/epub_extraction_boundary.py       (+10)  body offsets
core/adapters/canonical_book_intake_adapter.py  (+57/-...) canonical metadata mapping
```

Tests:

```
tests/integration/test_s10_02_epub_extraction_repair.py   (new, 4 tests)
tests/e2e/test_s9_07_epub_reader_flow.py                  (EPUB-04..06 now positive)
```

Not modified (proven by `git diff --stat`): `core/epub_translation/chunking.py`,
`core/epub_translation/contract/*`, runtime, provider, packaging, Project schema.

Pre-existing dirty files untouched and unstaged:
`memory/character_memory_lts.json`, the four `tests/literary/outputs/*` residuals.

---

## 2. Fix A — Chapter Body Offsets

Boundary: `core/adapters/epub_extraction_boundary.py` (chapter loop).

The extraction already computes `marker`, `chapter_text`, and the
marker-inclusive `start_offset`/`end_offset` in one coordinate space
(`full_chapter_text == marker + chapter_text + "\n"`). The repair derives the
body span in that same space:

```
body_start_offset = start_offset + len(marker)
body_end_offset   = body_start_offset + len(chapter_text)
```

and passes both into `ChapterBoundary(...)`. No change to extraction
architecture, security, ordering, or `chunking.py`.

Coordinate-space proof (asserted in tests):
- `text[start_offset : start_offset + len(marker)] == marker`
- `body_start_offset == start_offset + len(marker)`
- `body_end_offset == end_offset - 1` (trailing newline excluded)
- `text[start_offset:end_offset] == marker + body + "\n"`

`chunk_epub_translation_input()` is unchanged and now receives a valid contract.

---

## 3. Fix B — Canonical Metadata Handoff

Boundary: `core/adapters/canonical_book_intake_adapter.py`.

Production call sites pass `dict(extraction_result.metadata.raw)`, whose keys are
namespace-qualified (e.g. `http://purl.org/dc/elements/1.1/:title`), while intake
previously read plain keys — dropping title/author/language/identifier/publisher/date.

The repair adds one pure canonical mapper used by `ingest_extracted`:

```
build_canonical_epub_metadata(epub_metadata) -> {
    "title", "author" (dc:creator|author), "language",
    "identifier", "publisher", "date", "raw"
}
```

It accepts plain or namespace-qualified keys and produces one canonical plain-key
representation. `raw` (the original namespaced dict) is preserved for provenance.
No schema change; no TXT semantics change; no metadata framework introduced.

Flow is now single-sourced:

```
extraction metadata -> build_canonical_epub_metadata -> intake metadata
                    -> EpubTranslationInput.metadata -> packaging
```

Call sites were intentionally not edited (outside §4 production allowlist); the
adapter is the canonical metadata adapter and normalizes at that boundary.

---

## 4. Explicitly Deferred (not part of the broken contract)

- **S3 — non-linear spine ordering.** Not fixed. The existing fixture is
  all-linear and the positive integration test does not surface observable wrong
  ordering. Recorded as DEFERRED per S10-02 §16. No extraction ordering change.
- **S4 — TOC title fallback (`spine_item.get("href")`).** Not fixed. The
  integration fixture supplies in-document `<h1>` titles, so no missing-title
  breakage is demonstrated. Recorded as DEFERRED per S10-02 §17.
- **S2 — duplicated call-site mapping.** Left as-is; the canonical mapper removes
  the behavioral fault without an architecture change.

No stop condition was triggered.

---

## 5. Tests Added / Updated

### New: `tests/integration/test_s10_02_epub_extraction_repair.py`
Self-contained deterministic EPUB (metadata, 2 chapters, spine, nav, resource);
no Qt, no provider, no network, tmp dirs only.

1. `test_body_offsets_populated_and_slice_correct` — offsets present; marker
   slice exact; `body_start == start + len(marker)`; `body_end == end - 1`;
   body slice marker-free and correct.
2. `test_multi_chapter_offsets_ordered_non_overlapping_and_deterministic` —
   `prev.body_end <= cur.body_start`, `prev.end == cur.start`, re-extraction
   yields identical offsets.
3. `test_metadata_preserved_through_intake` — title/author/language/identifier
   survive extraction → intake (namespaced raw path, as production).
4. `test_positive_extraction_intake_chunking_integration` — real
   `EpubExtractionBoundary → CanonicalBookIntakeAdapter → EpubTranslationInput →
   chunk_epub_translation_input`; chunks are produced with no mocked
   extraction/offsets/chunking.

### Updated: `tests/e2e/test_s9_07_epub_reader_flow.py`
EPUB-04/05 changed from asserting the F1 `ValueError` to asserting the repaired
production path (canonical `EpubTranslationOptions` built with non-empty chunks;
runner faked so provider/network/real translation remain 0).

### Regression runs
```
extraction + contract(s1..s5c) + reader_project : 440 passed
UI epub/s8/s9 suites                            : 80 passed, 1 skipped
tests/ui/test_s6_03_acceptance.py (isolated)    : 7 passed
tests/e2e (full, offscreen)                     : 27 passed
reader_structure packager                       : 56 passed, 3 pre-existing env failures
lts_stage_01 TXT                                : 2 passed, 3 pre-existing stale failures
```

Pre-existing failures, verified unrelated (my changed modules are not imported by
them; `rg` returns no match):
- `reader_structure/test_epub_packager.py` permission/invalid-path tests
  (Windows non-privileged chmod assumptions) — different packager module.
- `lts_stage_01` TXT tests (missing legacy root script `ntpe_translate_txt.py`;
  stale prompt/dry-run expectations).

---

## 6. Boundaries Honored

- Chunking validation: UNCHANGED (no bypass/guess).
- Runtime / providers / model: UNCHANGED; Provider=0, Network=0, Real translation=0.
- TXT: UNCHANGED; impact NONE.
- Packaging: UNCHANGED (not rewritten).
- Security: UNCHANGED (no relaxation).
- Schema: ReaderProject v1 and EPUB contract UNCHANGED.
- Second EPUB pipeline: NONE.
- Fake production route: NONE (S9-07 now exercises real extraction → chunking).
- Glossary: NOT IMPLEMENTED / untouched.
- Root hygiene: PASS (only `artifacts/` + `tests/` additions; tmp dirs used).

---

## 7. Stop Conditions

NONE.

# NTPE S12-06 — EPUB Chunk Offset Contract Minimal Production Repair Report

Repair of the S12-05-identified validator defect. Canonical two-space offset contract is
unchanged; the validator now validates legal chunks according to that contract.

## 0. Baseline

| Metric | Value |
|--------|-------|
| Baseline HEAD | `77fd7ae6e162a7aa806a9d6af141dd43c4d97d09` |
| Actual HEAD | `77fd7ae` + this commit |
| origin/main (before) | `77fd7ae` |
| Branch | `main` |

Baseline verified with `git status --short`, `git branch --show-current`,
`git rev-parse HEAD`, `git rev-parse origin/main`. No reset/clean/stash/restore.

## 1. Canonical offset contract (unchanged)

Per S12-05 (`artifacts/NTPE_S12_05_EPUB_CHUNK_OFFSET_AUDIT.md` §11) and the accepted
prior decision `NTPE_S5_VALIDATION_DEFECT_REPAIR_01_REPORT.md` §2.3:

```text
EpubTranslationChunk.extracted_start/end_offset : absolute in extracted_text (Space C),
                                                   marker-inclusive, 0-based, [start, end)
EpubTranslationChunk.body_start/end_offset      : chapter-body-relative (Space B),
                                                   0-based, [start, end), 0 = body start
invariant: body_range == extracted_range (non-empty chunk); body_range == 0 allowed
```

`EpubChapterBoundary.body_*` remains absolute in `extracted_text` (different model).
No space was redefined; no marker arithmetic and no hardcoded marker length is used.

## 2. Exact validator change

File: `core/epub_translation/contract/validation.py`
Function: `validate_epub_translation_chunk`

Removed the invalid cross-space ordering checks (`body_start >= extracted_start`,
`body_end <= extracted_end`) and replaced them with the same-contract invariant:

```diff
-    # Body offsets must be within extracted range
-    if chunk.body_start_offset < chunk.extracted_start_offset:
-        raise ContractValidationError(
-            f"chunk body_start_offset ({chunk.body_start_offset}) < extracted_start_offset ({chunk.extracted_start_offset})"
-        )
-    if chunk.body_end_offset > chunk.extracted_end_offset:
-        raise ContractValidationError(
-            f"chunk body_end_offset ({chunk.body_end_offset}) > extracted_end_offset ({chunk.extracted_end_offset})"
-        )
+    # body_* are chapter-body-relative; extracted_* are absolute in extracted_text.
+    # They are distinct coordinate spaces, so their raw positions must NOT be
+    # compared. Both ranges describe the same chapter-body segment, so the
+    # same-contract invariant is equal range length (mirrors
+    # EpubTranslationChunk.__post_init__).
+    body_range = chunk.body_end_offset - chunk.body_start_offset
+    if body_range != 0:
+        extracted_range = chunk.extracted_end_offset - chunk.extracted_start_offset
+        if body_range != extracted_range:
+            raise ContractValidationError(
+                f"chunk body range ({body_range}) must equal extracted range ({extracted_range})"
+            )
```

Retained (not weakened): id/order/sequence checks, non-negative checks,
`extracted_end >= extracted_start`, `body_end >= body_start`, and the same-space
chapter-ownership bounds in `validate_chunk_ownership`. This is a contract repair, not a
validation bypass.

Production files modified: **1** (`validation.py`). Chunker, model, adapter,
extraction, TXT, runtime, provider, schema, security: untouched.

## 3. Before failure / after behavior

Before (S12-04, reproduced in S12-05):

```text
chunk_epub_translation_input -> chunk.body_start_offset=0 (relative),
                                chunk.extracted_start_offset=31 (absolute)
translate_epub_translation_input -> validate_chunk_ownership
  -> validate_epub_translation_chunk
     ContractValidationError: chunk body_start_offset (0) < extracted_start_offset (31)
```

After (S12-06):

```text
same chunk -> validate_epub_translation_chunk: PASS (body_range == extracted_range)
           -> validate_chunk_ownership: PASS
           -> real translate_epub_translation_input proceeds past the offset gate
```

## 4. Offset / content-mapping proof (real fixture)

Fixture: 3-chapter EPUB (`Chapter One/Two/Three`), extraction marker present, through the
real extraction -> intake -> `EpubTranslationInput` bridge.

```text
ch1: start=0  end=334  body=[31,333)  marker_len=31
chunk0: body=[0,302)  extracted=[31,333)
        body_start(0) != extracted_start(31)     <- distinct coordinate spaces
        body_range(302) == extracted_range(302)
        extracted_text[31:333] == chunk.source_text          -> True
        chapter_body[0:302]    == chunk.source_text          -> True
```

The repaired validator accepts the chunk while the two raw offsets remain numerically
different — proving the fix targets coordinate-space comparison, not the offsets.

## 5. Real adapter regression (critical)

`tests/integration/test_s12_06_epub_chunk_offset_repair.py`
`test_s12_06_real_adapter_proceeds_past_offset_gate`:

- Real `EpubExtractionBoundary`, real `CanonicalBookIntakeAdapter`, real
  `EpubTranslationInput`, real `chunk_epub_translation_input`, real
  `translate_epub_translation_input`, real `validate_epub_translation_chunk`.
- The only stub is `RuntimeOrchestrator.execute` (deterministic echo) at the provider
  execution boundary.
- Asserts `total_chapters==3`, `total_chunks==3`, `success_count==3`, no
  `ContractValidationError`, and `glossary_path is None` / `glossary_hash is None`.

No deterministic replacement adapter is used (FAIL-H avoided).

## 6. Negative validation (still enforced)

| Test | Case | Result |
|------|------|--------|
| `test_s12_06_negative_body_offset_rejected` | `body_start < 0` | ContractValidationError |
| `test_s12_06_reversed_body_range_rejected` | `body_end < body_start` | validator + model raise |
| `test_s12_06_invalid_extracted_range_rejected` | `extracted_end < extracted_start` | validator + model raise |
| `test_s12_06_range_mismatch_rejected` | `body_range != extracted_range` | ContractValidationError |
| `test_s12_06_range_exceeds_owning_text_rejected` | extracted end beyond chapter end | ContractValidationError (ownership) |

## 7. Marker-free regression

`test_s12_06_marker_free_compatible_case_passes`: zero-length marker
(`body_* == start/end`) still passes; S12-05 negative-reproduction closure preserved.

## 8. S12-04 affected path

`tests/integration/test_s12_04_glossary_reader_first_e2e.py` re-run after repair: 12/12
pass. The S12-04 defect-evidence test previously asserted the failure; it now asserts the
real adapter proceeds past the offset gate (status in `{success, incomplete}`). This is
the §20 "affected test path" flip and the only modification to an existing test; no other
S12-04 assertion was changed or weakened. Full persisted-E2E read-back remains S12-07.

Glossary independence: the offset evidence path passes with `glossary=None`; the fixed
validation runs at `adapter.py:274` before any glossary loading (`adapter.py:281`).
Glossary is not a prerequisite of the offset fix (FAIL-I avoided).

## 9. Regression results

| Suite | Result |
|-------|--------|
| S1/S2/S3/S4/S5/S5B/S5C EPUB contract + unit adapters | 365 passed |
| S10-02, S11-03, S11-06, S11-09, S11-10, S12-06 integration | 32 passed |
| S10-03, S11-04, S11-07 e2e (per file) | 16 passed |
| S6-03 UI acceptance | 7 passed |
| S12-04 integration | 12 passed |
| S12-06 new regression | 9 passed |

Broad regression classification: no S12-06-caused failures. Pre-existing residuals /
environment issues (legacy launcher collection, LCR/TIC fixtures, Windows filesystem
tests, the shared Qt E2E fatal) are unchanged and untouched.

## 10. Side-effect hygiene / accounting

```text
Provider Execution        : 0
Network Execution         : 0
Real Translation          : 0
Production Files Modified : 1 (validation.py, validator only)
Tests Modified            : 2 (new S12-06 file; S12-04 affected-path flip)
Project schema            : unchanged
Runtime architecture      : unchanged
Provider / model          : unchanged
Recovery / hash           : unchanged (offsets are not hashed, not persisted in resume)
TXT                       : unchanged
Security                  : unchanged
```

`git status` after work: only the S12-06 owned paths plus the preserved pre-existing
dirty state (`memory/character_memory_lts.json`, the four `tests/literary/outputs/*`
residuals with `PS-03/README.md` still deleted) and the untracked S11-01/S11-02
artifacts. No sandbox/release/temp EPUB/root diagnostics were left tracked.

## 11. Modified files

```text
core/epub_translation/contract/validation.py                              (validator repair)
tests/integration/test_s12_06_epub_chunk_offset_repair.py                 (new regression)
tests/integration/test_s12_04_glossary_reader_first_e2e.py                (affected-path flip)
artifacts/NTPE_S12_06_EPUB_CHUNK_OFFSET_REPAIR_REPORT.md                  (this report)
```

Excluded/untouched: `core/epub_translation/chunking.py`,
`core/epub_translation/contract/models.py`,
`core/epub_translation/runtime/adapter.py`,
`core/adapters/epub_extraction_boundary.py`, `lts/`, `engine/`, `ui/` (production),
provider, model, runtime, schema, security, S11 closed EPUB chain, pre-existing
residuals.

## 12. Acceptance Matrix

| Gate | Requirement | Result |
|------|-------------|--------|
| Baseline | `77fd7ae` | PASS |
| Canonical Contract | unchanged | PASS |
| Body Space | chapter-relative | PASS |
| Extracted Space | marker-inclusive absolute | PASS |
| Repair Owner | validator | PASS |
| Cross-space Comparison | removed/fixed | PASS |
| Same-contract Invariant | enforced | PASS |
| Chunker | unchanged | PASS |
| Model | unchanged | PASS |
| Adapter | unchanged | PASS |
| Marker Fixture | PASS | PASS |
| Real Adapter | proceeds past validator | PASS |
| Negative Validation | still enforced | PASS |
| Marker-free | PASS | PASS |
| Content Mapping | proven | PASS |
| TXT | unchanged | PASS |
| Security | unchanged | PASS |
| Schema | unchanged | PASS |
| Runtime | unchanged | PASS |
| Recovery | unchanged | PASS |
| Provider | 0 | PASS |
| Network | 0 | PASS |
| Real Translation | 0 | PASS |
| S12-04 | affected failure removed | PASS (full persisted E2E = S12-07) |
| Legacy | untouched | PASS |
| Dirty State | preserved | PASS |
| Hygiene | PASS | PASS |

## 13. Decision

```text
S12_06_EPUB_CHUNK_OFFSET_REPAIR_ACCEPTED
```

S12-04 remains PARTIAL/BLOCKED for the full persisted EPUB E2E until S12-07. Glossary UI,
glossary backend, TXT E2E, and EPUB glossary binding remain PASS.

## 14. Commit

```text
fix(epub): reconcile chunk offset validation spaces
Push origin main · Tag: NO
```

*End of report.*

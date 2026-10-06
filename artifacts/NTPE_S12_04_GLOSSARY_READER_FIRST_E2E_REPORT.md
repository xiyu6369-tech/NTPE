# NTPE S12-04 — Glossary Reader-First Production E2E Verification Report

Verification-only. No production, schema, runtime, provider or model change.

## 0. Baseline

```text
Baseline HEAD : 771bf087b47077b47b33cce7ba3e250dcf28728e
Actual HEAD   : 771bf08 + this commit
Branch        : main
```

## 1. Result Summary

```text
Reader-first glossary verification : PASS
TXT production leg                 : PASS
EPUB option binding + glossary     : PASS
EPUB real-adapter execution leg    : BLOCKED (pre-existing, unrelated production defect)
```

A pre-existing production defect, unrelated to glossary, was discovered while
exercising the real EPUB adapter (§5). Per S12-04 §5/§36 this task records the evidence
and does **not** fix production.

## 2. Test Artifact

`tests/integration/test_s12_04_glossary_reader_first_e2e.py` (12 tests, all pass).

Placement under `tests/integration` follows the S11-10 bounded strategy: the shared Qt
e2e session has a pre-existing PySide6/Python 3.14 fatal; this module drives ProjectPage
synchronously on the main thread, so placement does not change semantics.

Provider injection only: `RuntimeOrchestrator.execute` is replaced by a deterministic
echo. UI action, ReaderProject state, glossary backend, canonical option binding,
canonical glossary loader, canonical post-processing and artifact write/read-back are
real. Runtime root is the hermetic test home (config/character-memory isolation).

## 3. Verified Flows

- UI import (`ProjectPage` + file chooser) -> S12-02 backend -> `ReaderProject` persistence.
- Restart: fresh manager + fresh page reload the same glossary (same content hash,
  term count, active state).
- TXT launch: `apply_glossary_to_options` -> canonical options -> real
  `lts.txt_translation_runtime.translate_txt`; persisted `book_zh.txt`; fresh read has
  `測試詞彙甲` / `鄭泰義`, no `TEST_TERM_A`.
- EPUB launch (binding): canonical `EpubTranslationOptions` carry `glossary_path`
  (project-owned snapshot, not the user file) + `glossary_hash`; the canonical EPUB
  loader returns the terms and canonical `_apply_locked_dictionary` produces the effect.
- Replace: hash changes A != B; the launch uses B; TXT output contains `測試詞彙乙`.
- Detach: launch returns `glossary_path=None` / `glossary_hash=None`.
- Invalid import: project state unchanged (previous glossary preserved); warning shown.
- Corrupt active glossary: launch blocked, runner not invoked, warning shown.
- No glossary: `glossary_path=None`; TXT output keeps `TEST_TERM_A` (feature-off).
- Recovery: same glossary hash -> eligible; different hash -> `blocked_by="glossary"`.
- Determinism: repeated launches give identical `glossary_hash` and `glossary_path`.

## 4. Distinguishing Project Glossary from built-in locked terminology

The fixture adds a glossary-only term `TEST_TERM_A -> 測試詞彙甲` alongside Korean terms.
The no-glossary case proves the Korean terms that appear come only from the project
glossary (the runtime root is hermetic), and the effect is produced by the canonical
`apply_locked_dictionary` / `_apply_locked_dictionary` (no test-side `replace`).

## 5. DISCOVERED PRE-EXISTING PRODUCTION DEFECT (not fixed here)

**EPUB chunk offset validation inconsistency — real adapter aborts on canonical chunks.**

Minimal reproduction (also encoded in
`test_s12_04_epub_real_adapter_chunk_validation_defect_evidence`):

```text
source EPUB (any chapter with a marker prefix, i.e. a title/heading)
-> epub_extraction_boundary.extract            (chapter.start_offset=0, body_start_offset=29)
-> canonical_book_intake_adapter.ingest        (body_start_offset=29, consistent)
-> chunk_epub_translation_input                (chunk.body_start_offset=0 [relative],
                                                chunk.extracted_start_offset=29 [absolute])
-> translate_epub_translation_input
   -> validate_chunk_ownership -> validate_epub_translation_chunk
      ContractValidationError: chunk body_start_offset (0) < extracted_start_offset (29)
```

Cause: `core/epub_translation/chunking.py:196` stores `body_start_offset` relative to the
chapter body, while `core/epub_translation/contract/validation.py:197` requires
`body_start_offset >= extracted_start_offset` (marker-inclusive absolute). The two
subsystems disagree, so `translate_epub_translation_input`
(`core/epub_translation/runtime/adapter.py:274`) rejects the canonical chunks for every
chapter that has a marker prefix.

Why it was not caught: all prior S9/S10/S11 EPUB E2E (`test_s10_03_*`, `test_s11_04/07/10`,
and the S11-10 production-path test) inject a deterministic adapter runtime, bypassing the
real `translate_epub_translation_input`; the real adapter's chunk validation was never
exercised end to end. This defect is independent of glossary.

Impact: the real reader-first EPUB translation path cannot complete on such chapters
until either the chunker emits absolute `body_start_offset` or the validator compares
against the chapter body start. Note: the deterministic-injection EPUB E2E suites still
pass, so this is invisible to the current green suite.

Recommended separate workstream (NOT performed here):

```text
S12-05 — EPUB chunk offset contract reconciliation audit + minimal repair
(decide authoritative offset space; fix chunking.py XOR validation.py; add a real-adapter
 E2E regression that does not inject the adapter runtime)
```

## 6. Regression Results

```text
tests/reader_project + tests/ui/test_s12_03 + S12-02/S11 integration + S12-04   138 passed
S9-07 txt/epub/failure, S10-03 reader/recovery, S11-04, S11-07                  PASS (per-file)
S12-02 backend (26) and S12-03 UI (13)                                          PASS
```

## 7. Broad Regression Classification

S12-04 modifies **no production code** (only `tests/` + `artifacts/`), so the broad
unit/contract/integration results are unchanged from the S12-03 baseline
(unit+contract 3823 passed / 58 failed / 12 errors, all pre-existing). The Qt
whole-directory fatal remains the pre-existing shared-session issue; each file passes
individually. S12-04-caused failures: none.

## 8. Side-effect / Protected-File Hygiene

During development the TXT runtime initially wrote matched terms into the repository
`memory/character_memory_lts.json` (the runtime root defaulted to the repo root). The
test harness now forces a hermetic root, and the protected file was restored to its
committed content (no content diff). `memory/character_memory_lts.json` and the four
`tests/literary/outputs/*` residuals remain the pre-existing dirty state; S11-01/S11-02
untracked artifacts untouched.

## 9. Execution Accounting

```text
Provider Execution : 0
Network Execution  : 0
Real Translation   : 0
Production Files Modified : NO
Schema / Runtime / Legacy : unchanged
```

## 10. Modified Files

```text
tests/integration/test_s12_04_glossary_reader_first_e2e.py   (new)
artifacts/NTPE_S12_04_GLOSSARY_READER_FIRST_E2E_REPORT.md
```

Excluded/untouched: `core/`, `lts/`, `engine/`, `ui/`, `cli/`, provider, model,
pre-existing residuals.

## 11. S12-04 Acceptance

| Gate | Result |
|---|---|
| UI Import | PASS |
| Backend State | PASS |
| Persistence | PASS |
| Restart | PASS |
| TXT Option Binding | PASS |
| TXT Terminology Effect | PASS |
| TXT Output | PASS |
| EPUB Option Binding | PASS |
| EPUB Terminology Effect (canonical mechanism) | PASS |
| EPUB Output (real adapter) | **BLOCKED (pre-existing defect §5)** |
| EPUB Fresh Read-back | **BLOCKED (same defect)** |
| Replace | PASS |
| Detach | PASS |
| Invalid Import | PASS |
| Corrupt Glossary Launch | PASS |
| Recovery | PASS |
| No-glossary | PASS |
| Determinism | PASS |
| S11-03 / S11-07 / S11-10 / S12-02 / S12-03 Regression | PASS |
| Provider / Network / Real Translation | 0 / 0 / 0 |
| Production Changes | NO |

Overall: **PASS for the Glossary capability; FAIL/BLOCKED for the EPUB real-adapter
production leg due to a newly-discovered pre-existing production defect (unrelated to
glossary).**

## 12. Commit

```text
test(glossary): verify reader-first workflow end to end
Push origin main · Tag: NO
```

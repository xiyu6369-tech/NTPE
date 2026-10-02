# NTPE S11-07 — EPUB Non-Linear Spine Semantics Reader-First E2E Report

Baseline HEAD: `a0991c2c9c40c6972442769b2c74085cfe54c0dd`
Actual HEAD (pre-commit): `a0991c2c9c40c6972442769b2c74085cfe54c0dd`
Branch: `main`
`origin/main` = `a0991c2`

Type: verification only. **Production files modified: NO.**
Provider execution: 0. Network execution: 0. Real translation: 0.

---

## 1. Fixture

Deterministic EPUB3, 5 chapters + 1 referenced image; manifest order deliberately
different from spine order.

```
Manifest order: item2, item0, item4, item1, item3, img
Source spine:   item0(yes), item1(no), item2(yes), item3(no), item4(yes)
spine_position: 1, 2, 3, 4, 5
linear:         True, False, True, False, True
chapter_id:     ch0001 .. ch0005
markers:        CHAPTER_ITEM_0 .. CHAPTER_ITEM_4
```

Expected values are derived from the fixture/source contract, not from the final output.

---

## 2. Verified Chain (persisted reader-first production path)

```
source EPUB
  -> production extraction (EpubExtractionBoundary)
  -> canonical intake (CanonicalBookIntakeAdapter)
  -> EpubTranslationInput
  -> chunking (chunk_epub_translation_input)
  -> deterministic injected translation (translate_epub_translation_input patched)
  -> real packaging (pack_epub_resource_aware)
  -> persisted final EPUB artifact
  -> fresh reopen + OPF <spine> parse
  -> reader-facing order / identity / linear semantics
```

The UI reader-first journey (`page._on_translate()`) is used for the persistence test;
ordering-critical layers (extraction, intake, input, chunking, packaging, read-back) are
the real production code and are not mocked. Only runtime execution and the OS opener are
injected.

---

## 3. Results by Stage

| Stage | Observed | Verdict |
|---|---|---|
| Source spine | positions `[1..5]`, titles `[item0..item4]`, linear `[T,F,T,F,T]` | PASS |
| Extraction | positions `[1..5]` (and `!= [1,3,5,2,4]`), titles `[item0..item4]`, `is_linear [T,F,T,F,T]`, status `[linear,supplementary,...]` | PASS |
| Intake | `submission_eligible=True`; titles/linear preserved | PASS |
| Translation input | `chapter_id [ch0001..ch0005]`; `is_linear [T,F,T,F,T]` | PASS |
| Chunking | first-occurrence order `[ch0001..ch0005]`; per-chapter sequence `0..n-1` (no test-side sort) | PASS |
| Deterministic translation | chapter results in canonical order; text carries `[ZH:chNNNN]` identity | PASS |
| Packaging | real `pack_epub_resource_aware`; EPUB written to filesystem | PASS |
| Persistence | artifact exists, `artifact_kind="epub"`, `available=True` | PASS |
| Fresh read-back | chapter hrefs `[item0.xhtml..item4.xhtml]`; markers `[ch0001..ch0005]`; linear `[None,"no",None,"no",None]` | PASS |
| Restart/re-read | new `ProjectPage` + `ReaderProjectManager` reload → same order/semantics/identity | PASS |
| Reader-facing distinction | item1/item3 remain supplementary (`linear="no"`); not removed, not moved to end | PASS |
| Determinism | two runs → identical chapter entries (order + semantics + identity) | PASS |

### Separate assertions (not merged)

- Ordering: `[item0, item1, item2, item3, item4]`
- Semantics: `[yes, no, yes, no, yes]` (canonical parser form `[None,"no",None,"no",None]`)
- Identity: `[ch0001, ch0002, ch0003, ch0004, ch0005]`
- Resource mapping: `img.png` present; each href ↔ content marker correct
  (`item0.xhtml→ch0001`, `item4.xhtml→ch0005`).

`None` denotes the attribute is omitted (EPUB default `yes`) and is treated as distinct
from explicit `"no"`.

---

## 4. Test Results

### S11-07 targeted

```
tests/e2e/test_s11_07_epub_non_linear_spine_semantics_e2e.py    4 passed
  - test_s11_07_source_through_chunking_preserves_order_identity_semantics
  - test_s11_07_final_epub_readback_preserves_order_semantics_identity
  - test_s11_07_reader_first_persisted_artifact_and_restart
  - test_s11_07_determinism_repeated_run_preserves_semantics
```

### Regression locks

```
tests/e2e/test_s11_07_epub_non_linear_spine_semantics_e2e.py
tests/e2e/test_s11_04_epub_spine_ordering_e2e.py
tests/integration/test_s11_06_epub_non_linear_spine_semantics_repair.py
tests/integration/test_s11_03_epub_spine_ordering_repair.py
tests/e2e/test_s10_03_epub_reader_first_e2e.py
tests/e2e/test_s10_03_epub_recovery_e2e.py
tests/contract
= 373 passed
```

- S11-04: PASS (including the updated `test_s11_04_final_epub_linear_attribute_preserved`).
- S11-06: PASS.
- S10-03 reader-first E2E and recovery E2E: PASS (regression only; recovery was not modified).
- S11-03 ordering: PASS.

### Broad regression

Partitions (81 import-time-`SystemExit` legacy modules excluded; single `pytest -q`
remains non-runnable as established in S11-03):

| Partition | Result | vs baseline |
|---|---|---|
| `tests/unit` | 3520 passed, 58 failed, 3 skipped, 2 errors | identical |
| `tests/integration` | 1308 passed, 315 failed, 81 errors | identical |

All failures are pre-existing legacy classes (frozen-artifact/canary/freeze suites,
`lcr_*`, `tic_*`, `stage15_*`, `stage17_2`, `public_api`, `launcher_product`,
`reader_structure` chmod, `lts_stage_01`, `production_submission_adapter`). S11-07 is
test-only and introduced zero new failures.

---

## 5. Side Effects

The broad run generated `.ntpe_test_sandbox/`, which was removed. No root reports,
`release/`, or regenerated tracked files remained. The five pre-existing residuals were
not staged or modified.

---

## 6. Diff Boundary

```
tests/e2e/test_s11_07_epub_non_linear_spine_semantics_e2e.py   (new)
artifacts/NTPE_S11_07_EPUB_NON_LINEAR_SEMANTICS_E2E_REPORT.md  (new)
```

No `core/ lts/ engine/ ui/ cli/` change; schema/runtime/security/TXT unchanged; TOC
fallback not touched.

Pre-existing dirty state (untouched, unstaged):
`memory/character_memory_lts.json`,
`tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json`,
`tests/literary/outputs/PS-03/README.md` (deleted, preserved),
`tests/literary/outputs/Regression_History.json`,
`tests/literary/outputs/Regression_History.md`.
S11-01/S11-02 artifacts remain untracked and were not staged.

---

## 7. Acceptance Gates

| Gate | Result |
|---|---|
| Baseline `a0991c2` | PASS |
| Real reader-first production path | PASS |
| Extraction `T,F,T,F,T` | PASS |
| Intake semantics preserved | PASS |
| Chunking order preserved | PASS |
| Deterministic identity-preserving translation | PASS |
| Real packager | PASS |
| Final EPUB explicit `linear="no"` preserved | PASS |
| Final order `item0..item4` | PASS |
| Spine position `1..5` | PASS |
| Identity `ch0001..ch0005` | PASS |
| Resource mapping correct | PASS |
| Persistence artifact | PASS |
| Fresh read-back semantics | PASS |
| Reader-facing primary/supplementary distinction | PASS |
| Determinism | PASS |
| S11-04 / S11-06 / S10-03 | PASS |
| Provider / Network / Real translation | 0 / 0 / 0 |
| Production change | NONE |
| Security / Schema / Runtime | unchanged |
| Legacy untouched | PASS |
| Dirty state preserved | PASS |
| Hygiene | PASS |

**S11-07 Acceptance: PASS.**

---

## 8. Closure

DEF-1 is closed end-to-end: the source `linear` semantics (`T,F,T,F,T`) survive extraction,
intake, chunking, deterministic translation orchestration, real packaging, artifact
persistence, and fresh reader-side read-back, with order (`item0..item4`) and identity
(`ch0001..ch0005`) unchanged. The S11 EPUB correctness chain — Spine Ordering plus
Non-Linear Semantics — now has a complete Audit → Repair → Integration Regression →
Reader-first E2E loop.

Commit: `test(epub): verify non-linear spine semantics end to end`. Tag: none.

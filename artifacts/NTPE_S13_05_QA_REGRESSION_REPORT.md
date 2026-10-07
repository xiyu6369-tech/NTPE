# NTPE S13-05 — QA Dead-Path Consolidation Regression Report

Companion to `artifacts/NTPE_S13_05_QA_DEAD_PATH_REPAIR.md`. Read-only verification of the
bounded cleanup. No production semantics, tests, or contract changed.

## 0. Baseline / actual

```text
Baseline HEAD  : c35abb7682c34a341e96d0bfb6d1a94768670070
Actual HEAD    : S13-05 cleanup commit (this commit; see final report / git log)
origin/main    : c35abb7 before push; updated by this commit
Branch         : main
```

## 1. Collection boundary

```text
pytest --collect-only  ->  3950 tests collected, 0 errors
```

Identical to the S13-03/S13-04 baseline (3950, 0 errors) — the cleanup did not change the
collection boundary and introduced no collection error.

## 2. Canonical suite results

| Suite | Result | Notes |
|---|---|---|
| `tests/contract` | **338 passed** | matches S13-03 baseline (338) |
| `tests/reader_project` | **86 passed** | matches S13-03 baseline (86) |
| `tests/e2e` | **55 passed** | matches S13-03 baseline (55) |
| `tests/runtime` | **10 passed** | includes `analyze_runtime_quality` boundary |
| `tests/integration/test_s12_06_...` + `test_s12_07_...` | **14 passed** | S12-06 + S12-07 both PASS |

### 2.1 Transient failure encountered and resolved (transparency)

During implementation, an EOF whitespace error introduced by the edit to
`core/translation_runtime/runtime_qa.py` (`new blank line at EOF`) caused 3 contract
failures in `test_git_diff_check` / `test_s5b_tests_still_pass`, because those tests run
`git diff --check`. The blank line was removed and `git diff --check` now exits 0; the
contract suite then passed 338/338. This was an artifact-edit defect, not a semantic
change, and no test was modified.

## 3. Preserved canonical behaviour

- QA remains **advisory**; no new blocking state, `qa_failed`, `failed_chunk`, manifest QA
  field, retry loop, or output rejection.
- `analyze_translation_quality` wrapper, `analyze_runtime_quality`, `BasicTranslationQA`,
  `quality_v5`, discipline, and `translation_naturalness` are unchanged.
- Glossary / EPUB / TXT / Recovery / Output contracts: their suites (contract, reader_project,
  e2e, S12-06, S12-07) all pass unchanged.

## 4. Obsolete Stage-04 tests (unchanged classification)

`tests/lts_stage_04/test_translation_qa.py`:

```text
Before cleanup : 2 failed, 3 passed
After  cleanup : 2 failed, 3 passed   (identical set)
```

The two failures (`test_translate_txt_qa_warn_records_qa_without_failing`,
`test_translate_txt_qa_fail_stops_chunk`) are the obsolete QA-enforcement expectations
documented by S13-04. The cleanup did **not** change their collection or execution, did
**not** reintroduce the old QA-enforcement contract, and did **not** modify production to
satisfy them.

## 5. Static verification

```text
python -m compileall core lts ui   -> exit 0
git grep removed symbols           -> 0 active production/test callers
git diff --check                   -> exit 0
python import/symbol checks        -> OK
```

Archived (out-of-scope, unmodified) `archive/stage_tests/ntpe_te_v30_stage022_runtime_speed_policy_test.py`
still references two removed symbols; it is not collected and was intentionally not
touched (no legacy-archive cleanup in S13-05).

## 6. Qt constraint

```text
tests/e2e : PASS in this run (55 passed)
Historical Windows Qt shared-session access violation : remains DEFERRED.
```

No claim is made that the historical non-deterministic Qt AV is fixed.

## 7. Execution accounting

```text
Provider Execution : 0
Network Execution  : 0
Real Translation   : 0
```

## 8. Working tree / pollution

Pre-existing dirty state preserved and unchanged; no test-generated pollution added to
the commit:

```text
 M memory/character_memory_lts.json
 M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
 D tests/literary/outputs/PS-03/README.md
 M tests/literary/outputs/Regression_History.json
 M tests/literary/outputs/Regression_History.md
?? artifacts/NTPE_S11_01_CAPABILITY_MATRIX.md
?? artifacts/NTPE_S11_01_POST_S10_PRODUCT_CAPABILITY_QUALITY_AUDIT.md
?? artifacts/NTPE_S11_02_EPUB_SPINE_ORDERING_AUDIT.md
?? artifacts/NTPE_S11_02_EPUB_SPINE_ORDERING_DESIGN.md
```

Only the four authorized source paths and the two S13-05 artifacts were staged; no
`git add .` / `git add -A` used. No scratch files created.

## 9. Result

```text
Contract      : PASS (338)
ReaderProject : PASS (86)
Runtime       : PASS (10)
E2E           : PASS (55, Qt historic AV deferred)
S12-06        : PASS
S12-07        : PASS
QA semantics  : unchanged (advisory)
```

**FINAL: PASS**

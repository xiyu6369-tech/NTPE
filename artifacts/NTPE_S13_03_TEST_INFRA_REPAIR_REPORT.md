# NTPE S13-03 — Minimal Test Infrastructure Repair & Canonical Collection Stabilization Report

Implementation / test-only repair, per S13-02 Decision A.

## 0. Baseline

```text
Baseline HEAD : fd7f37c1e92465cb84513a9e65d4b8b93d8e74b3
Actual HEAD   : fd7f37c (repair commit appended separately)
origin/main   : fd7f37c
Branch        : main
```

Pre-existing dirty state preserved (see §7).

## 1. Change summary

Single new file: `tests/conftest.py` — a repository-level pytest collection boundary
(`collect_ignore` for legacy top-level dirs + `collect_ignore_glob` for legacy file/nested
patterns). No production, runtime, schema, provider, EPUB, Glossary, Output or Recovery
change. No test was deleted, moved, renamed or rewritten.

Details: `artifacts/NTPE_S13_03_COLLECTION_BOUNDARY.md`.

## 2. Collection before / after

```text
BEFORE (S13-02 baseline, no boundary):
  pytest --collect-only            -> pytest INTERNALERROR (SystemExit: 2) — aborted
  (7 unguarded files ignored,
   --continue-on-collection-errors)-> 6559 collected, 222 errors

AFTER (S13-03 boundary):
  pytest --collect-only            -> 3950 collected, 0 errors, exit 0
```

The 7 unguarded import-time `SystemExit` legacy wrappers no longer cause an INTERNALERROR;
whole-tree collection is clean.

## 3. 7-wrapper result

All 7 unguarded wrappers are covered by the `**/launcher_*_test.py` ignore glob (see
COLLECTION_BOUNDARY §4). Verified by the clean `--collect-only` (exit 0). Their legacy
status is evidenced by import-time `subprocess.run` of non-existent root scripts +
`raise SystemExit`; no production entry point imports them.

## 4. Legacy quarantine result

Quarantined (evidence-backed, not because they merely fail):

```text
dirs : beta_stage_*, stage_*, foundation_*, rc_stage_*, rm5
files: **/launcher_*_test.py, integration/*_test.py,
       unit/controlled_*/**, integration/controlled_*/**,
       unit/prompt_runtime/**, unit/test_stage15_4/5, validation/test_ntpe_validate.py,
       launcher_prompt_narrative_integration_test.py
```

`tests/contract/controlled_*` (canonical contract tests) are deliberately preserved — an
initial `**/controlled_*/**` draft dropped 36 canonical contract tests and was corrected.

## 5. Canonical verification

```text
pytest --collect-only       : 3950 collected, 0 errors, exit 0
pytest tests/contract       : 338 passed   (matches pre-repair baseline)
pytest tests/reader_project :  86 passed   (matches pre-repair baseline)
pytest tests/e2e            :  55 passed
pytest tests/integration/test_s12_06_epub_chunk_offset_repair.py
                            + test_s12_07_glossary_epub_real_adapter_e2e.py : 14 passed
```

S12-06 / S12-07 real-adapter coverage is preserved and PASS (not quarantined).

`pytest tests/integration` (whole dir): **19 failed / 101 passed, 0 collection errors**.
All 19 failures are legacy stale expectations (LCR `batch109/110/111` governance-freeze
hash/fixture tests, `launcher_product` CLI integration, `stage15_2`/`stage17_2`
integrations); they are collected cleanly and are not on the canonical reader path. They
are documented, not silently deleted.

## 6. Qt / Windows stability

```text
tests/e2e : 55 passed, exit 0 (this session)
```

The S13-02-classified session-scoped `QApplication` / Windows access violation remains a
**deferred test-infrastructure limitation**: it is nondeterministic and was not reproduced
this session. Per S13-03 §6, no production `QApplication` lifecycle, worker-thread or
runtime-threading change was made. The existing integration-placement workaround (S11-10,
S12-07) is retained.

## 7. Pollution check / hygiene

```text
git status --short after all runs:
  M memory/character_memory_lts.json                                  (pre-existing)
  M tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json (pre-existing)
  D tests/literary/outputs/PS-03/README.md                            (pre-existing)
  M tests/literary/outputs/Regression_History.json                    (pre-existing)
  M tests/literary/outputs/Regression_History.md                      (pre-existing)
  ?? artifacts/NTPE_S11_01_* / NTPE_S11_02_*                          (pre-existing untracked)
  ?? tests/conftest.py                                                (S13-03)
```

No new literary outputs / `PS-03-smoke/*` were generated and left behind. Only
`tests/conftest.py` plus the two S13-03 artifacts are staged; `git add .` / `-A` not used.

## 8. Remaining stale expectations (documented, not fixed)

```text
Stage-15/16/17 quality/intelligence unit tests (tests/unit/test_stage15_*, test_stage16_*,
   test_stage17_*) — obsolete APIs (e.g. TypeError: 'NoneType' object is not callable)
LCR governance/offline unit tests (tests/unit/test_lcr_*) — missing legacy frozen fixtures
LCR batch109/110/111 integration governance-freeze tests — frozen-artifact hash/fixture drift
tests/integration launcher_product + stage15_2/stage17_2 legacy integrations
Category A/B/C/E (obsolete behavior / removed architecture / obsolete fixture / legacy
   dependency). NONE is category D (production wrong).
```

These remain on disk; no production semantics were changed to make them pass.

## 9. Acceptance Matrix

| Gate | Result |
|---|---|
| Baseline `fd7f37c` | PASS |
| 7 SystemExit wrappers no longer INTERNALERROR | PASS |
| Legacy quarantine evidence-backed | PASS |
| Canonical suites collect | PASS (0 errors) |
| Canonical e2e PASS | PASS (55) |
| Canonical contract PASS | PASS (338) |
| Canonical reader_project PASS | PASS (86) |
| S12-06 coverage PASS | PASS |
| S12-07 coverage PASS | PASS |
| No production files modified | PASS |
| No schema/runtime/provider change | PASS |
| Provider / Network / Real Translation = 0 / 0 / 0 | PASS |
| Pre-existing dirty state preserved | PASS |
| No hidden second test runtime | PASS |
| No `git add .` / `git add -A` | PASS |
| No repository-root scratch files | PASS |
| Remaining stale expectations documented | PASS |
| Remaining Qt AV limitation documented | PASS |

## 10. Commit

```text
test(infra): stabilize canonical pytest collection
Push origin main · Tag: NO
```

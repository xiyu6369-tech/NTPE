# NTPE S13-03 — Test Collection Boundary

Companion to `artifacts/NTPE_S13_03_TEST_INFRA_REPAIR_REPORT.md`. Baseline HEAD `fd7f37c`.

## 1. Mechanism

A new repository-level `tests/conftest.py` defines `collect_ignore` (legacy top-level
directories) and `collect_ignore_glob` (legacy file/nested-dir patterns). Nothing is
deleted, moved or renamed; quarantined tests remain on disk and can be run explicitly by
path. Test-only change; no production code affected.

## 2. Top-level historical directories (collect_ignore)

```text
beta_stage_*      (beta_stage_01 .. beta_stage_14_6)
stage_*           (stage_14 .. stage_16_2)
foundation_*      (foundation_08_0 .. foundation_09)
rc_stage_*        (rc_stage_01 .. rc_stage_06)
rm5
```

Not canonical reader-first; historical beta/foundation/stage suites. Not imported as
fixtures by canonical tests.

## 3. File / nested patterns (collect_ignore_glob)

```text
**/launcher_*_test.py          # historical launcher wrappers (231 files), incl. all 7
                               #   unguarded import-time SystemExit files
integration/*_test.py          # legacy integration top-level wrappers (lcr_*, translation_*)
unit/controlled_*/**           # legacy controlled-runtime unit suites (import removed modules)
integration/controlled_*/**    # legacy controlled-runtime integration suites
unit/prompt_runtime/**         # legacy prompt-runtime unit suite
unit/test_stage15_4_repetition_detection.py
unit/test_stage15_5_structure_integrity.py
validation/test_ntpe_validate.py
launcher_prompt_narrative_integration_test.py
```

Note: `tests/contract/controlled_*` are **canonical** contract tests and are intentionally
NOT ignored (an earlier draft's `**/controlled_*/**` wrongly dropped 36 canonical contract
tests; corrected to `unit/` + `integration/` only).

## 4. The 7 unguarded import-time `SystemExit` wrappers

All are covered by `**/launcher_*_test.py`:

```text
tests/beta_stage_03/launcher_ai_provider_test.py
tests/stage_14/launcher_ai_provider_framework_test.py
tests/stage_14_1/launcher_provider_runtime_binding_test.py
tests/stage_14_2/launcher_provider_config_layer_test.py
tests/integration/launcher_ter_v19_stability_repetition_guard_test.py
tests/integration/launcher_stage18_13_translation_quality_stabilization_test.py
tests/smoke/launcher_ter_v19_stability_repetition_guard_smoke_test.py
```

Evidence they are legacy wrappers (not canonical): they shell out to root-level
`ntpe_*`/`stage*` scripts that no longer exist and `raise SystemExit(returncode)` at
module import. No production entry script imports them.

## 5. Quarantine justification (per directory)

| Quarantined | Not canonical workflow | Not S12 acceptance | Not a canonical fixture dep | Not a live production contract test |
|---|---|---|---|---|
| beta_stage_* | yes | yes | yes | yes (historical beta acceptance) |
| stage_* | yes | yes | yes | yes (legacy stage suites) |
| foundation_* | yes | yes | yes | yes |
| rc_stage_* | yes | yes | yes | yes |
| rm5 | yes | yes | yes | yes |
| unit/integration controlled_* | yes | yes | yes | yes (replaced by canonical runtime) |
| unit/prompt_runtime | yes | yes | yes | yes |
| launcher_*_test.py | yes | yes | yes | yes |
| integration/*_test.py | yes | yes | yes | yes |

Quarantine reason is **import-time collection failure / removed-module dependency**, not
merely test failure.

## 6. Canonical boundary (preserved)

```text
tests/unit/            test_*.py canonical units (legacy stage15_4/5 + controlled_*/prompt_runtime excluded)
tests/contract/        ALL canonical contract tests (incl. controlled_* contract dirs) - 338 pass
tests/integration/     test_s9/s10/s11/s12 canonical + legacy-named stage suites (collect clean)
tests/e2e/             canonical e2e - 55 pass
tests/ui/              canonical UI tests
tests/reader_project/  canonical project tests - 86 pass
```

S12-06 (`test_s12_06_epub_chunk_offset_repair.py`) and S12-07
(`test_s12_07_glossary_epub_real_adapter_e2e.py`) are preserved and pass (14 total).

## 7. Before / after

```text
Before (S13-02):  pytest --collect-only -> INTERNALERROR SystemExit:2 (aborted)
                  (7 ignored, --continue) -> 6559 collected, 222 errors
After  (S13-03):  pytest --collect-only -> 3950 collected, 0 errors, exit 0
Canonical: contract 338 passed, reader_project 86 passed, e2e 55 passed,
           S12-06+S12-07 14 passed, tests/integration 19 failed / 101 passed (legacy stale)
```

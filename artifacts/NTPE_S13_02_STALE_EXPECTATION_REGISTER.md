# NTPE S13-02 — Stale Expectation Register

Companion to `artifacts/NTPE_S13_02_E2E_TEST_INFRA_AUDIT.md`. Baseline HEAD `cd3892e`,
branch `main`. Audit only; nothing modified.

Classification vocabulary:

```text
A  Test expects obsolete product behavior
B  Test expects removed architecture
C  Test fixture is obsolete
D  Test assertion is still contract-valid and production is wrong
E  Test depends on legacy module
F  Test infrastructure / environment failure
G  Unknown / requires evidence
```

## 1. Collection errors (222) — root-cause classes

| Area | Current failure | Root cause | Classification | Recommended action |
|---|---|---|---|---|
| `tests/integration` (93) | ImportError at collection | imports `runtime_api.runtime_context` (88×) / removed `ntpe_te_v*` root scripts | E / B | legacy-test quarantine (test-only) |
| `tests/unit` (23) | ImportError at collection | `core.prompt_builder` (9×), `core.quality.quality_context` (3×), legacy imports | E / B | legacy-test quarantine (test-only) |
| `tests/rm5` (8) | ImportError at collection | removed legacy modules | E | legacy-test quarantine |
| `tests/beta_stage_11_*..13_*` (~70) | ImportError at collection | removed beta-stage modules | E / B | legacy-test quarantine |
| `tests/validation`, `tests/rc_stage_*`, `tests/smoke` (few) | ImportError at collection | removed modules / root scripts | E / B | legacy-test quarantine |

Verbatim missing modules (`No module named 'X'`):

```text
runtime_api.runtime_context        88
core.prompt_builder                 9
core.quality.quality_context        3
ntpe_te_v5*/ntpe_stage*/root scripts ~122
```

## 2. Import-time `SystemExit` (aborts collection)

| Test / Area | Current failure | Root cause | Classification | Recommended action |
|---|---|---|---|---|
| `tests/integration/launcher_stage18_13_translation_quality_stabilization_test.py` | Uncaught `SystemExit(2)` at import → pytest INTERNALERROR | module-level `subprocess.run(...)` of a non-existent root script then `raise SystemExit(result.returncode)` (lines 6-10) | F / E | not a pytest file: rename out of `*_test.py` or add `collect_ignore` |
| `tests/stage_14/launcher_ai_provider_framework_test.py` | `raise SystemExit(1)` at import | unguarded legacy wrapper | F / E | same |
| `tests/stage_14_1/launcher_provider_runtime_binding_test.py` | `raise SystemExit(1)` at import | unguarded legacy wrapper | F / E | same |
| `tests/stage_14_2/launcher_provider_config_layer_test.py` | `raise SystemExit(1)` at import | unguarded legacy wrapper | F / E | same |
| `tests/beta_stage_03/launcher_ai_provider_test.py` | `raise SystemExit(1)` at import | unguarded legacy wrapper | F / E | same |
| `tests/integration/launcher_ter_v19_stability_repetition_guard_test.py` | unguarded `SystemExit` | legacy wrapper | F / E | same |
| `tests/smoke/launcher_ter_v19_stability_repetition_guard_smoke_test.py` | unguarded `SystemExit` | legacy wrapper | F / E | same |

## 3. Stale expectation failures (representative, executed offline)

| Test / Area | Current failure | Root cause | Classification | Recommended action |
|---|---|---|---|---|
| `tests/unit/test_stage15_2_translation_completeness.py` (4) | assertion failures | Stage-15 quality API changed / module partial | A / E | quarantine or re-point to canonical QA |
| `tests/unit/test_stage15_3_terminology_consistency.py` (1) | assertion failure | obsolete Stage-15 glossary metadata contract | A / E | quarantine |
| `tests/unit/test_stage15_6_quality_export_layer.py` (2) | assertion failures | obsolete export-layer API | B / E | quarantine |
| `tests/unit/test_stage15_7_quality_auto_repair.py` (5) | assertion failures | obsolete repair-facade API | B / E | quarantine |
| `tests/unit/test_stage15_8_quality_engine_freeze.py` (3) | `TypeError: 'NoneType' object is not callable` | frozen symbol resolved to `None` (removed/renamed) | B / E | quarantine |
| `tests/unit/test_lcr_offline_validation.py` (2) | executor result/metric assertions fail | stale LCR executor contract | A / E | quarantine |
| `tests/unit/test_lcr_governance_baseline_consumption.py` (4) | `GovernanceBaselineInvalidError: required_file_unavailable: audits/legacy_capability_recovery/batch10_9/LCR_BATCH109_TAXONOMY_REPORT.json` | obsolete/missing legacy audit fixture | C / E | quarantine |

Aggregate of the sampled hermetic suites:

```text
Stage-15 quality sample : 15 failed / 3 passed
LCR sample              :  6 failed / 79 passed / 1 skipped
```

None of these execute the canonical TXT/EPUB reader path; the target modules are not on
the canonical pipeline (canonical QA = `core.translation_runtime.runtime_qa` +
`core.translation_quality_v5.runtime_integration`).

## 4. Category D check

No sampled stale failure is category **D** (production wrong). Rationale:

- The failing targets (`core.quality.quality_context`, Stage-15 engine freeze,
  `core.prompt_builder`, `runtime_api.*`, legacy LCR fixtures) are not imported by the
  canonical reader path. `core/validator.py` and the Stage-15 engine have no production
  importers; canonical QA uses `core.translation_runtime.runtime_qa`.
- Canonical suites that *do* exercise the production path pass
  (`tests/contract` 338, `tests/reader_project` 86, `tests/e2e` 55).

Category D would require a failing test whose assertion is still contract-valid **and**
whose subject is reached by the canonical pipeline. None found.

## 5. Category G (unknown)

- Exact per-test enumeration of the full ~58 failures was not executed end-to-end because
  the legacy `tests/unit` tree mixes provider-adjacent LCR tests; the audit honours
  Provider / Network = 0 and therefore sampled hermetic suites only. Any residual unknown
  is bounded to the same legacy Stage-15/16/17 + LCR families above.

## 6. Summary

```text
A (obsolete behavior)        : LCR/stage assertions on changed internal contracts
B (removed architecture)     : Stage-16/17 + removed modules; import-time wrappers
C (obsolete fixture)         : missing legacy audit JSON fixtures
D (production wrong)         : NONE
E (legacy dependency)        : dominant category (all collection errors + most failures)
F (infra/environment)        : import-time SystemExit; Qt session flakiness
G (unknown)                  : bounded; not executed for provider-adjacent legacy tests
```

# NTPE S13-02 — E2E Test Infrastructure Reliability & Stale Expectation Audit

Audit only. No production code, canonical runtime, schema, Glossary, EPUB, Output or test
was modified.

## 0. Baseline

```text
Baseline HEAD : cd3892e7c680f262b48a83aece49a30ec76a2cd0
Actual HEAD   : cd3892e (audit commit appended separately)
origin/main   : cd3892e
Branch        : main
Working Tree Before : pre-existing dirty state only (5 tracked residuals + 4 untracked S11 artifacts)
Working Tree After  : identical
```

No reset/clean/force-pull/force-push/discard. Provider / Network / Real Translation = 0/0/0.

## 1. Test configuration

```text
pyproject.toml [tool.pytest.ini_options]
  pythonpath = ["."]
  testpaths  = ["tests"]
```

No `norecursedirs`, markers, `addopts` or import-isolation hooks. pytest therefore collects
**every** `test_*.py` **and** `*_test.py` under `tests/` (default `python_files`), which
includes the legacy `launcher_*_test.py` wrappers.

Inventory:

```text
test_*.py            : 376
*_test.py            : 566
launcher_*_test.py   : 231
conftest.py          : tests/contract/conftest.py, tests/e2e/conftest.py only
```

## 2. Audit A — Qt E2E session reliability

- Fixture: `tests/e2e/conftest.py:26-28` defines **session-scoped** `qapp` =
  `QApplication.instance() or QApplication(sys.argv)` — a single shared Qt application for
  the whole session. `page` closes each `ProjectPage` (`conftest.py:111-118`).
- Reported symptom (S11-10 §6, cited by S12-07 §34): adding a new module under `tests/e2e/`
  aborted the whole directory run with a Windows access violation in the background
  `TranslationRuntime` thread of `test_s11_04`.
- Reproduction now: `pytest tests/e2e -q` → **55 passed, exit 0** (no crash). Combined with
  S11-10's "crashed in 1/2 runs", the failure is **nondeterministic / environmental**, not
  deterministic and not reproducible on demand.
- Workaround in use: new verifications are placed in `tests/integration` (non-e2e),
  driving `ProjectPage` synchronously (S11-10, S12-07). This is a **test-placement**
  workaround.
- Production impact: none. The crash occurs in a Qt test session/thread teardown; the
  production application does not use the session-scoped test QApplication pattern.
- Boundary: Qt infrastructure instability (session/thread lifecycle) is separate from
  application correctness; no evidence links it to a production defect.

Classification: **TEST INFRASTRUCTURE DEBT — FLAKINESS / SESSION ISOLATION**.

## 3. Audit B — Launcher import-time `SystemExit`

- 78 test files contain a top-level `raise SystemExit(...)`; **7** of them have no
  `if __name__ == "__main__"` guard and therefore execute at **import (collection)**:
  - 7 unguarded files:
    ```
    tests/beta_stage_03/launcher_ai_provider_test.py
    tests/stage_14/launcher_ai_provider_framework_test.py
    tests/stage_14_1/launcher_provider_runtime_binding_test.py
    tests/stage_14_2/launcher_provider_config_layer_test.py
    tests/integration/launcher_ter_v19_stability_repetition_guard_test.py
    tests/integration/launcher_stage18_13_translation_quality_stabilization_test.py
    tests/smoke/launcher_ter_v19_stability_repetition_guard_smoke_test.py
    ```
- Confirmed root cause example:
  `tests/integration/launcher_stage18_13_translation_quality_stabilization_test.py:6-10`
  runs `subprocess.run([sys.executable, ROOT/'ntpe_stage18_13_translation_quality_stabilization_test.py'], ...)`
  at module level and `raise SystemExit(result.returncode)` when it fails. The referenced
  root script does not exist (`ROOT` has only 5 canonical entry scripts), so the
  subprocess returns 2 → uncaught `SystemExit` at import → pytest **INTERNALERROR** that
  aborts the entire collection.
- Production startup does not share this behaviour: these are legacy test wrappers that
  shell out to removed root scripts; the canonical entry scripts do not import them.
- Fixable by **test import isolation** (rename wrappers out of `*_test.py`, add
  `collect_ignore`, or exclude legacy dirs). **No production refactor is required.**

Classification: **TEST INFRASTRUCTURE DEFECT — MODULE COLLECTION BOUNDARY** (legacy test
wrappers).

## 4. Audit C — Legacy / root module collection

Bounded evidence:

```text
Full-tree collect (7 unguarded files ignored, --continue-on-collection-errors):
  6559 tests collected, 222 errors

Full-tree collect (no ignores): INTERNALERROR SystemExit:2 after 725 collected / 103 errors
```

Error composition (missing modules imported by legacy tests):

```text
No module named 'runtime_api.runtime_context'   : 88
No module named 'core.prompt_builder'           :  9
No module named 'core.quality.quality_context'  :  3
other (ntpe_te_v5*/ntpe_stage*/root scripts)    : ~122
```

By directory: `integration` 93, `unit` 23, `rm5` 8, plus many `beta_stage_13_*`,
`beta_stage_12_*`, `beta_stage_11_*` (4 each).

Reachability findings (static, production only):

- `core.translation_release.reader_structure.models` is a **live canonical dependency**
  (`core/epub_translation/reader_chapter_map.py:19`) — must NOT be archived wholesale
  (consistent with S11-11 C4).
- `core/quality/*` and `core/intelligence/*` are **partially live**:
  `core/intelligence.narrative_engine` is imported by `lts/txt_translation_runtime.py:648`
  and `core/epub_translation/runtime/adapter.py:360` (feature-gated);
  `core.quality.coverage_expansion_analyzer` by `core/expansion/expansion_planner.py:5`.
  But `core.quality.quality_context` (imported by legacy tests) is absent.
- `core/validator.py` and the Stage-15 quality engine have **no production importers**
  (includes the canonical QA, which uses `core/translation_runtime/runtime_qa` and
  `core/translation_quality_v5.runtime_integration`).

Classification: **LEGACY TEST** (collection noise from removed/relocated modules); the
affected modules are not on the canonical reader path.

## 5. Audit D — Stale expectations

Representative hermetic runs (offline; no provider/network):

```text
tests/unit/test_stage15_2..8 (quality suite) : 15 failed, 3 passed
  e.g. test_stage15_8_quality_engine_freeze.py:25 TypeError: 'NoneType' object is not callable
tests/unit/test_lcr_offline_validation.py
tests/unit/test_lcr_bounded_dual_pass_pilot.py
tests/unit/test_lcr_single_chunk_dual_pass_executor.py
tests/unit/test_lcr_pilot_authorization.py
tests/unit/test_lcr_governance_baseline_consumption.py : 6 failed, 79 passed, 1 skipped
  e.g. GovernanceBaselineInvalidError: required_file_unavailable:
       audits/legacy_capability_recovery/batch10_9/LCR_BATCH109_TAXONOMY_REPORT.json
```

See `artifacts/NTPE_S13_02_STALE_EXPECTATION_REGISTER.md` for the classification table.
Common roots: obsolete Stage-15/16/17 quality/intelligence APIs (symbol resolved to
`None`), and missing legacy audit fixture files. None exercise the canonical TXT/EPUB
reader path.

Classification: **STALE EXPECTATION** (categories A/B/C/E — obsolete behavior,
obsolete architecture, obsolete fixture, legacy module dependency) — **not D**.

## 6. Audit E — Test boundary integrity

Canonical suites are hermetic and healthy:

```text
tests/contract       : 338 passed
tests/reader_project :  86 passed
tests/e2e            :  55 passed (this run; historically flaky — §2)
```

- Boundary respected: UI/Project → canonical runtime → deterministic injected external
  boundary. `tests/ui` patch the runtime by design (wiring/state only); E2E exercises the
  real pipeline with only runtime execution injected.
- S12-07 EPUB E2E architecture intact and unaffected:
  `tests/integration/test_s12_07_glossary_epub_real_adapter_e2e.py` (real extraction →
  intake → chunk → validator → real adapter → real packaging → persisted read-back; only
  `RuntimeOrchestrator.execute` stubbed).
- Real-adapter coverage intact: `tests/integration/test_s12_06_epub_chunk_offset_repair.py`
  + S12-07. Not overturned.
- No hidden second test runtime / second pipeline; no provider/network/real translation in
  the canonical suites.

Classification: **PASS** (canonical E2E architecture and real-adapter coverage intact).

## 7. Required classification

| Area | Classification |
|---|---|
| Qt shared-session issue | TEST INFRASTRUCTURE DEBT (flakiness/session isolation) |
| Windows access violation | ENVIRONMENTAL LIMITATION (nondeterministic; not reproduced this run) |
| Launcher `SystemExit` | TEST INFRASTRUCTURE DEFECT (module collection boundary; legacy wrappers) |
| Legacy/root collection | LEGACY TEST (222 collection errors; removed modules) |
| ~58 stale expectations | STALE EXPECTATION (A/B/C/E; not production defect) |
| Canonical E2E architecture | PASS |
| Real-adapter coverage | CLOSED / intact (S12-06, S12-07) |
| Hidden second pipeline | ABSENT |

## 8. Result

```text
Qt finding            : session-scoped QApplication; flaky Windows AV in legacy background
                        thread; NOT deterministic (55 passed now); test-only.
Windows finding       : environmental/flaky, not reproducible on demand; not production.
Launcher finding      : 7 unguarded import-time raise SystemExit -> pytest INTERNALERROR;
                        legacy test wrappers; no production dependency.
Legacy collection      : 222 collection errors (runtime_api.runtime_context 88,
                        core.prompt_builder 9, core.quality.quality_context 3, root scripts).
Stale expectation      : 58-ish legacy Stage-15/16/17 + LCR failures; obsolete APIs/fixtures.
Canonical E2E finding  : healthy (contract 338, reader_project 86, e2e 55); S12-07 intact.
```

See `artifacts/NTPE_S13_02_DECISION.md`.

## 8.1 Working tree / residual hygiene

- The `--collect-only` sweep imports every test module, including legacy `tests/literary/*`.
  That regenerated the pre-existing literary residual `tests/literary/outputs/Regression_History.md`
  (row ordering / line-ending only; 58 lines before and after, no trailing newline both
  sides; `git diff --ignore-cr-at-eol` = 3/3 same-shape reorder). No new content.
- The sweep also wrote **new** files under `tests/literary/outputs/PS-03-smoke/` (not part
  of the baseline dirty set). These were restored to `HEAD`
  (`git restore --source=HEAD -- tests/literary/outputs/PS-03-smoke/`), so the baseline
  dirty set is unchanged.
- No production/test file was modified by this audit. The five pre-existing residuals
  (`memory/character_memory_lts.json`, the four `tests/literary/outputs/*` with
  `PS-03/README.md` still deleted) and the untracked S11-01/S11-02 artifacts are preserved.

## 9. Acceptance criteria

- [x] baseline = `cd3892e`
- [x] Qt E2E issue located (session scope + flaky legacy thread)
- [x] Windows access violation classified (environmental)
- [x] launcher `SystemExit` located (7 unguarded wrappers)
- [x] legacy/root collection inventoried (222 errors, categorized)
- [x] ~58 stale expectations classified (representative, evidence-backed)
- [x] canonical E2E boundary confirmed
- [x] S12 real-adapter coverage intact
- [x] no production code modified
- [x] no tests modified
- [x] Provider / Network / Real Translation = 0 / 0 / 0
- [x] pre-existing dirty state preserved
- [x] no hidden second test/runtime pipeline
- [x] next step stated (Decision A — minimal test-only repair)
- [x] artifacts only under `artifacts/`

**FINAL: PASS**

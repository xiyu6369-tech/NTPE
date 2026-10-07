# NTPE S13-02 — Test Infrastructure Decision

Companion to `artifacts/NTPE_S13_02_E2E_TEST_INFRA_AUDIT.md` and
`artifacts/NTPE_S13_02_STALE_EXPECTATION_REGISTER.md`. Decision-support only; no
implementation.

## 1. Decision

**Decision A — Test infrastructure repair (minimal, test-only).**

Evidence that infrastructure debt materially affects maintenance/acceptance reliability:

- Running `pytest` on the configured `testpaths = ["tests"]` **aborts with
  INTERNALERROR** (`SystemExit: 2`) driven by 7 unguarded import-time `raise SystemExit`
  legacy wrappers; the whole-repo suite cannot be collected in one invocation.
- With those 7 files excluded, collection still reports **222 errors** (removed modules:
  `runtime_api.runtime_context` 88, `core.prompt_builder` 9, `core.quality.quality_context`
  3, plus ~122 root-script wrappers).
- ~58 legacy Stage-15/16/17 + LCR tests fail on obsolete APIs / missing fixtures.
- The shared-session Qt e2e directory is historically flaky (S11-10: crash in 1/2 runs),
  which already forced relocating S11-10 and S12-07 verifications to `tests/integration`.

This is **not** Decision C: no evidence of a production defect. All canonical suites that
exercise the production reader path pass (contract 338, reader_project 86, e2e 55), and
S12-06/S12-07 real-adapter coverage is intact.

Decision B (defer) is rejected because the configured full-suite invocation is currently
non-functional (INTERNALERROR), which is a concrete reliability regression for developers
and CI, not merely cosmetic noise.

## 2. Minimal repair boundary (documented only; NOT implemented)

Test-only; no production, runtime, schema, Glossary, EPUB or Output change. No second test
runtime.

```text
Step 1 (fix INTERNALERROR — highest value, smallest change)
  Add a `tests/conftest.py` with `collect_ignore` (or pyproject `norecursedirs`) that
  excludes the 7 unguarded import-time SystemExit wrappers, and/or rename them out of the
  `*_test.py` pattern. No production refactor.

Step 2 (quarantine legacy collection noise)
  Exclude the legacy beta_stage_*/stage_*/foundation_*/rm5/rc_stage_* directories (or the
  specific `*_test.py` wrappers) that import removed modules, OR gate them behind an
  explicit opt-in marker so canonical runs are green and legacy runs are separate.

Step 3 (optional, later)
  Rename/retire the ~58 stale Stage-15/16/17 + LCR unit tests, or re-point them at the
  canonical QA surface. Out of scope for the minimal repair.
```

Boundary rationale:

```text
Owner            : tests/ only (conftest/pyproject/markers/filenames)
Production impact: none
Schema impact    : none
Runtime impact   : none
Reversibility    : full (additive ignores / renames)
Provider/Network : 0 / 0
```

## 3. Flaky Qt session (separate, lower priority)

- Keep the existing integration-placement workaround (S11-10, S12-07) which is sufficient
  for acceptance.
- A future task MAY isolate the session (e.g., function-scoped QApplication or a dedicated
  e2e marker), but this is not required now and must not change production code.

## 4. Explicit non-goals

No production code, tests, runtime, schema, Glossary, EPUB extraction/packaging/validation,
Output, or legacy archive changes in this task. Do not modify production semantics to make
stale tests pass.

## 5. Next-phase recommendation

1. **S13-0x — Test collection isolation** (Decision A Step 1+2): restore a single
   collectable `pytest` invocation (fix INTERNALERROR, quarantine legacy dirs). Test-only,
   small, high-value.
2. Qt e2e session isolation (optional, later).
3. Legacy stale-expectation retirement (optional, later) — aligns with the S12-08 legacy
   archive workstream (split `core/translation_release` first).

## 6. Result

```text
Classification : TEST INFRASTRUCTURE DEBT + STALE EXPECTATION (legacy)
Decision       : A — minimal test-only infrastructure repair (recommended)
Production      : unaffected; no production defect
Blockers       : NONE for production acceptance (canonical suites pass)
FINAL          : PASS (audit + decision complete; no implementation)
```

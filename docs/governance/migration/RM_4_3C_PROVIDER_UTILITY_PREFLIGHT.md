# RM-4.3C — Provider Utility Preflight Analysis

## Phase
RM-4: Repository De-Historicization  
`RM-4.3C` — Preflight: Provider Utility Migration Planning

## Date
2026-07-31

## Baseline
- **RM-4.2D Wrapper Migration Plan**: `docs/governance/migration/RM_4_2D_WRAPPER_MIGRATION_PLAN.md`
- **RM-4.3B Legacy Pipeline**: COMMITTED (`ac3b6da`)
- Root Python count: **20**

---

## Candidate List (RM-4.2D Batch C)

Target directory: `tools/provider_utils/`

| # | File | Current Location | RM-4.2D Classification |
|---|------|------------------|------------------------|
---

## Dependency Scan

### 1. `ntpe_provider_setup.py`

| Check | Result | Detail |
|-------|--------|--------|
| Python `import` | ⚠️ 1 importer | `tests/regression/provider_environment_regression_test.py` line 7 |
| Production import | ✅ 0 | Zero `core/`, `lts/`, `engine/` importers |
| Runtime dependency | ✅ 0 | No runtime calls |
| Validator dependency | ✅ No | Not in `ntpe_validate.py` REQUIRED_ENTRYPOINTS |
| External CLI | ✅ None | No README/CI/batch documentation |
| lts/ references | ✅ 0 | Zero subprocess or path checks |
| Pytest collected | ⚠️ 2 tests | funcs in provider_environment_regression_test.py |

**Risk**: Test file uses bare `import ntpe_provider_setup as setup`. Naked `git mv` will break this test at import time.

### 2. `ntpe_provider_verify.py`

| Check | Result | Detail |
|-------|--------|--------|
| Python `import` | ⚠️ 1 importer | Same test file, line 8: `import ntpe_provider_verify as verify` |
| All other gates | ✅ PASS | Zero production/runtime/validator/CLI/lts references |

**Risk**: Same test file as #1.

### 3. `ntpe_provider_audit.py`

| Check | Result | Detail |
|-------|--------|--------|
| Python `import` | ⚠️ 2 importers | `tests/integration/provider_configuration_test.py` (line 8) + `archive/stage_tests/ntpe_ter_v23_provider_configuration_audit_test.py` (line 5) |
| All other gates | ✅ PASS | Zero production/runtime/validator/CLI/lts |

**Risk**: Two importers; one active test, one archive test.

### 4. `ntpe_lcr_batch107_real_provider_validation.py`

| Check | Result | Detail |
|-------|--------|--------|
| Python `import` | ✅ 0 | **Zero importers** (verified across 5088 files) |
| Production import | ✅ 0 | Zero |
| Runtime dependency | ✅ 0 | No runtime calls |
| Validator dependency | ✅ No | Not in REQUIRED_ENTRYPOINTS |
| External CLI | ✅ None | Manual execution only |
| lts/ references | ✅ 0 | Zero |
| 4 | `ntpe_lcr_batch107_real_provider_validation.py` | root | SAFE_MOVE |
---

## Gate Conditions Evaluation

| Condition | #1 setup | #2 verify | #3 audit | #4 batch107 |
|-----------|:---:|:---:|:---:|:---:|
| ✅ No production import | ✅ | ✅ | ✅ | ✅ |
| ✅ No runtime import | ✅ | ✅ | ✅ | ✅ |
| ✅ No validator dependency | ✅ | ✅ | ✅ | ✅ |
| ✅ No active manifest dependency | ✅ | ✅ | ✅ | ✅ |
| ✅ No CLI compatibility requirement | ✅ | ✅ | ✅ | ✅ |
| ⚠️ No test import (bare SAFE_MOVE) | ❌ 1 | ❌ 1 | ❌ 2 | ✅ 0 |

---

## Classification & Recommendations

### Case A: SAFE_MOVE — Clean (no changes needed)

| File | Confidence |
|------|-----------|
| `ntpe_lcr_batch107_real_provider_validation.py` | ✅ HIGH — zero importers, self-contained |

**Action**: `git mv` → `tools/provider_utils/` + update `project_layout_policy.json`. Zero import changes.

### Case B: SAFE_MOVE — Requires import update

| File | Importers to update | Tests affected |
|------|---------------------|----------------|
| `ntpe_provider_setup.py` | 1 (`tests/regression/provider_environment_regression_test.py`) | 2 |
| `ntpe_provider_verify.py` | 1 (same file) | 2 |
| `ntpe_provider_audit.py` | 2 (`tests/integration/provider_configuration_test.py` + `archive/stage_tests/ntpe_ter_v23_provider_configuration_audit_test.py`) | 1 active + 1 archive |

**Options**:

1. **Option A — Direct import update**: Update import statements in test files only (no logic change). `import ntpe_provider_setup` → `from tools.provider_utils import ntpe_provider_setup`
2. **Option B — Root thin wrapper**: Place compatibility stubs at root (RM-4.4 pattern). Zero test modifications.
3. **Option C — Split batch**: Move #4 now as clean SAFE_MOVE; defer #1–#3 to RM-4.4 Wrapper phase.

### Recommendation

**Option C — Split batch** for strictest RM-4.3B policy compliance (no wrappers, no test modifications):

- **RM-4.3C**: Move `ntpe_lcr_batch107_real_provider_validation.py` only
- **RM-4.4**: Handle `ntpe_provider_setup.py`, `ntpe_provider_verify.py`, `ntpe_provider_audit.py` with root wrappers
---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Test breakage (#1-3) | ⚠️ MEDIUM | Options A or B required; naked git mv WILL break 2 test files |
| Provider execution triggered | ✅ LOW | Only via explicit `--execute` CLI flag |
| ntpe_validate regression | ✅ NONE | None in REQUIRED_ENTRYPOINTS |
| Archive test import (#3) | ⚠️ LOW | 1 archive test still imports |

---

## Summary

| # | File | RM-4.2D | Importers | Gate | Risk | Rec |
|---|------|---------|-----------|------|------|-----|
| 1 | `ntpe_provider_setup.py` | SAFE_MOVE | 1 test | ⚠️ FAIL | MEDIUM | Defer RM-4.4 |
| 2 | `ntpe_provider_verify.py` | SAFE_MOVE | 1 test | ⚠️ FAIL | MEDIUM | Defer RM-4.4 |
| 3 | `ntpe_provider_audit.py` | SAFE_MOVE | 2 tests | ⚠️ FAIL | MEDIUM | Defer RM-4.4 |
| 4 | `ntpe_lcr_batch107_real_provider_validation.py` | SAFE_MOVE | **0** | ✅ PASS | LOW | **SAFE_MOVE** |

---

## Next Step

Only file #4 is gate-clean. Execute RM-4.3C with 1 SAFE_MOVE → `tools/provider_utils/`.

Deferred 3 to RM-4.4 (Provider Wrappers).

## Compliance (Preflight)

| Op | Status |
|----|--------|
| Git mv | ❌ |
| Python edit | ❌ |
| Import edit | ❌ |
| Provider exec | ❌ |
| Network | ❌ |
| Commit | ❌ |
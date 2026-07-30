# RM-4.3C — Provider Utility Migration Report

## Phase
RM-4: Repository De-Historicization  
`RM-4.3C` — Batch C: Provider Utility Migration (1 SAFE_MOVE)

## Date
2026-07-31

## Baseline
- **RM-4.2D Wrapper Migration Plan**: `docs/governance/migration/RM_4_2D_WRAPPER_MIGRATION_PLAN.md`
- **RM-4.3C Preflight**: `docs/governance/migration/RM_4_3C_PROVIDER_UTILITY_PREFLIGHT.md`
- **RM-4.3B**: COMMITTED (`ac3b6da`)

---

## Scope

Per RM-4.3C Preflight gate analysis, only **1 of 4** Batch C candidates passed all gate conditions for SAFE_MOVE:

| # | File | Gate Result | Action |
|---|------|-------------|--------|
| 1 | `ntpe_provider_setup.py` | ⚠️ FAIL (1 test importer) | **Deferred → RM-4.4** |
| 2 | `ntpe_provider_verify.py` | ⚠️ FAIL (1 test importer) | **Deferred → RM-4.4** |
| 3 | `ntpe_provider_audit.py` | ⚠️ FAIL (2 test importers) | **Deferred → RM-4.4** |
| 4 | `ntpe_lcr_batch107_real_provider_validation.py` | ✅ ALL PASS (0 importers) | **SAFE_MOVE → tools/provider_utils/** |

### Gate Confirmation for #4

| Gate | Status |
|------|--------|
| Zero Python importers | ✅ 0 (verified across 5088 files) |
| Zero production import | ✅ 0 |
| Zero runtime dependency | ✅ 0 |
| Zero validator dependency | ✅ Not in REQUIRED_ENTRYPOINTS |
| Zero manifest dependency | ✅ 0 |
| Zero active test dependency | ✅ 0 |
| Zero CLI compatibility requirement | ✅ Manual execution only |

---

## Migration Manifest

### File Moved (1/1)

| Source (root) | Destination |
|---------------|-------------|
| `ntpe_lcr_batch107_real_provider_validation.py` | `tools/provider_utils/ntpe_lcr_batch107_real_provider_validation.py` |

### New Directory Created

- `tools/provider_utils/` — holds provider utility launchers (1 file now; 3 deferred to RM-4.4)

---

## Configuration Update

`config/project_layout_policy.json`:

- **`allowed_root_files`**: 320 → 319 (−1)
- **`retained_root_wrappers`**: 13 → 12 (−1)

Removed: `ntpe_lcr_batch107_real_provider_validation.py` (both sections)

---

## Before / After

| Metric | Before | After |
|--------|-------:|------:|
| Root Python files | 20 | 19 |
| Provider utils at root | 4 | 3 |
| Provider utils in `tools/provider_utils/` | 0 | 1 |
| `allowed_root_files` entries | 320 | 319 |
| `retained_root_wrappers` entries | 13 | 12 |
| Errors | 0 | 0 |

---

## Validation Results

| Check | Result | Detail |
|-------|--------|--------|
| `git diff --check` | ✅ PASS | Exit 0, no violations |
| `python ntpe_validate.py` | ✅ ALL PASS | All 8 checks; Root Python layout: 19 files |
| `python -m compileall tools/provider_utils` | ✅ PASS | 1/1 compiled, 0 errors |
| Production imports | ✅ Unchanged | Zero changes |
| Runtime | ✅ Unchanged | `core/`, `lts/`, `config/` untouched |
| Provider requests | 0 | No API calls |
| Network requests | 0 | All local |
| File content modification | 0 | R100 rename only |

---

## Deferred to RM-4.4

| File | Reason |
|------|--------|
| `ntpe_provider_setup.py` | 1 test importer (`tests/regression/provider_environment_regression_test.py`) |
| `ntpe_provider_verify.py` | 1 test importer (same file) |
| `ntpe_provider_audit.py` | 2 test importers (`tests/integration/provider_configuration_test.py` + `archive/stage_tests/ntpe_ter_v23_provider_configuration_audit_test.py`) |

These require root compatibility wrappers (RM-4.4 pattern).

---

## Rollback

```powershell
cd D:\Python\NTPE
git mv tools/provider_utils/ntpe_lcr_batch107_real_provider_validation.py ntpe_lcr_batch107_real_provider_validation.py
git checkout -- config/project_layout_policy.json
```

---

## Compliance: Forbidden Operations

| Operation | Performed |
|-----------|-----------|
| Python logic modification | ❌ No |
| Import modification | ❌ No |
| Runtime modification | ❌ No |
| Provider execution | ❌ No |
| Translation execution | ❌ No |
| Git commit | ❌ No (staged only) |
| Git push | ❌ No |
| Wrapper creation | ❌ No |
| Test modification | ❌ No |
| Network requests | ❌ No |

---

## Final Verdict

```
RM-4.3C Provider Utility Migration  ✅ COMPLETE (1/4)
```

1 SAFE_MOVE: `ntpe_lcr_batch107_real_provider_validation.py` → `tools/provider_utils/`  
3 deferred to RM-4.4 (Provider Wrappers).

Zero content modifications. R100 rename. All validation gates passed.

**Next Stage:** RM-4.4 — Provider Wrappers + Compatibility Stubs (Batch D + deferred #1-#3)
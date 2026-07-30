# RM-4.3B — Legacy Pipeline Demo Migration Report

## Phase
RM-4: Repository De-Historicization  
`RM-4.3B` — Batch B: Legacy Pipeline Demo Migration

## Date
2026-07-31

## Baseline
- **RM-4.2D Wrapper Migration Plan**: `docs/governance/migration/RM_4_2D_WRAPPER_MIGRATION_PLAN.md`
- **RM-4.3A One-Shot Migration**: COMPLETE (17 SAFE_MOVE → `tools/one_shots/`)

---

## Scope

All 5 Batch B targets identified in RM-4.2D were migrated: 4 SAFE_MOVE to `tools/legacy_pipeline_launchers/` and 1 ARCHIVE to `archive/legacy_tools/`.

### Migration Criteria (confirmed per RM-4.2D)
- Zero Python importers (no `import launcher_pipeline` anywhere in production code)
- Zero production runtime dependency
- Zero validator dependency (not in `ntpe_validate.py` REQUIRED_ENTRYPOINTS)
- Zero external compatibility requirement
- No Wrapper needed

---

## Pre-Flight Gate

| Gate | Status | Detail |
|------|--------|--------|
| Production imports | ✅ PASS | Zero Python importers for all 5 candidates |
| Runtime dependency | ✅ PASS | `core/`, `lts/` have zero references |
| Validator dependency | ✅ PASS | Not in REQUIRED_ENTRYPOINTS (only `launcher.py`, `launcher_translate.py`, `ntpe_translate_txt.py`, `ntpe_translate_batch.py`) |
| README / CI / LTS new references | ✅ PASS | Zero new references |
| RM-4.2D classification | ✅ MATCH | 5/5 candidates unchanged since RM-4.2D audit |

---

## Migration Manifest

### Files Moved (5/5)

| # | Source (root) | Destination | Action |
|---|---------------|-------------|--------|
| 1 | `launcher_adaptive_recovery.py` | `tools/legacy_pipeline_launchers/launcher_adaptive_recovery.py` | SAFE_MOVE |
| 2 | `launcher_pipeline.py` | `tools/legacy_pipeline_launchers/launcher_pipeline.py` | SAFE_MOVE |
| 3 | `launcher_pipeline_production.py` | `tools/legacy_pipeline_launchers/launcher_pipeline_production.py` | SAFE_MOVE |
| 4 | `launcher_pipeline_recovery.py` | `tools/legacy_pipeline_launchers/launcher_pipeline_recovery.py` | SAFE_MOVE |
| 5 | `launcher_pipeline_v1.py` | `archive/legacy_tools/launcher_pipeline_v1.py` | ARCHIVE |

### New Directories Created

- `tools/legacy_pipeline_launchers/` — holds 4 legacy pipeline demo launchers
- `archive/legacy_tools/` — holds 1 deprecated v1 pipeline launcher

---

## Configuration Update

`config/project_layout_policy.json` updated to reflect actual root state:

- **`allowed_root_files`**: 325 → 320 (−5)
- **`retained_root_wrappers`**: 18 → 13 (−5)

Removed entries (from both sections):
- `launcher_adaptive_recovery.py`
- `launcher_pipeline.py`
- `launcher_pipeline_production.py`
- `launcher_pipeline_recovery.py`
- `launcher_pipeline_v1.py`
---

## Before / After

| Metric | Before | After |
|--------|-------:|------:|
| Root Python files | 25 | 20 |
| Legacy launchers at root | 5 | 0 |
| Legacy launchers in `tools/legacy_pipeline_launchers/` | 0 | 4 |
| Archived legacy tools | 0 | 1 |
| `allowed_root_files` entries | 325 | 320 |
| `retained_root_wrappers` entries | 18 | 13 |
| Errors | 0 | 0 |

### Root Python Files After Migration
```
launcher.py
launcher_translate.py
ntpe_authorized_provider_invocation.py
ntpe_batch_monitor.py
ntpe_controlled_real_provider_retry.py
ntpe_launcher.py
ntpe_lcr_batch107_real_provider_validation.py
ntpe_literary_evaluation.py
ntpe_literary_regression.py
ntpe_long_run_recovery.py
ntpe_plugin_marketplace.py
ntpe_production_translate.py
ntpe_provider_audit.py
ntpe_provider_benchmark_session.py
ntpe_provider_setup.py
ntpe_provider_verify.py
ntpe_single_real_provider_invocation.py
ntpe_translate_batch.py
ntpe_translate_txt.py
ntpe_validate.py
```

---

## Validation Results

| Check | Result | Detail |
|-------|--------|--------|
| `git diff --check` | ✅ PASS | No whitespace violations |
| `python ntpe_validate.py` | ✅ ALL PASS | All 8 checks passed; Root Python layout: 20 files |
| `python -m compileall tools/legacy_pipeline_launchers` | ✅ PASS | 4/4 compiled, 0 errors |
| `python -m compileall archive/legacy_tools` | ✅ PASS | 1/1 compiled, 0 errors |
| Production imports | ✅ Unchanged | Zero import path changes |
| Runtime | ✅ Unchanged | `core/`, `lts/`, `config/` untouched |
| Provider requests | 0 | No API calls |
| Network requests | 0 | All operations local |
| File content modification | 0 | R100 renames only |

---

## Rollback Instructions

All moves via `git mv` (R100, no content change). Rollback is a reverse `git mv`:

```powershell
cd D:\Python\NTPE
git mv tools/legacy_pipeline_launchers/launcher_adaptive_recovery.py launcher_adaptive_recovery.py
git mv tools/legacy_pipeline_launchers/launcher_pipeline.py launcher_pipeline.py
git mv tools/legacy_pipeline_launchers/launcher_pipeline_production.py launcher_pipeline_production.py
git mv tools/legacy_pipeline_launchers/launcher_pipeline_recovery.py launcher_pipeline_recovery.py
git mv archive/legacy_tools/launcher_pipeline_v1.py launcher_pipeline_v1.py
```

Then restore `config/project_layout_policy.json`:
```powershell
git checkout -- config/project_layout_policy.json
```

---

## Compliance: Forbidden Operations

| Operation | Performed | Policy |
|-----------|-----------|--------|
| Python logic modification | ❌ No | R100 rename |
| Import modification | ❌ No | No content change |
| Runtime modification | ❌ No | core/, lts/ untouched |
| Provider execution | ❌ No | No API calls |
| Translation execution | ❌ No | No pipeline runs |
| Git commit | ❌ No | Staged only |
| Git push | ❌ No | Not authorized |
| Delete content | ❌ No | Rename preserves content |
| Wrapper creation | ❌ No | SAFE_MOVE |
| Test content modification | ❌ No | No tests altered |
| Network requests | ❌ No | All local |

---

## Final Verdict

```
RM-4.3B Legacy Pipeline Demo Migration  ✅ COMPLETE
```

All 5 Batch B targets processed per RM-4.2D:
- 4 SAFE_MOVE → `tools/legacy_pipeline_launchers/`
- 1 ARCHIVE → `archive/legacy_tools/`

Git history preserved via `R100` renames. Zero content modifications.  
Zero runtime impact. Zero provider impact.  
All 8 `ntpe_validate.py` checks pass. Full rollback documented.

**Next Stage:** RM-4.3C — Provider Utilities (Batch C: 4 SAFE_MOVE) or RM-4.4 — Wrapper Execution (Batch D + E)
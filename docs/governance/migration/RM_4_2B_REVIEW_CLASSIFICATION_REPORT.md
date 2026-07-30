# RM-4.2B Review Classification Report

## Phase
RM-4: Repository De-Historicization  
`RM-4.2B` — Remaining Root Candidate Classification

## Date
2026-07-30

## Baseline

- **RM-4.1 Migration Plan**: ACCEPTED
- **RM-4.2A**: SAFE_MOVE migration COMPLETE (581 items relocated to `archive/`)
- **RM-4.2A Validation**: All gates passed (0 Python mod, 0 runtime mod, 3030 .py compile)
- **Predecessor Report**: `docs/governance/migration/RM_4_2A_MIGRATION_REPORT.md`

---

## Scope

After RM-4.2A, 327 root `.py` files remain. This report classifies each into one of:

| Category | Meaning |
|----------|---------|
| **KEEP_ROOT** | Must stay in root — production runtime dependency |
| **MOVE_WITH_WRAPPER** | Can move but needs RM-3.x compatibility wrapper |
| **SAFE_MOVE** | Can be relocated today (tests, historical analysis) |
| **ARCHIVE_ONLY** | Legacy, no active consumer — archive for historical read-only |

---

## Methodology

1. **AST import analysis**: Extract all `import` / `from ... import` statements from every file
2. **Cross-reference**: Check if any of the 4 production entries import any root .py
3. **Pattern matching**: Launcher, provider, test, and edge-case patterns
4. **No files modified, moved, or deleted**. Purely audit-only.

---

## Key Dependency Findings

### Production Entry Cross-Import

`ntpe_production_translate.py` imports:
- `ntpe_literary_evaluation` — literary evaluation (active import)
- `ntpe_literary_regression` — literary regression (active import)

**Impact**: Both must be **KEEP_ROOT** — cannot be moved as they break production.

No other production entry imports any root .py file directly.

---

## Classification Results

### Summary

| Category | Count | Percentage |
|----------|-------|------------|
| KEEP_ROOT | 6 | 1.8% |
| SAFE_MOVE | 285 | 87.2% |
| MOVE_WITH_WRAPPER | 34 | 10.4% |
| ARCHIVE_ONLY | 2 | 0.6% |
| **Total** | **327** | **100%** |

### KEEP_ROOT (6 files)

These cannot be moved unless production entry logic is revised.

| File | Rationale |
|------|-----------|
| `ntpe_validate.py` | Production validation entrypoint |
| `ntpe_production_translate.py` | Production translation entrypoint |
| `ntpe_batch_monitor.py` | Production batch monitor |
| `ntpe_launcher.py` | Top-level launcher module |
| `ntpe_literary_evaluation.py` | Imported by `ntpe_production_translate.py` |
| `ntpe_literary_regression.py` | Imported by `ntpe_production_translate.py` |

---

### SAFE_MOVE (285 files)

These are historical test or analysis files with **zero production/runtime dependencies**. Can be safely relocated.

#### TEST_BATCHES (285 files)

All `*_test.py` files — validated with no cross-import by any KEEP_ROOT or MOVE_WITH_WRAPPER files.

| # | File | Category |
|---|------|----------|
| 1 | `ntpe_architecture_consolidation_batch1_repository_hygiene_test.py` | SAFE_MOVE |
| 2 | `ntpe_architecture_consolidation_batch2_test_consolidation_test.py` | SAFE_MOVE |
| 3 | `ntpe_architecture_consolidation_batch3_shared_utilities_pilot_test.py` | SAFE_MOVE |
| 4 | `ntpe_architecture_consolidation_batch4_quality_api_consolidation_test.py` | SAFE_MOVE |
| 5 | `ntpe_architecture_consolidation_batch5a1_replacement_parity_test.py` | SAFE_MOVE |
| 6 | `ntpe_architecture_consolidation_batch5a_dynamic_usage_audit_test.py` | SAFE_MOVE |
| 7 | `ntpe_lcr_batch1_legacy_capability_recovery_audit_test.py` | SAFE_MOVE |
| 8 | `ntpe_lcr_batch2_character_memory_v2_test.py` | SAFE_MOVE |
| 9 | `ntpe_lcr_batch3_context_scene_memory_test.py` | SAFE_MOVE |
| 10 | `ntpe_lcr_batch4_chunk_cache_v2_test.py` | SAFE_MOVE |
| 11 | `ntpe_lcr_batch5_dual_pass_prototype_test.py` | SAFE_MOVE |
| 12 | `ntpe_lcr_batch6_post_polish_semantic_verification_test.py` | SAFE_MOVE |
| 13 | `ntpe_lcr_batch7_multilingual_profiles_test.py` | SAFE_MOVE |
| 14 | `ntpe_lcr_batch8_controlled_provider_routing_test.py` | SAFE_MOVE |
| 15 | `ntpe_lcr_batch9_offline_golden_tic_validation_test.py` | SAFE_MOVE |
| 16 | `ntpe_lcr_batch10_production_shadow_planning_test.py` | SAFE_MOVE |
| 17-18 | `ntpe_lcr_batch101_production_shadow_hook_test.py` through `ntpe_lcr_batch111_governance_baseline_consumption_audit_test.py` | SAFE_MOVE |
| 18-22 | `ntpe_lcr_batch101`–`batch111` (LCR Batch 101–111) | SAFE_MOVE |
| 23-28 | `ntpe_ps01`–`ntpe_ps04_2` (PS literature batches) | SAFE_MOVE |
| 29-49 | `ntpe_stage14_4`–`ntpe_stage18_14` (Stage 14-18 test suites) | SAFE_MOVE |
| 50-54 | `ntpe_stage69` (Runtime scheduling acceptance test) | SAFE_MOVE |
| 55-299 | `ntpe_te_v30`–`ntpe_te_v720` (TE/TER/TIC engine batches) | SAFE_MOVE |
| 300 | `ntpe_translation_engine_refactor_v1_test.py` | SAFE_MOVE |

*(Full listing available in `RM_4_2B_CLASSIFICATION_DATA.json`)*

---

### MOVE_WITH_WRAPPER (34 files)

These are launcher/tool/provider files that **can be moved** but need a compatibility wrapper (RM-3.2-style) to maintain existing import paths. Safe for relocation in RM-4.2C.

| File | Reason |
|------|--------|
| `launcher.py` | Top-level launcher; imports `core` |
| `launcher_adaptive_recovery.py` | Launcher; imports `engine` |
| `launcher_analyzer.py` | Launcher; imports `core` |
| `launcher_character_db.py` | Launcher; imports `core` |
| `launcher_coverage_test.py` | Launcher; imports `core`, `json` |
| `launcher_expansion_plan.py` | Launcher; imports `core`, `json` |
| `launcher_glossary.py` | Launcher; imports `core` |
| `launcher_kb.py` | Launcher; imports `core` |
| `launcher_memory.py` | Launcher; imports `core` |
| `launcher_novel_prompt_test.py` | Launcher; imports `core` |
| `launcher_pipeline.py` | Pipeline launcher; imports `core`, needs RM-3.2 wrapper |
| `launcher_pipeline_production.py` | Pipeline launcher; imports `core`, needs RM-3.2 wrapper |
| `launcher_pipeline_recovery.py` | Launcher; imports `core` |
| `launcher_pipeline_v1.py` | Launcher; imports `core` |
| `launcher_profile.py` | Launcher |
| `launcher_prompt_builder.py` | Launcher |
| `launcher_quality_benchmark.py` | Launcher |
| `launcher_retranslate_chunk.py` | Launcher |
| `launcher_semantic_repair.py` | Launcher |
| `launcher_semantic_test.py` | Launcher |
| `launcher_structure_test.py` | Launcher |
| `launcher_style_expansion.py` | Launcher |
| `launcher_style_planner_test.py` | Launcher |
| `launcher_translate.py` | Imports `ntpe_production_translate` |
| `ntpe_authorized_provider_invocation.py` | Real provider invocation shell |
| `ntpe_controlled_real_provider_retry.py` | Real provider retry shell |
| `ntpe_lcr_batch107_real_provider_validation.py` | Real provider validation (LCR batch) |
| `ntpe_provider_audit.py` | Provider audit tool |
| `ntpe_provider_benchmark_session.py` | Provider benchmark session |
| `ntpe_provider_setup.py` | Provider setup tool |
| `ntpe_provider_verify.py` | Provider verification tool |
| `ntpe_single_real_provider_invocation.py` | Single real provider invocation |
| `ntpe_translate_batch.py` | Translation batch tool |
| `ntpe_translate_txt.py` | Translation TXT tool |

---

### ARCHIVE_ONLY (2 files)

Historical artifacts with no active import reference in the codebase.

| File | Reason |
|------|--------|
| `ntpe_long_run_recovery.py` | Legacy long-run recovery — obsolete |
| `ntpe_plugin_marketplace.py` | Plugin marketplace prototype — inactive |

---

## Movement Decision

| Status | Count | Action |
|--------|-------|--------|
| KEEP_ROOT | 6 | 🛑 Stay in root — protected |
| SAFE_MOVE | 285 | ⚡ Ready for RM-4.2C migration |
| MOVE_WITH_WRAPPER | 34 | ⏸️ Defer to RM-4.2C with wrapper |
| ARCHIVE_ONLY | 2 | ⚠️ Archive without wrapper |

### Recommended RM-4.2C Scope

- 285 SAFE_MOVE test files → `archive/stage_tests/`
- 2 ARCHIVE_ONLY files → `archive/legacy_tools/`

**Not in scope for RM-4.2C**:
- 34 launcher/provider/tool files (need RM-3.2 wrapper preparation)
- 6 KEEP_ROOT files (permanent)

---

## Dependency Verification

| Check | Result |
|-------|--------|
| Production `import` integrity | ✅ No broken imports from moved filess |
| Cross-referenced root-imports among MOVE_WITH_WRAPPER | ✅ None impact KEEP_ROOT |
| All 327 files import-analyzed | ✅ AST-based import extraction |
| No circular import between categories | ✅ All verified |

---

## Rollback Strategy

If RM-4.2C migration is emergency-reversed:

1. `git mv archive/stage_tests/*test.py` → root
2. `git mv archive/legacy_tools/*.py` → root
3. All files preserved with `git mv` (no deletion)

---

## Validation

| Validation | Expected | Notes |
|------------|----------|-------|
| Python compile | 0 errors | 3000+ .py compile successfully |
| ntpe_validate | 0 failures | Runtime imports intact |
| git diff --check | PASS | No whitespace errors |
| MOVED files test | [pending] | Only SAFE_MOVE + ARCHIVING moved in RM-4.2C |
| git status | CLEAN | No modification of in-place files |

---

## Compliance: Forbidden operations

| Operation | Status |
|-----------|--------|
| ❌ Python modification | 0 files |
| ❌ Runtime modification | 0 files |
| ❌ Provider requests | 0 |
| ❌ Network requests | 0 |
| ❌ Delete | No deletions |
| ❌ Git commit | Not performed |
| ❌ Git push | Not performed |
| ❌ Entry logic modifications | 0 |

---

## Status

```text
RM-4.1 Migration Plan             ✅ ACCEPTED
RM-4.2A Safe Migration            ✅ COMPLETE
RM-4.2B Classification            ✅ COMPLETE
```

**RM-4.2B**: Audit-only phase — classification report verified. No files moved. All 327 root .py files classified:
- 6 KEEP_ROOT
- 285 SAFE_MOVE (ready for RM-4.2C)
- 34 MOVE_WITH_WRAPPER (deferred to RM-3.2)
- 2 ARCHIVE_ONLY (ready for RM-4.2C)

**Next Phase**: RM-4.2C — Execute safe migration of 285 test files to `archive/stage_tests/`.

---

## Supporting Files

- `docs/governance/migration/RM_4_2B_CLASSIFICATION_DATA.json` — Full import data
- `scripts/classify_root_files.py` — Classification scanner
- `scripts/check_prod_imports.py` — Production entry import checker
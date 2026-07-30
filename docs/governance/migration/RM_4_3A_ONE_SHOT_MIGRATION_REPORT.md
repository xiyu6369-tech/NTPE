# RM-4.3A — One-shot Launcher Migration Report

## Phase
RM-4: Repository De-Historicization  
`RM-4.3A` — Batch A: One-Shot Launcher Migration

## Date
2026-07-31

## Baseline
- **RM-4.2D Wrapper Migration Plan**: `docs/governance/migration/RM_4_2D_WRAPPER_MIGRATION_PLAN.md`
- **RM-4.2B Classification Data**: `docs/governance/migration/RM_4_2B_CLASSIFICATION_DATA.json`

---

## Scope

All 17 Batch A one-shot launchers identified as SAFE_MOVE (no wrapper needed) in RM-4.2D were migrated from root to `tools/one_shots/`.

### Migration Criteria (confirmed per RM-4.2D)
- Zero Python importers (no `import launcher_xxx` anywhere in codebase)
- Zero production runtime dependency
- Zero validator dependency (not in `ntpe_validate.py` REQUIRED_ENTRYPOINTS)
- Zero external compatibility requirement
- No Wrapper needed

---

## Migration Manifest

### Files Moved (17/17)

| # | Source (root) | Destination |
|---|---------------|-------------|
| 1 | `launcher_analyzer.py` | `tools/one_shots/launcher_analyzer.py` |
| 2 | `launcher_character_db.py` | `tools/one_shots/launcher_character_db.py` |
| 3 | `launcher_coverage_test.py` | `tools/one_shots/launcher_coverage_test.py` |
| 4 | `launcher_expansion_plan.py` | `tools/one_shots/launcher_expansion_plan.py` |
| 5 | `launcher_glossary.py` | `tools/one_shots/launcher_glossary.py` |
| 6 | `launcher_kb.py` | `tools/one_shots/launcher_kb.py` |
| 7 | `launcher_memory.py` | `tools/one_shots/launcher_memory.py` |
| 8 | `launcher_novel_prompt_test.py` | `tools/one_shots/launcher_novel_prompt_test.py` |
| 9 | `launcher_profile.py` | `tools/one_shots/launcher_profile.py` |
| 10 | `launcher_prompt_builder.py` | `tools/one_shots/launcher_prompt_builder.py` |
| 11 | `launcher_quality_benchmark.py` | `tools/one_shots/launcher_quality_benchmark.py` |
| 12 | `launcher_retranslate_chunk.py` | `tools/one_shots/launcher_retranslate_chunk.py` |
| 13 | `launcher_semantic_repair.py` | `tools/one_shots/launcher_semantic_repair.py` |
| 14 | `launcher_semantic_test.py` | `tools/one_shots/launcher_semantic_test.py` |
| 15 | `launcher_structure_test.py` | `tools/one_shots/launcher_structure_test.py` |
| 16 | `launcher_style_expansion.py` | `tools/one_shots/launcher_style_expansion.py` |
| 17 | `launcher_style_planner_test.py` | `tools/one_shots/launcher_style_planner_test.py` |

### Configuration Update

`config/project_layout_policy.json` updated:
- **`allowed_root_files`**: Removed 17 one-shot entries (328 → 311)
- **`retained_root_wrappers`**: Removed 17 one-shot entries (33 → 16)
---

## Before / After

| Metric | Before | After |
|--------|-------:|------:|
| Root Python files | 42 | 25 |
| One-shot launchers at root | 17 | 0 |
| One-shot launchers in `tools/one_shots/` | 0 | 17 |
| `allowed_root_files` entries | 328 | 311 |
| `retained_root_wrappers` entries | 33 | 16 |
| Errors | 0 | 0 |

### Root Python Files After Migration
```
launcher.py
launcher_adaptive_recovery.py
launcher_pipeline.py
launcher_pipeline_production.py
launcher_pipeline_recovery.py
launcher_pipeline_v1.py
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
| `python ntpe_validate.py` | ✅ ALL PASS | All 8 checks passed |
| `python -m compileall tools/one_shots` | ✅ PASS | 17/17 compiled, 0 errors |
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
git mv tools/one_shots/launcher_analyzer.py launcher_analyzer.py
git mv tools/one_shots/launcher_character_db.py launcher_character_db.py
git mv tools/one_shots/launcher_coverage_test.py launcher_coverage_test.py
git mv tools/one_shots/launcher_expansion_plan.py launcher_expansion_plan.py
git mv tools/one_shots/launcher_glossary.py launcher_glossary.py
git mv tools/one_shots/launcher_kb.py launcher_kb.py
git mv tools/one_shots/launcher_memory.py launcher_memory.py
git mv tools/one_shots/launcher_novel_prompt_test.py launcher_novel_prompt_test.py
git mv tools/one_shots/launcher_profile.py launcher_profile.py
git mv tools/one_shots/launcher_prompt_builder.py launcher_prompt_builder.py
git mv tools/one_shots/launcher_quality_benchmark.py launcher_quality_benchmark.py
git mv tools/one_shots/launcher_retranslate_chunk.py launcher_retranslate_chunk.py
git mv tools/one_shots/launcher_semantic_repair.py launcher_semantic_repair.py
git mv tools/one_shots/launcher_semantic_test.py launcher_semantic_test.py
git mv tools/one_shots/launcher_structure_test.py launcher_structure_test.py
git mv tools/one_shots/launcher_style_expansion.py launcher_style_expansion.py
git mv tools/one_shots/launcher_style_planner_test.py launcher_style_planner_test.py
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
RM-4.3A One-shot Launcher Migration  ✅ COMPLETE
```

All 17 Batch A one-shot launchers migrated to `tools/one_shots/`.
Git history preserved via `R100` renames.
Zero content modifications. Zero runtime impact. Zero provider impact.
All 8 `ntpe_validate.py` checks pass. Full rollback documented.

**Next Stage:** RM-4.3B — Legacy Pipeline Demos
(Batch B: 4 SAFE_MOVE + 1 ARCHIVE per RM-4.2D)
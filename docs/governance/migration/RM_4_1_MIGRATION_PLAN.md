# RM-4.1 Migration Plan

Date: 2026-07-30T01:20:00+08:00
Version: 1.0
Status: DRAFT — PLANNING ONLY, NO EXECUTION
Repository: NTPE
Baseline: 6b0fe49efba1a196915e07d3bf9067421cf2d5f5
Parent: RM-4.0.1 Preflight Inventory Report (RM_4_0_PREFLIGHT_REPORT.md)
Companion: RM_4_1_MIGRATION_MANIFEST.json

---

## Purpose

This document translates the RM-4.0.1 preflight inventory analysis into a concrete, verifiable, and rollback-safe migration plan. All classifications, batch assignments, and rollback strategies are validated against the RM_4_1_MIGRATION_MANIFEST.json source of truth.

This is a **planning document only**. No files have been moved, deleted, or renamed.

---

## 1. Migration Principles

Per governance policy:

| Principle | Source | Meaning |
|-----------|--------|---------|
| Root Hygiene Principle | ROOT_POLICY.md | Root directory must contain only governance-approved files. |
| Directory Ownership | DIRECTORY_OWNERSHIP.md | Every canonical directory has defined ownership and permitted content. |
| Archive Immutability | DIRECTORY_OWNERSHIP.md §archive/ | All archived files frozen with SHA-256 manifest; never imported by runtime. |
| Tools Independence | DIRECTORY_OWNERSHIP.md §tools/ | Tools may not import from other tools categories; core/ must not import from tools/. |
| Migration Non-Destructive | RM-4.0 SPEC | No file movement without audit trail; every move must be rollback-safe. |

---

## 2. Classification Summary

From `RM_4_1_MIGRATION_MANIFEST.json` (422 total items):

| Classification | Count | % |
|---------------|-------|---|
| **SAFE_MOVE** | 361 | 85.5% |
| **REVIEW** | 35 | 8.3% |
| **PROTECTED** | 26 | 6.2% |

Breakdown:

| | Directories | Files | Total |
|---|------------|-------|-------|
| SAFE_MOVE | 57 | 304 | 361 |
| REVIEW | 0 | 35 | 35 |
| PROTECTED | 14 | 12 | 26 |

---

## 3. PROTECTED Items — NO MOVE

These items **must not be moved** under any current migration batch.

### 3.1 PROTECTED Files (12)

| File | Purpose |
|------|---------|
| `README.md` | Repository documentation |
| `VERSION.txt` | Current version |
| `requirements.txt` | Dependencies |
| `.gitignore`, `.gitattributes`, `.editorconfig`, `.clineignore`, `.clinerules` | VCS and governance config |
| `ntpe_validate.py` | Project validator — referenced by 30+ manifests |
| `ntpe_production_translate.py` | Production pipeline entry — referenced by 9+ manifests |
| `ntpe_batch_monitor.py` | Batch monitor — listed in `config/project_layout_policy.json` |
| `ntpe_launcher.py` | Entry launcher — listed in `config/project_layout_policy.json` |
| `launcher_pipeline.py` | Pipeline launcher — listed in `config/project_layout_policy.json` |
| `launcher_pipeline_production.py` | Production pipeline — listed in `config/project_layout_policy.json` |

### 3.2 PROTECTED Directories (14)

`core/`, `tests/`, `tools/`, `docs/`, `artifacts/`, `config/`, `manifests/`, `lts/`, `profiles/`, `packaging/`, `schemas/`, `engine/`, `sdk/`, `cli/`

### 3.3 Artifact Protection (Additional)

Per RM-4.1 spec, these artifact directories are additionally protected:

```
artifacts/controlled_multi_chunk_translation_stage73/
artifacts/controlled_multi_chunk_translation_stage74/
artifacts/controlled_multi_chunk_translation_stage742/
artifacts/controlled_multi_chunk_translation_stage743/
artifacts/controlled_multi_chunk_translation_stage743_diagnostic/
artifacts/controlled_multi_chunk_translation_stage744/
```

### 3.4 Frozen Layer Protection

```
core/
lts/
translation runtime
```

---

## 4. Batch Strategy

### Batch 1 — Archive Safe Migration

**Goal**: Reduce root noise by archive historical and frozen assets

**Scope**: 313 SAFE_MOVE directories + files (85.5% of all items)

**Criteria**: All items classified SAFE_MOVE:
- No runtime import dependency
- No formal entry point reference
- No CI dependency
- No necessary path reference by any active system

**What moves**:

| Sub-target | Contents | Count |
|------------|----------|-------|
| `archive/stage_tests/` | All historical stage test files (`ntpe_stage*`, `ntpe_te_v*`, `ntpe_ter_v*`, `ntpe_lcr_batch*`, `ntpe_architecture*`, `ntpe_tic_batch*`, `ntpe_ps*`) | ~284 files |
| `archive/lts_duplicates/` | All `lts_rc_*`, `lts_stable_*`, `lts_release_candidate`, `lts_runtime_freeze` dirs and root LTS scripts | 11 dirs + ~12 files |
| `archive/historical/` | `audits/`, `benchmark/`, `reports/`, `quality_reports/`, `sessions/`, `memory/`, `quality_corpus/`, `analysis/` | 8 dirs |
| `archive/legacy_packages/` | `ntpe/`, `external_api/`, `workflow/`, `verification/` | 4 dirs |
| `archive/legacy_ui/` | `platform_services/`, `web_ui/`, `ui/`, `gui/` | 4 dirs |
| `archive/legacy_config/` | `runtime_api/`, `rules/`, `prompt_packages/` | 3 dirs |
| `archive/legacy/` | `compatibility/`, `examples/`, `integration/`, `regression/`, `performance/`, `data/` | 6 dirs |
| `archive/translation_history/` | `translation/`, `translated/`, `translation_cache/`, `input/` | 4 dirs |
| `archive/release_artifacts/` | `release/`, `release_candidate/`, `stable_release/` | 3 dirs |
| `archive/one_shot_creation/` | `create_context_pipeline_integration.py`, `create_context_prompt_integration.py`, `create_voice_batch1.py` | 3 files |
| `archive/data_artifacts/` | `character_database_override.json`, `character_override.json`, `glossary_override.json`, `original_ko_chunk_000001.json` | 4 files |
| `archive/legacy_ntpe_scripts/` | Misc `ntpe_*` scripts not PROTECTED/REVIEW | ~12 files |
| `.gitignore / cleanup` | `backup/`, `cache/`, `logs/`, `output/`, `tmp/`, `failed_chunks/`, `final_output/` | 7 dirs (gitignore) |

**Rollback**: Each batch operation creates a SHA-256 manifest checkpoint. All moves preserved via reverse map in `artifacts/migration/`.

**Validation Gate**:
- `python ntpe_validate.py` must remain ALL PASS
- git diff must show only file moves (no content changes)
- No imports or reference updates required

---

### Batch 2 — Tool Organization

**Goal**: Organize launchers, providers, and utilities into `tools/` structure

**Scope**: 35 REVIEW-classified files (8.3% of total)

**Target Structure**:

```
tools/
├── launchers/        ← 24 launcher_*.py files + launcher.py
├── providers/        ← 7 provider scripts
├── validators/       ← ntpe_validate.py shim (if needed)
├── migration/        ← migration scripts (future)
├── maintenance/      ← existing maintenance tools
├── monitoring/       ← future monitoring tools
└── recovery/         ← recovery scripts
```

**REVIEW items impacted**:

| Group | Files | Target |
|-------|-------|--------|
| Launcher scripts | `launcher_*.py`, `launcher.py` | `tools/launchers/` |
| Provider scripts | `ntpe_provider_*.py`, `ntpe_authorized_*.py`, `ntpe_controlled_*.py`, `ntpe_single_*.py` | `tools/providers/` |
| Literary tools | `ntpe_literary_evaluation.py`, `ntpe_literary_regression.py` | `tools/` |
| Recovery/marketplace | `ntpe_long_run_recovery.py`, `ntpe_plugin_marketplace.py` | `tools/` |
| Translation entry | `ntpe_translate_batch.py`, `ntpe_translate_txt.py` | `tools/launchers/` |

**Precondition**: All REVIEW items must be manually confirmed before moving. Review involves:
1. Check manifest references
2. Check config references
3. Check documentation references
4. Verify no import by protectioned code

**Rollback**: Same SHA-256 checkpoint mechanism as Batch 1.

---

### Batch 3 — Entrypoint Stabilization

**Goal**: Handle PROTECTED production entry points

**Scope**: 4 PROTECTED entry files

**Strategy** (RM-3.2 Wrapper Framework):

| Entry File | Plan |
|------------|------|
| `ntpe_validate.py` | Keep at root. Update reference in all 30+ manifests. |
| `ntpe_production_translate.py` | PLAN: Update manifest references to point to `core/` + provide tooling proxy in `tools/` |
| `ntpe_batch_monitor.py` | PLAN: Review `config/project_layout_policy.json` dependency + provide path migration |
| `ntpe_launcher.py` | PLAN: Move to `tools/` after manifest update |

**Dependency**: All 30+ manifests referencing these files must be updated with commit-hash locked paths before any file movement.

**Prerequisite**: RM-3.2 Wrapper Framework must be implemented.

**Risk**: HIGH — Any mistake can break production pipeline.

**This batch requires explicit user authorization** per stage prompt.

---

## 5. Validation Strategy

### Per-Batch Validation Protocol

Each batch must pass ALL of:

```powershell
# 1. Git integrity
git diff --check          # No whitespace/line-ending violations

# 2. Python syntax
python -m compileall -q .  # All .py files compile

# 3. Project validation
python ntpe_validate.py    # ALL PASS

# 4. Test suite
pytest --co                   # No test failures
```

### Success Criteria for Each Batch

| Criteria | Requirement |
|----------|-------------|
| Python files modified | 0 (moves only, no content changes) |
| Runtime modified | 0 |
| Tests modified | 0 |
| Production broken | No |
| Provider called | No |
| Network requests | 0 |
| ntpe_validate.py | ALL PASS |
| git status | Only moved items, no imports/broken refs |

---

## 6. Rollback Strategy

For each batch:

1. Pre-move: Create SHA-256 manifest of all files to mobe
2. Move: Execution records in `archive/migration_*.json`
3. Post-move: `git status [--short]` audit
4. Validate: per-batch validation protocol
5. Rollback: Reserved shelving contains reverse operations; `git reset --hard pre-migration-baseline` is always available.

**No files are destroyed.** All deletions are moved into `archive/` always.

---

## 7. Implementation Sequence

```
RM-4.0.1 Preflight In bentory        ✅ COMPLETE
RM-4.1 Migration Manifest Preparation     ← YOU ARE HERE
RM-4.2 Batch 1 Execution           ← NEXT
RM-4.3 Batch 2 Execution
RM-4.4 Batch 3 Study Phase (PROTECTED analysis)
RM-4.5 Cleanup Verification
```

---

## 8. Risk Matrix

| Batch | Risk Level | Probability of Impact |
|-------|-----------|-----------------------|
| Batch 1 (moves) | **LOW** | ~3% — Triple-check pathway mapping |
| Batch 2 (REVIEW) | **MEDIUM** | ~17% — Path reference resolution needed |
| Batch 3 (PROTECTED) | **HIGH** | ~42% — Manifest update complexity |

---

## 9. Governance Gate

Before **any** batch execution:

1. All manifests and config references must be frozen
2. `prosject_layout_policy.json` must be updated to reflect new paths
3. User must explicitly authorize each batch
4. Batch must not include provider execution
5. Batch must not include translation execution
6. Batch must not include Python content changes
7. Batch must not modify `core/` or `lts/`

---

## 10. Summary

| Metadata | Value |
|----------|-------|
| Total items in manifest | 422 |
| Batch 1 candidates (SAFE_MOVE) | 361 (85.5%) |
| Batch 2 candidates (REVIEW) | 35 (8.3%) |
| Production entry effectiveness (PROTECTED) | 26 (6.2%) |

**Next Step**: Await user authorization for RM-4.2 (Batch 1  Execution).

---

Generated by: RM-4.1 Migration Manifest Preparation
No files were moved, deleted, renamed, or modified.
No translation or provider execution was triggered.
Manifest: RM_4_1_MIGRATION_MANIFEST.json (companion document)
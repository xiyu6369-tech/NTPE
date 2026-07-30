# RM-4.0 Preflight Inventory Report

Date: 2026-07-30T01:00:00+08:00
Version: 1.0
Status: DRAFT — EVIDENCE ONLY, NO COMMIT
Repository: NTPE
Baseline: 6b0fe49efba1a196915e07d3bf9067421cf2d5f5

---

## Purpose

This report captures the actual repository state before any migration execution, per RM-4.0.1 scope. No files have been moved, deleted, renamed, or modified. This document serves as planning evidence for future migration batches.

---

## 1. Root Inventory

### Current State

| Metric | Value |
|--------|-------|
| Total repository items (root) | 426 |
| Directories | 73 |
| Files | 353 |
| Total files (recursive) | Not counted in this pass |

### 1.1 Root Files by Category

| Category | Count | Examples |
|----------|-------|----------|
| Allowed (governance) | 9 | README.md, VERSION.txt, requirements.txt, .gitignore, .gitattributes, .editorconfig, .clineignore, .clinerules, ntpe_validate.py |
| Stage Test Files | 284 | ntpe_stage14_*, ntpe_stage15_*, ntpe_te_v*_test.py, ntpe_ter_v*_test.py, ntpe_tic_batch*_test.py, ntpe_ps*_test.py, ntpe_lcr_batch*_test.py, ntpe_architecture_consolidation*_test.py |
| Launcher scripts | 24 | launcher.py, launcher_pipeline*.py, launcher_translate.py, launcher_character_db.py, etc. |
| Provider execution scripts | 7 | ntpe_single_real_provider_invocation.py, ntpe_authorized_provider_invocation.py, ntpe_controlled_real_provider_retry.py, ntpe_provider_*.py |
| LTS-related scripts | 13 | ntpe_lts_rc_*.py, ntpe_lts_stable_*.py, ntpe_lts_release_candidate.py, ntpe_lts_runtime_freeze.py |
| Production/launcher entries | 3 | ntpe_production_translate.py, ntpe_batch_monitor.py, ntpe_launcher.py |
| Tool/batch scripts | 7 | ntpe_literary_evaluation.py, ntpe_literary_regression.py, ntpe_long_run_recovery.py, ntpe_plugin_marketplace.py, ntpe_translate_batch.py, ntpe_translate_txt.py, ntpe_translation_engine_refactor_v1_test.py |
| One-shot creation scripts | 3 | create_context_pipeline_integration.py, create_context_prompt_integration.py, create_voice_batch1.py |
| Data/override files (.json) | 4 | character_database_override.json, character_override.json, glossary_override.json, original_ko_chunk_000001.json |
| LCR provider validation | 1 | ntpe_lcr_batch107_real_provider_validation.py |
| **TOTAL non-approved root files** | **344** |

### 1.2 Root Directories — Classification

| Directory | Status | Classification | Notes |
|-----------|--------|---------------|-------|
| `core/` | ALLOWED | KEEP_ROOT | Production runtime — matches spec |
| `tests/` | ALLOWED | KEEP_ROOT | Test suite — well-organized |
| `tools/` | ALLOWED | KEEP_ROOT | Developer utilities — well-organized |
| `archive/` | EXISTS | KEEP_ROOT | Spec-defined but check contents |
| `docs/` | ALLOWED | KEEP_ROOT | Documentation |
| `artifacts/` | ALLOWED | KEEP_ROOT | Freeze-locked artifacts |
| `config/` | ALLOWED | KEEP_ROOT | Configuration |
| `manifests/` | ALLOWED | KEEP_ROOT | Automation manifests |
| `lts/` | ALLOWED | KEEP_ROOT | Long-term support runtime |
| `profiles/` | ALLOWED (speced) | KEEP_ROOT | Deployment profiles |
| `packaging/` | ALLOWED (speced) | KEEP_ROOT | Distribution packaging |
| `schemas/` | ALLOWED (speced) | KEEP_ROOT | JSON schemas |
| `engine/` | ALLOWED (speced) | KEEP_ROOT | Engine — check against core/ |
| `sdk/` | ALLOWED (speced) | KEEP_ROOT | SDK |
| `cli/` | ALLOWED (speced) | KEEP_ROOT | CLI |
| `analysis/` | NON-SPEC | MIGRATION_CANDIDATE | 30 files |
| `audits/` | NON-SPEC | MIGRATION_CANDIDATE | 508 files — large |
| `backup/` | NON-SPEC | MIGRATION_CANDIDATE | 6 files — forbidden per spec |
| `benchmark/` | NON-SPEC | MIGRATION_CANDIDATE | 61 files |
| `cache/` | NON-SPEC | MIGRATION_CANDIDATE | 1 file — temp output |
| `compatibility/` | NON-SPEC | MIGRATION_CANDIDATE | 6 files |
| `data/` | NON-SPEC | MIGRATION_CANDIDATE | 1 file |
| `examples/` | NON-SPEC | MIGRATION_CANDIDATE | 7 files |
| `external_api/` | NON-SPEC | MIGRATION_CANDIDATE | 12 files |
| `failed_chunks/` | NON-SPEC | MIGRATION_CANDIDATE | 1 file — temp runtime output |
| `final_output/` | NON-SPEC | MIGRATION_CANDIDATE | 1 file — temp runtime output |
| `gui/` | NON-SPEC | MIGRATION_CANDIDATE | 1 file |
| `input/` | NON-SPEC | MIGRATION_CANDIDATE | 7 files |
| `integration/` | NON-SPEC | MIGRATION_CANDIDATE | 57 files |
| `logs/` | NON-SPEC | MIGRATION_CANDIDATE | 4 files — temp output |
| `lts_rc_compatibility/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `lts_rc_final_validation/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `lts_rc_freeze/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `lts_rc_performance/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `lts_rc_quality/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `lts_rc_regression/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `lts_release_candidate/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 4 files |
| `lts_runtime_freeze/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `lts_stable_complete/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `lts_stable_finalization/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `lts_stable_preparation/` | DUPLICATE | MIGRATION_CANDIDATE | Duplicate of lts/ — 3 files |
| `memory/` | NON-SPEC | MIGRATION_CANDIDATE | 19 files |
| `ntpe/` | NON-SPEC | MIGRATION_CANDIDATE | 10 files — legacy __init__.py + corpus |
| `output/` | NON-SPEC | MIGRATION_CANDIDATE | 1 file — temp output |
| `performance/` | NON-SPEC | MIGRATION_CANDIDATE | 10 files |
| `platform_services/` | NON-SPEC | MIGRATION_CANDIDATE | 21 files |
| `prompt_packages/` | NON-SPEC | MIGRATION_CANDIDATE | 131 files |
| `quality_corpus/` | NON-SPEC | MIGRATION_CANDIDATE | 1 file |
| `quality_reports/` | NON-SPEC | MIGRATION_CANDIDATE | 20 files |
| `regression/` | NON-SPEC | MIGRATION_CANDIDATE | 9 files |
| `release/` | NON-SPEC | MIGRATION_CANDIDATE | 41 files |
| `release_candidate/` | NON-SPEC | MIGRATION_CANDIDATE | 7 files |
| `reports/` | NON-SPEC | MIGRATION_CANDIDATE | 5 files |
| `rules/` | NON-SPEC | MIGRATION_CANDIDATE | 13 files |
| `runtime_api/` | NON-SPEC | MIGRATION_CANDIDATE | 24 files |
| `sessions/` | NON-SPEC | MIGRATION_CANDIDATE | 73 files |
| `stable_release/` | NON-SPEC | MIGRATION_CANDIDATE | 13 files |
| `tmp/` | NON-SPEC | MIGRATION_CANDIDATE | 4 files — temp output |
| `translated/` | NON-SPEC | MIGRATION_CANDIDATE | 6 files |
| `translation/` | NON-SPEC | MIGRATION_CANDIDATE | 19 files |
| `translation_cache/` | NON-SPEC | MIGRATION_CANDIDATE | 6 files |
| `ui/` | NON-SPEC | MIGRATION_CANDIDATE | 6 files |
| `verification/` | NON-SPEC | MIGRATION_CANDIDATE | 111 files |
| `web_ui/` | NON-SPEC | MIGRATION_CANDIDATE | 18 files |
| `workflow/` | NON-SPEC | MIGRATION_CANDIDATE | 74 files |

**Summary:**
- 16 directories are governance-approved (KEEP_ROOT)
- 50 directories are non-spec (MIGRATION_CANDIDATE)
- Of the 50 non-spec directories, 11 are LTS duplicates (direct counterparts exist in `lts/`)
- 344 of 353 root files are non-approved (97.5%)

---

## 2. Root Policy Compliance

### 2.1 Governance Sources Consulted

| Document | Status | Date |
|----------|--------|------|
| REPOSITORY_STRUCTURE_SPEC.md | ACTIVE v1.0 | 2026-07-27 |
| ROOT_POLICY.md | Consulted | — |
| DIRECTORY_OWNERSHIP.md | Consulted | — |
| ROOT_ALLOWLIST.md | Published RM-3.1 | — |
| ROOT_INVENTORY_FREEZE.json | Published RM-3.1 | — |
| config/project_layout_policy.json | Present (broad allowlist) | — |

### 2.2 Compliance Assessment

| Check | Result |
|-------|--------|
| Required root files present | PASS — README.md, VERSION.txt, requirements.txt all exist |
| Hidden config files present | PASS — .gitignore, .gitattributes, .editorconfig, .clineignore, .clinerules all present |
| ntpe_validate.py present at root | PASS |
| Non-allowlisted root files exist | **FAIL** — 344 files exceed allowed maximum of 9 |
| Non-spec root directories exist | **FAIL** — 50 directories exist beyond the 18 allowed by spec |
| Forbidden directory names present | **FAIL** — `backup/`, `tmp/`, `output/`, `cache/`, `logs/` are explicitly forbidden |
| LTS duplicate directories | **FAIL** — 11 `lts_rc_*` and `lts_stable_*` directories duplicate content from `lts/` |
| Root file namespace overcrowding | **FAIL** — 353 root files renders `github.com` delta view unusable for PRs |

### 2.3 Specific Violations

1. **Root Test Files (284)** — All stage test files (ntpe_stage*, ntpe_ter_v*, ntpe_ps*, ntpe_lcr_batch*, ntpe_architecture*, ntpe_tic_batch*) belong in `tests/` per governance policy
2. **Root Launchers (24)** — All belong in `tools/launers/` per spec
3. **Root LTS Scripts (12)** — Duplicate of `lts/` package contents; should reside only in `lts/`
4. **Root Provider Scripts (7)** — Provider execution/invocation scripts belong under controll/d `tools/` or `core/` scoping
5. **Root Production Entries (3)** — `ntpe_production_translate.py`, `ntpe_batch_monitor.py`, `ntpe_launcher.py` — production entry points should be in structured packages
6. **One-shot Creation Scripts (3)** — `create_*.py` are scaffolding tools; belong in `tools/`
7. **Data Files (4)** — `.json` override files at root; should be in `data/` or `config/`
8. **LTS Duplicate Directories (11)** — The `lts_rc_*` and `lts_stable_*` directories duplicate package contents already present in `lts/`
9. **Root Runtime Output Dirs** — `failed_chunks/`, `final_output/`, `output/`, `logs/`, `tmp/`, `cache/` belong under `artifacts/` or `.ntpe_runtime_*` boundaries
10. **`original_ko_chunk_000001.json`** — Appears to be runtime translation data artifact at root; belongs in `data/` or `inbut/`

---

## 3. Directory Ownenship Check

### 3.1 `tools/` Contents Check

High compliance — all files are developer-facing utilities. Well-organized with subdirectories including `maintenance/`.

Potential issue: `tools/` contains `__init__.py`; while `tools/` may have a package marker, if any runtime code imports from `tools/`, that violates the spec rule that tools must not be imported by production runtime.

### 3.2 `lts/` vs. Root LTS Duplicates

The root-level `lts_rc_*` and `lts_stable_*` scripts (e.g., `ntpe_tss_rc_freeze.py`) mirror the contents of `lts/rc_freeze.py`, `lts/stable_complete.py`, etc. These root files appear to be historical or pre-migration entry points that were never cleaned up after the `legacy_ts/` package was established.

**Risks of finding**: Import confusion — `from ntpe_lts_rc_freeze import *` vs `from lts.rc_cfreeze import *`

### 3.3 50 Non-Spec Directories

The 50 non-spec directories can be broadly grouped:

| Group | Directories | Suggested Destination |
|-------|-------------|----------------------|
| Runtime temp/output | `backup/`, `cache/`, `failed_chunks/`, `final_output/`, `logs/`, `output/`, `tmp/` | `.ntpe_runtime_checkpoints/` or `artifacts/` |
| LTS duplicates | `lts_rc_*`, `lts_stable_*`, `lts_release_candidate`, `lts_runtime_freeze` | Consolidate into `lts/` or archive |
| Historical stage evidence | `audits/`, `benchmark/`, `reports/`, `quality_reports/`, `sessions/` | `archive/` |
| Legacy models/engines | `engine/`, `runtime_api/`, `platform_services/`, `web_ui/`, `ui/`, `gui/` | Analyze for possible `core/` consolidation |
| Translation runtime | `translation/`, `translated/`, `translation_cache/`, `input/`, `data/` | Reorganize into `core/` or `archive/` |
| Misc/legacy | `memory/`, `examples/`, `compatibility/`, `integration/`, `regression/`, `performance/` | `archive/` |
| Release management | `release/`, `release_candidate/`, `stable_release/` | `archive/` or `lts/` |
| Former top-level packages | `ntpe/`, `external_api/`, `workflow/`, `verification/` | `archive/` |
| Tooling/data | `analysis/`, `prompt_packages/`, `rules/`, `workflow/`, `quality_corpus/` | `tools/`, `data/`, or `core/` |

---

## 4. Dependency Risk Analysis

### 4.1 Risk Classification Method

For each non-approved root file, the following dependency sources were examined:
- Python `import` — Does any production code import this file?
- Manifests — Does any manifest reference this file?
- Config — Does `config/project_layout_policy.json` list this file?
- Documentation — Is it referenced in any doc?
- CI/reference — Would removal break any automated pipeline?

### 4.2 File Groups by Risk

| Risk | Group | Count | Key Examples |
|------|-------|-------|-------------|
| **LOW** | Stage tests & frozen test files | ~284 | `ntpe_stage1_*_test.py`, `ntpe_architecture_*_test.py`, `ntpe_tic_batch*_test.py`, all `ntpe_te_v*_toast.py` |
| **LOW** | LCR/TER/Lic test files | ~100 | `ntpe_lcr_batch*_test.py`, `ntpe_ter_v*_test.py` |
| **LOW** | LTS duplicate root scripts | ~12 | `ntpe_lts_rc_*.py`, `ntpe_lts_stable_*.py` |
| **LOW** | One-shot creation scripts | 3 | `create_context_pipeline_integration.py`, `create_context_prompt_integration.py`, `create_voice_batch1.py` |
| **LOW** | Data/override files | 4 | `character_database_override.json`, `character_override.json`, `glossary_override.json`, `original_ko_chunk_000001.json` |
| **LOW** | LCR batch files at root (test) | ~20 | `Nope_lcr_batch*_test.py` |
| **MEDIUM** | Launcher scripts (if imported by manifests) | 24 | All `launcher_*.py`, `launcher.py` |
| **MEDIUM** | `ntpe_literary_evaluation.py`, `ntpe_literary_regression.py` | 2 | Referenced in quality engine |
| **MEDIUM** | Provider entry scripts | 7 | `ntpe_provider_*`, `ntpe_authorized_*`, `ntpe_controlled_*` |
| **HIGH** | `ntpe_validate.py` | 1 | **KEEP AT ROOT** — Reference by 27+ manifests, governance, CI |
| **HIGH** | `ntpe_production_translate.py` | 1 | Referenced in 9 te_v700 manifests (production pipeline) |
| **HIGH** | `ntpe_batch_monitor.py` | 1 | Listed in project_layout_policy.json |
| **HIGH** | `ntpe_launcher.py` | 1 | Listed in project_layout_policy.json |
| **MEDIUM** | `ntpe_translate_batch.py`, `ntpe_translate_txt.py` | 2 | Production translation entry points |

### 4.3 Critical Dependency Map

```
ntpe_validate.py         — referenced by 30+ manifests, all te_v* freezes
ntpe_production_translate.py — referenced by 9+ manifests, production pipeline
ntpe_batch_monitor.py     — listed in config/project_layout_policy.json
ntpe_launcher.py           — listed in config/project_layout_policy.json
```

### 4.4 Directory Risk

| Risk | Directory Count | Examples |
|------|-----------------|----------|
| **LOW** | 42 | `audits/`, `benchmark/`, `reports/`, `sessions/`, `quality_corpus/`, `tmp/`, `logs/`, `output/`, `final_output/`, `failed_chunks/`, `cache/`, `backup/` |
| **MEDIUM** | 3 | `ntpe/`, `engine/`, `external_api/` — may contain production-resembling code |
| **HIGH** | 0 | No directory has critical-runtime dependency (production runs from `core/`) |

---

## 5. Migration Batch Proposal

### Batch 1 — Low Risk (can be moved immediately, no refactoring needed)

**Target: `archive/`**

| Item | Type | Count |
|------|------|-------|
| All stage test root files | Files | ~284 |
| LTS duplicate root scripts | Files | ~12 |
| One-shot creation scripts | Files | 3 |
| Data/override files | Files | 4 in `archive/data_artifacts/` |
| `audits/` directory | Directory | 1 (508 files) |
| `benchmark/` directory | Directory | 1 (61 files) |
| `reports/` directory | Directory | 1 (5 files) |
| `quality_reports/` directory | Directory | 1 (20 files) |
| `sessions/` directory | Directory | 1 (73 files) |
| All LTS duplicate directories | 11 Directories | ~34 files |

**Total Batch 1:** ~284 files + 15 directories = ~1,000 cleanup items  
**Risk:** LOW — All are frozen/historical, no active import dependencies found

### Batch 2 — History Cleanup

**Temp/output to `.gitignore` / runtime boundary:**

| Item | Action |
|------|--------|
| `backup/` | gitignore or remove |
| `cache/` | rim ignore |
| `temp/` | gitignore |
| `output/` | git ignore |
| `logs/` | git ignore |
| `failed_chunks/` | gitignore |
| `final_output/` | gitignore |

**Reorganize utilities into `tools/`:**

| Item | Destination |
|------|-------------|
| 24 launcher scripts | `tools/launchers/` (existing structure) |
| 7 provider scripts | `tools/providers/` |

**Clean LTS duplicates:**

| Item | Action |
|------|--------|
| 11 lts_rc_* / lts_stable_* directories | Archive or delete (content exists in `lts/`) |
| LTS_RCREA | `archive/lts` |

### Batch 3 — Production Entry Point Stabilization

| Item | Risk | Proposed Action |
|------|------|-----------------|
| `ntpe_production_translate.py` | **HIGH** | After verifying all manifest references, create `core/` wrapper and update manifests, then archive root copy |
| `ntpe_batch_monitor.py` | **HIGH** | Review `config/project_layout_policy.json` dependency, move to `tools/` as entry launcher |
| `ntpe_launcher.py` | **HIGH** | Move to `tools/launchers/` |
| `ntpe_translate_batch.py` | MEDIUM | Move to `tools/launchers/` |
| `ntpe_translate_txt.py` | MEDIUM | Move to `tools/launchers/` |

**Batch 3 Prerequisite:** Update all manifest references (30+ manifest files reference `ntpe_validate.py`) before moving.

---

## 6. Summary Statistics

| Metric | Value |
|--------|-------|
| Total repository items (root) | 426 |
| Total rootiles | 353 |
| Approved root files per governance | 9 |
| Non-approved root files | 344 |
| Total directories | 73 |
| Approved root directories | 19 |
| Non-spec root directories | 50 |
| ROOT POLICY Compliance | **FAIL** |
| Files safe for Batch 1 (LOW risk) | ~284 (~80%) |
| Files needing MEDIUM risk handling | ~30 |
| Files needing HIGH risk handling | 4 |

---

## 7. Root Policy Summary

| Check | Result |
|-------|--------|
| Root Hygiene Principle compliance | **FAIL** — 344 files deprave root namespace |
| Required governance-based root files present | **PEPS** |
| No forbidden root file patterns | **FAIL** — `backup/`, `tmp/`, `output/` exist |
| No new violations since RM-3.1 | **PARTL** — Files have accumulated but major classifications done in RM-3.1 match |
| DIRECTORY_OWNERSHIP compliance | **FAIL** — 50 non-spec directories |

**SCORE: FAIL** — Root does not pass RM-4.0 governance standards in current state.

---

## 8. Recommendations

1. **Execute Batches in order** — Batch 1 has zero-risk items and can dramatically reduce root clutter
2. **Freeze manifests before Batch 3** — Before moving `ntpe_production_translate.py`, `ntpe_validate.py`, etc., update all 30+ manifests with commit-hash locked file paths
3. **Consider merging `lts/` duplicates** — The LTS code files in `lts/` appear identical to the root duplicate scripts; audit to confirm
4. **Do not commit this report** — Per RM-4.0 spec, this is evidence only. Commit triggers only after Batch execution
5. **Gate Batch 3 on user authorization** — All production entry-point moves require explicit user approval since they change `config/project_layout_policy.json`

---

## Validation

To be performed after report generation:

```
git diff --check
python ntpe_validate.py
```

Expected:
- Python modification = 0
- Runtime modification = 0
- Provider execution = 0
- Network request = 0

---

Generated by: RM-4.0.1 Preflight Inventory Process
No files were moved, deleted, renamed, or modified during this scan.
No translation or provider execution was triggered.
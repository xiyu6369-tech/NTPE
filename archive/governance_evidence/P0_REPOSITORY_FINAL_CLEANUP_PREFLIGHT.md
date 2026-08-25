# P0 Repository Final Cleanup — Preflight Document

## 1. Repository Baseline

| Item | Value |
|------|-------|
| **Baseline Commit** | `61fc7d359a9e3e1e51c66b0909aec86a3baf3831` (P0 Stage 5 Batch 5.8.1) |
| **Current HEAD** | `61fc7d3` |
| **origin/main** | `61fc7d3` (fast-forward, no divergence) |
| **Branch** | `main` |
| **Working Tree** | Dirty (pre-existing B/C/D changes + new untracked) |

---

## 2. Local vs Origin Comparison

### Git Status Summary

```
# Tracked files with worktree modifications (17 items)
D  RM_6_4_0_ACCEPTANCE_REPORT.md
D  RM_7_3_1_ACCEPTANCE_REPORT.md
M  artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json
M  artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json
D  ntpe_controlled_real_provider_retry.py
D  ntpe_literary_evaluation.py
D  ntpe_literary_regression.py
D  ntpe_provider_audit.py
D  ntpe_provider_benchmark_session.py
D  ntpe_provider_setup.py
D  ntpe_provider_verify.py
D  ntpe_single_real_provider_invocation.py
D  scripts/check_prod_imports.py
M  tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json
M  tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json
M  tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json
M  tests/literary/outputs/Regression_History.json
M  tests/literary/outputs/Regression_History.md
D  tools/one_shots/fix_char_rules.py
D  tools/one_shots/fix_narrative.py

# Untracked files (29 items)
?? P0_STAGE5_INTEGRATED_REVIEW.md
?? artifacts/p0_productization/ (17 files)
?? artifacts/rm7_entity_canary/
?? artifacts/rm8_5_audit/
?? core/adapters/production_submission_adapter.py.new
?? core/context_scene_memory/persistence.py
?? core/translation_runtime/boundary_detector.py
?? docs/governance/rm8/ (40+ files)
?? dummy.txt
?? knowledge/
?? tools/one_shots/ntpe_literary_evaluation.py
?? tools/one_shots/ntpe_literary_regression.py
```

### Three-Way State Matrix

| Path | HEAD (61fc7d3) | Worktree | origin/main | Classification |
|------|----------------|----------|-------------|----------------|
| RM_6_4_0_ACCEPTANCE_REPORT.md | Present | Deleted | Present | **B** — Pre-existing intended cleanup |
| RM_7_3_1_ACCEPTANCE_REPORT.md | Present | Deleted | Present | **B** — Pre-existing intended cleanup |
| ntpe_*provider*.py (5 files) | Present | Deleted | Present | **B** — Pre-existing intended cleanup |
| ntpe_literary_*.py (2 files) | Present | Deleted | Present | **B** — Pre-existing intended cleanup |
| ntpe_controlled_real_provider_retry.py | Present | Deleted | Present | **B** — Pre-existing intended cleanup |
| ntpe_single_real_provider_invocation.py | Present | Deleted | Present | **B** — Pre-existing intended cleanup |
| scripts/check_prod_imports.py | Present | Deleted | Present | **B** — Pre-existing intended cleanup |
| tools/one_shots/fix_char_rules.py | Present | Deleted | Present | **B** — Pre-existing intended cleanup |
| tools/one_shots/fix_narrative.py | Present | Deleted | Present | **B** — Pre-existing intended cleanup |
| artifacts/rm6_canary/*_progress.json | Present | Modified | Present | **D** — Generated/test artifacts |
| tests/literary/outputs/* | Present | Modified | Present | **D** — Generated/test artifacts |
| P0_STAGE5_INTEGRATED_REVIEW.md | Absent | Untracked | Absent | **A** — Review working file |
| dummy.txt | Absent | Untracked | Absent | **A** — Root hygiene violation |
| core/adapters/production_submission_adapter.py.new | Absent | Untracked | Absent | **E** — Ambiguous (WIP) |
| core/context_scene_memory/persistence.py | Absent | Untracked | Absent | **E** — Ambiguous (WIP) |
| core/translation_runtime/boundary_detector.py | Absent | Untracked | Absent | **E** — Ambiguous (WIP) |
| docs/governance/rm8/* | Present (partial) | Untracked (new) | Present (partial) | **A** — Authorized governance |
| artifacts/p0_productization/* | Absent | Untracked | Absent | **C** — Unrelated/new |
| artifacts/rm7_entity_canary/ | Absent | Untracked | Absent | **D** — Generated/test artifacts |
| artifacts/rm8_5_audit/ | Absent | Untracked | Absent | **D** — Generated/test artifacts |
| knowledge/ | Absent | Untracked | Absent | **C** — Unrelated/new |
| tools/one_shots/ntpe_literary_*.py | Absent | Untracked | Absent | **C** — Copies of deleted root files |

---

## 3. Complete Root Inventory

### Tracked Root Files (per `git ls-files`)

| File | Size | ROOT_ALLOWLIST | Status | Classification |
|------|------|----------------|--------|----------------|
| README.md | 10KB+ | ✅ KEEP_ROOT | Tracked | KEEP |
| VERSION.txt | ~10B | ✅ KEEP_ROOT | Tracked | KEEP |
| requirements.txt | ~500B | ✅ KEEP_ROOT | Tracked | KEEP |
| pyproject.toml | ~2KB | ✅ KEEP_ROOT | Tracked | KEEP |
| .gitignore | 3KB | ✅ KEEP_ROOT | Tracked | KEEP |
| .gitattributes | ~200B | ✅ KEEP_ROOT | Tracked | KEEP |
| .editorconfig | ~300B | ✅ KEEP_ROOT | Tracked | KEEP |
| .clineignore | ~100B | ✅ KEEP_ROOT | Tracked | KEEP |
| .clinerules | ~1KB | ✅ KEEP_ROOT | Tracked | KEEP |
| ntpe_validate.py | ~15KB | ✅ KEEP_ROOT | Tracked | KEEP |
| ntpe_launcher.py | ~10KB | ⚠️ Entrypoint | Tracked | KEEP |
| ntpe_production_translate.py | ~8KB | ⚠️ Entrypoint | Tracked | KEEP |
| ntpe_batch_monitor.py | ~5KB | ⚠️ Entrypoint | Tracked | KEEP |
| launcher_translate.py | ~3KB | ⚠️ Entrypoint | Tracked | KEEP |
| RM_6_4_0_ACCEPTANCE_REPORT.md | ~20KB | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |
| RM_7_3_1_ACCEPTANCE_REPORT.md | ~25KB | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |
| ntpe_controlled_real_provider_retry.py | 1KB | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |
| ntpe_literary_evaluation.py | 350KB | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |
| ntpe_literary_regression.py | 250KB | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |
| ntpe_provider_audit.py | ~200B | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |
| ntpe_provider_benchmark_session.py | ~200B | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |
| ntpe_provider_setup.py | ~200B | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |
| ntpe_provider_verify.py | ~200B | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |
| ntpe_single_real_provider_invocation.py | ~200B | ❌ Not allowed | **Deleted in worktree** | B → REMOVE from HEAD |

### Untracked Root Files

| File | Size | Created | Content | Classification |
|------|------|---------|---------|----------------|
| dummy.txt | 36B | 2026-08-20 | Two glossary mappings (scratch) | **REMOVE** — No consumer verified |
| P0_STAGE5_INTEGRATED_REVIEW.md | 250KB | 2026-08-22 | Integrated review draft (Batches 5.1-5.7) | **MOVE** → docs/governance/rm8/ |

### Tracked Root Directories (Permitted)

```
core/  config/  tools/  tests/  docs/  archive/  artifacts/
manifests/  lts/  protocols/  schemas/  sdk/  cli/  engine/
```
All permitted per REPOSITORY_STRUCTURE_SPEC.md.

---

## 4. Complete Untracked Inventory

### Governance Documents (`docs/governance/rm8/` — 40+ files)
**Status**: Authorized Stage 5 production scope. All tracked in HEAD or newly created as part of Batch 5.x delivery.
**Action**: KEEP — Already in correct location.

### Productization Artifacts (`artifacts/p0_productization/` — 17 files)
**Status**: New untracked directory with implementation reports, specifications, audits.
**Action**: **ARCHIVE** — Not part of production repository; move to `archive/p0_productization/` or remove.

### Canary/Audit Artifacts
- `artifacts/rm7_entity_canary/` — **D** (Generated/test artifact) → REMOVE from tracking
- `artifacts/rm8_5_audit/` — **D** (Generated/test artifact) → REMOVE from tracking

### Core Work-in-Progress Files (3 files)
| File | Likely Purpose | Dependencies | Classification |
|------|----------------|--------------|----------------|
| `core/adapters/production_submission_adapter.py.new` | Production submission adapter (new) | References `ntpe_production_translate.py` | **E → RESOLVE** — Must determine if replacement or addition |
| `core/context_scene_memory/persistence.py` | Context/scene memory persistence layer | Implements `load_or_create_context_memory` | **E → RESOLVE** — Appears to be new production code |
| `core/translation_runtime/boundary_detector.py` | Scene/chapter boundary detection | Used by Context/Scene Memory | **E → RESOLVE** — Appears to be new production code |

### Knowledge Directory
- `knowledge/learning/candidates.json` (621B)
- `knowledge/learning/characters.json` (361B)
**Status**: Learning data, likely runtime-generated
**Action**: **LOCAL_ONLY** — Add to `.gitignore` if not already

### Tools One-Shots (27 files in `tools/one_shots/`)
| Category | Files | Action |
|----------|-------|--------|
| `launcher_*.py` (16 files) | Analysis/debug utilities | **ARCHIVE** → `tools/archive/one_shots_launcher/` |
| `write_*.py` (11 files) | Content generation utilities | **ARCHIVE** → `tools/archive/one_shots_write/` |
| `ntpe_literary_evaluation.py` | Copy of deleted root script | **REMOVE** — Already in tools/provider_utils/ or similar |
| `ntpe_literary_regression.py` | Copy of deleted root script | **REMOVE** — Already in tools/provider_utils/ or similar |
| `fix_char_rules.py`, `fix_narrative.py` | Already deleted (tracked) | **CONFIRMED B** — No action needed |

---

## 5. Complete Modified/Deleted Inventory (Worktree Changes)

### Deleted Tracked Files (13 files) — Category B (Pre-existing Intended Change)

| File | Original Purpose | Replacement Location | Verified No Consumer |
|------|------------------|---------------------|---------------------|
| `RM_6_4_0_ACCEPTANCE_REPORT.md` | Stage acceptance report | `docs/governance/rm6/` or `archive/` | ✅ |
| `RM_7_3_1_ACCEPTANCE_REPORT.md` | Stage acceptance report | `docs/governance/rm7/` or `archive/` | ✅ |
| `ntpe_controlled_real_provider_retry.py` | Compat wrapper | `tools/provider_controls/` | ✅ |
| `ntpe_literary_evaluation.py` | Literary evaluation runner | `tools/one_shots/` (untracked copy exists) | ⚠️ Check |
| `ntpe_literary_regression.py` | Literary regression runner | `tools/one_shots/` (untracked copy exists) | ⚠️ Check |
| `ntpe_provider_audit.py` | Compat wrapper | `tools/provider_utils/` | ✅ |
| `ntpe_provider_benchmark_session.py` | Compat wrapper | `tools/provider_controls/` | ✅ |
| `ntpe_provider_setup.py` | Compat wrapper | `tools/provider_utils/` | ✅ |
| `ntpe_provider_verify.py` | Compat wrapper | `tools/provider_utils/` | ✅ |
| `ntpe_single_real_provider_invocation.py` | Compat wrapper | `tools/provider_controls/` | ✅ |
| `scripts/check_prod_imports.py` | One-shot import checker | N/A (one-shot) | ✅ |
| `tools/one_shots/fix_char_rules.py` | One-shot rule fix | N/A (one-shot) | ✅ |
| `tools/one_shots/fix_narrative.py` | One-shot narrative fix | N/A (one-shot) | ✅ |

### Modified Tracked Files (6 files) — Category D (Generated/Artifact)

| File | Nature | Action |
|------|--------|--------|
| `artifacts/rm6_canary/legacy_kr/novel_sample_live_progress.json` | Canary progress tracking | **IGNORE** — Generated |
| `artifacts/rm6_canary/runtime_kr/novel_sample_live_progress.json` | Canary progress tracking | **IGNORE** — Generated |
| `tests/literary/outputs/PS-03-integration/Literary_Quality_Report.json` | Test output | **IGNORE** — Generated |
| `tests/literary/outputs/PS-03-smoke/Literary_Quality_Report.json` | Test output | **IGNORE** — Generated |
| `tests/literary/outputs/PS-03-smoke/Literary_Regression_Report.json` | Test output | **IGNORE** — Generated |
| `tests/literary/outputs/Regression_History.json` | Test history | **IGNORE** — Generated |
| `tests/literary/outputs/Regression_History.md` | Test history | **IGNORE** — Generated |

---

## 6. Dependency Evidence

### Root Scripts Deleted — Consumer Verification

| Deleted Script | Imports From | Imported By | Verdict |
|----------------|--------------|-------------|---------|
| `ntpe_controlled_real_provider_retry.py` | `tools.provider_controls` | None found | Safe to delete |
| `ntpe_literary_evaluation.py` | `core.translation_engine.utils`, `core.translation_runtime`, `lts.txt_translation_runtime` | None found (untracked copy in `tools/one_shots/`) | Safe to delete |
| `ntpe_literary_regression.py` | `core.translation_engine.utils`, `core.translation_runtime`, `lts.txt_translation_runtime`, `ntpe_literary_evaluation` | None found (untracked copy in `tools/one_shots/`) | Safe to delete |
| `ntpe_provider_audit.py` | `tools.provider_utils` | None found | Safe to delete |
| `ntpe_provider_benchmark_session.py` | `tools.provider_controls` | None found | Safe to delete |
| `ntpe_provider_setup.py` | `tools.provider_utils` | None found | Safe to delete |
| `ntpe_provider_verify.py` | `tools.provider_utils` | None found | Safe to delete |
| `ntpe_single_real_provider_invocation.py` | `tools.provider_controls` | None found | Safe to delete |
| `scripts/check_prod_imports.py` | stdlib only | None found | Safe to delete |

**Note**: The untracked copies in `tools/one_shots/` (`ntpe_literary_evaluation.py`, `ntpe_literary_regression.py`) appear to be duplicates placed there after the root deletions. These should be removed as they serve no purpose.

### Core WIP Files — Dependency Check

| File | Imports | Imported By | Verdict |
|------|---------|-------------|---------|
| `core/context_scene_memory/persistence.py` | `.models`, `.serialization`, `.store`, `.validation` | None found (new module) | **UNKNOWN** — Must verify if integrated |
| `core/translation_runtime/boundary_detector.py` | `core.context_scene_memory.models` | None found (new module) | **UNKNOWN** — Must verify if integrated |
| `core/adapters/production_submission_adapter.py.new` | stdlib, `pathlib` | None found (`.new` suffix) | **UNKNOWN** — Likely replacement candidate |

---

## 7. KEEP / MOVE / ARCHIVE / REMOVE / UNKNOWN Matrix

### Category A — Final Cleanup Authorized (New Actions)

| Path | Action | Target | Rationale |
|------|--------|--------|-----------|
| `dummy.txt` | **REMOVE** | — | Root hygiene violation; 36B glossary scratch; no consumer |
| `P0_STAGE5_INTEGRATED_REVIEW.md` | **MOVE** | `docs/governance/rm8/P0_STAGE5_INTEGRATED_REVIEW.md` | Formal review artifact belongs in governance |
| `core/adapters/production_submission_adapter.py.new` | **RESOLVE** | Replace `production_submission_adapter.py` or ARCHIVE | Must determine intent; `.new` suffix suggests replacement |
| `core/context_scene_memory/persistence.py` | **RESOLVE** | Integrate into `core/context_scene_memory/` or ARCHIVE | New production code? Must verify if part of Stage 5 |
| `core/translation_runtime/boundary_detector.py` | **RESOLVE** | Integrate into `core/translation_runtime/` or ARCHIVE | New production code? Must verify if part of Stage 5 |

### Category B — Pre-existing Intended Changes (Owner Worktree Changes)

| Path | Action | Rationale |
|------|--------|-----------|
| `RM_6_4_0_ACCEPTANCE_REPORT.md` | **KEEP DELETED** | Owner already deleted; remove from HEAD |
| `RM_7_3_1_ACCEPTANCE_REPORT.md` | **KEEP DELETED** | Owner already deleted; remove from HEAD |
| `ntpe_controlled_real_provider_retry.py` | **KEEP DELETED** | Owner already deleted; compat wrapper in tools/ |
| `ntpe_literary_evaluation.py` | **KEEP DELETED** | Owner already deleted; untracked copy in tools/one_shots/ to also remove |
| `ntpe_literary_regression.py` | **KEEP DELETED** | Owner already deleted; untracked copy in tools/one_shots/ to also remove |
| `ntpe_provider_audit.py` | **KEEP DELETED** | Owner already deleted; compat wrapper in tools/ |
| `ntpe_provider_benchmark_session.py` | **KEEP DELETED** | Owner already deleted; compat wrapper in tools/ |
| `ntpe_provider_setup.py` | **KEEP DELETED** | Owner already deleted; compat wrapper in tools/ |
| `ntpe_provider_verify.py` | **KEEP DELETED** | Owner already deleted; compat wrapper in tools/ |
| `ntpe_single_real_provider_invocation.py` | **KEEP DELETED** | Owner already deleted; compat wrapper in tools/ |
| `scripts/check_prod_imports.py` | **KEEP DELETED** | Owner already deleted; one-shot |
| `tools/one_shots/fix_char_rules.py` | **KEEP DELETED** | Owner already deleted; one-shot |
| `tools/one_shots/fix_narrative.py` | **KEEP DELETED** | Owner already deleted; one-shot |

### Category C — Pre-existing Unrelated Changes

| Path | Action | Rationale |
|------|--------|-----------|
| `artifacts/p0_productization/` | **ARCHIVE** → `archive/p0_productization/` | Not production; implementation evidence |
| `artifacts/rm7_entity_canary/` | **REMOVE** | Generated test artifacts |
| `artifacts/rm8_5_audit/` | **REMOVE** | Generated audit artifacts |
| `knowledge/` | **LOCAL_ONLY** | Add to `.gitignore`; runtime learning data |
| `tools/one_shots/launcher_*.py` (16 files) | **ARCHIVE** → `tools/archive/one_shots_launcher/` | Historical utilities |
| `tools/one_shots/write_*.py` (11 files) | **ARCHIVE** → `tools/archive/one_shots_write/` | Historical utilities |
| `tools/one_shots/ntpe_literary_evaluation.py` | **REMOVE** | Duplicate of deleted root file |
| `tools/one_shots/ntpe_literary_regression.py` | **REMOVE** | Duplicate of deleted root file |

### Category D — Generated / Artifact

| Path | Action | Rationale |
|------|--------|-----------|
| `artifacts/rm6_canary/*/novel_sample_live_progress.json` | **IGNORE** (already modified) | Test artifacts; add to `.gitignore` |
| `tests/literary/outputs/*` | **IGNORE** (already modified) | Test outputs; already in `.gitignore` |
| All `artifacts/te_v*`, `artifacts/tic_batch*`, `artifacts/lcr_batch*` | **ARCHIVE** or **REMOVE** | Historical canary/test data; not production |

### Category E — Ambiguous (MUST RESOLVE TO ZERO)

| Path | Current Classification | Required Resolution |
|------|----------------------|---------------------|
| `core/adapters/production_submission_adapter.py.new` | **E** | Determine: (a) replace existing adapter, (b) new feature, (c) WIP to discard |
| `core/context_scene_memory/persistence.py` | **E** | Determine: (a) new production module for Stage 5, (b) WIP to discard |
| `core/translation_runtime/boundary_detector.py` | **E** | Determine: (a) new production module for Stage 5, (b) WIP to discard |

**HARD RULE: E = 0 BEFORE ANY COMMIT**

---

## 8. Root Hygiene Assessment

### ROOT_POLICY Compliance Check

| Policy Rule | Current State | Violation? |
|-------------|---------------|------------|
| Only permitted files at root | `dummy.txt`, `P0_STAGE5_INTEGRATED_REVIEW.md` present | ✅ YES (2 violations) |
| No stage scripts | None at root currently | PASS |
| No verification scripts (except `ntpe_validate.py`) | None | PASS |
| No temporary utilities/one-shots | None at root currently | PASS |
| No test files | None at root currently | PASS |
| No backup archives/ZIP | None | PASS |
| No archive files | None at root currently | PASS |
| No duplicate production code | None | PASS |

### Root Hygiene Verdict: **DEBT — 2 violations**
1. `dummy.txt` — Must remove
2. `P0_STAGE5_INTEGRATED_REVIEW.md` — Must move to `docs/governance/rm8/`

---

## 9. GitHub Reconciliation

### Reconciliation Matrix

| Category | Local HEAD | origin/main | Action Required |
|----------|------------|-------------|-----------------|
| **Production Code (core/, lts/, engine/, cli/, sdk/)** | Clean (matches HEAD) | Clean | None |
| **Governance (docs/governance/rm8/)** | New files untracked | Partial | Add new Batch 5.8.1 docs to tracking |
| **Root Entrypoints** | 13 deleted in worktree | Present in HEAD | **Commit deletions** (Category B) |
| **Root Hygiene Violations** | 2 untracked | Clean | **Remove/Move** (Category A) |
| **Test Artifacts** | Modified | Clean | **Ignore** (add to .gitignore) |
| **Canary Artifacts** | New untracked dirs | Clean | **Remove/Archive** (Category C/D) |
| **Tools/One-Shots** | 2 deleted, 27 untracked | Present in HEAD | **Archive/Remove** (Category C) |
| **Core WIP Files** | 3 untracked | Absent | **Resolve E→A/B/C/D** |

### Key Finding
**origin/main is CLEAN** — All issues are local worktree state. No GitHub-side cleanup needed. The cleanup is purely about committing the Owner's intended deletions (Category B) and resolving local untracked state (Categories A, C, D, E).

---

## 10. Proposed Atomic Cleanup Batches

### Batch A: Root Hygiene (Minimal, Safe)
- `dummy.txt` → REMOVE
- `P0_STAGE5_INTEGRATED_REVIEW.md` → MOVE to `docs/governance/rm8/`
- **Validation**: `python ntpe_validate.py`, `git diff --check`

### Batch B: Owner's Intended Deletions (13 files)
- Commit all 13 deleted tracked files (already deleted in worktree)
- Also remove 2 untracked duplicates in `tools/one_shots/`
- **Validation**: `python ntpe_validate.py`, `python -m compileall core/`, `pytest tests/series/ -v`

### Batch C: Tools/One-Shots Organization
- Archive `tools/one_shots/launcher_*.py` (16 files) → `tools/archive/one_shots_launcher/`
- Archive `tools/one_shots/write_*.py` (11 files) → `tools/archive/one_shots_write/`
- Remove `tools/one_shots/ntpe_literary_*.py` (2 files, duplicates)
- **Validation**: `python ntpe_validate.py`

### Batch D: Generated Artifacts & Ignore Policy
- Add `artifacts/rm6_canary/` to `.gitignore`
- Add `artifacts/rm7_entity_canary/` to `.gitignore`
- Add `artifacts/rm8_5_audit/` to `.gitignore`
- Add `knowledge/` to `.gitignore`
- Verify `tests/literary/outputs/` already ignored
- **Validation**: `git status --ignored`, `python ntpe_validate.py`

### Batch E: Core WIP Resolution (REQUIRES OWNER DECISION)
- **STOP-02 TRIGGER** — 3 files classified as E (Ambiguous)
- Must resolve each to KEEP/MOVE/ARCHIVE/REMOVE before proceeding
- **Validation**: Full test suite, compile check, validation

### Batch F: Historical Artifacts Cleanup (Large Scope)
- Archive or remove `artifacts/te_v*`, `artifacts/tic_batch*`, `artifacts/lcr_batch*`, `artifacts/controlled_*`, `artifacts/translation_execution_*`, etc.
- **Scope**: 100+ directories — Requires separate assessment
- **Validation**: `python ntpe_validate.py`, ensure no production imports

---

## 11. Clean Clone Plan

### Fresh Clone Validation Steps

```powershell
# 1. Clone to temporary location
git clone https://github.com/<org>/NTPE.git /tmp/NTPE_clean_clone
cd /tmp/NTPE_clean_clone

# 2. Verify clean state
git status --short          # Must be empty
git log --oneline -1        # Must match 61fc7d3

# 3. Install dependencies
pip install -r requirements.txt

# 4. Compile check
python -m compileall core/

# 5. Validator
python ntpe_validate.py

# 6. Diff check
git diff --check

# 7. Core test suite
python -m pytest tests/series/ -v

# 8. E2E smoke (dry-run only)
NTPE_RUNTIME_PIPELINE=runtime python -m pytest tests/series/test_series_integration.py::test_two_book_series_e2e -v

# 9. Provider/Network/Translation audit
# Must confirm: Provider=0, Network=0, Translation=0
```

### Expected Clean Clone State
- Working tree: **CLEAN** (only `.gitignore`d directories like `.pytest_cache/`, `.kilo/`, `.vscode/`)
- No `dummy.txt`, no root review drafts
- No untracked core WIP files
- No untracked canary artifacts
- All 13 root deletions committed
- All governance docs in `docs/governance/rm8/`

---

## 12. Stop Conditions Assessment

| Stop Condition | Status | Details |
|----------------|--------|---------|
| **STOP-01**: Stage 5 functionality affected | **CLEAR** | Cleanup targets only root hygiene, artifacts, tools — not core production |
| **STOP-02**: Unknown files (E > 0) | **TRIGGERED** | 3 core WIP files classified E — **MUST RESOLVE** |
| **STOP-03**: Deleted file still used | **CLEAR** | Verified no consumers for 13 deleted scripts; 2 core WIP files need check |
| **STOP-04**: Local/GitHub unreconciled | **CLEAR** | origin/main clean; all issues local |
| **STOP-05**: New root production artifact | **CLEAR** | No new production artifacts at root |
| **STOP-06**: Frozen contract modification | **CLEAR** | Cleanup does not touch frozen contracts |
| **STOP-07**: Clean clone needs untracked files | **PENDING** | Must verify after Batch E resolution |
| **STOP-08**: Provider/Network/Translation > 0 | **CLEAR** | Cleanup is file operations only |
| **STOP-09**: Overlap with Owner B/C/D changes | **CLEAR** | Cleanup batches respect Owner's deletions (Batch B) |

---

## 13. Owner Authorization Points

### REQUIRED AUTHORIZATIONS

| # | Decision Required | Current State | Options |
|---|-------------------|---------------|---------|
| 1 | **Core WIP Resolution** (3 files) | All 3 are E (Ambiguous) | For each: KEEP (integrate), MOVE (to proper location), ARCHIVE, or REMOVE |
| 2 | **Historical Artifacts Scope** (Batch F) | 100+ artifact directories | Full cleanup? Archive only? Selective? |
| 3 | **Knowledge Directory** | Untracked, learning data | Add to `.gitignore` (LOCAL_ONLY) or track? |
| 4 | **Batch Execution Order** | 6 proposed batches | Approve A→B→C→D→E→F or modified order |

### PREFLIGHT COMPLETION STATUS

**Preflight is COMPLETE but BLOCKED on STOP-02 (E > 0).**

Cannot proceed to implementation until Owner resolves 3 ambiguous core files.

---

## 14. Preflight Summary Report

```
P0 Repository Final Cleanup — PREFLIGHT COMPLETE

Baseline:
61fc7d359a9e3e1e51c66b0909aec86a3baf3831

Local HEAD:
61fc7d3

origin/main:
61fc7d3

Root Hygiene:
DEBT (2 violations: dummy.txt, P0_STAGE5_INTEGRATED_REVIEW.md)

Unknown Files:
3 (core WIP files classified E)

KEEP:
21 (root permitted files + tracked directories)

MOVE:
1 (P0_STAGE5_INTEGRATED_REVIEW.md → docs/governance/rm8/)

ARCHIVE:
~50 (tools/one_shots/ historical, artifacts/p0_productization/, historical artifacts/)

REMOVE:
15 (dummy.txt, 13 root deletions committed, 2 duplicate one-shots)

Pre-existing Protected Changes (Category B):
13 (Owner's intended deletions already in worktree)

Proposed Atomic Cleanup Batches:
6 (A: Root Hygiene, B: Owner Deletions, C: Tools Org, D: Artifacts/Ignore, E: Core WIP, F: Historical)

Clean Clone Plan:
READY (pending Batch E resolution)

Owner Authorization:
REQUIRED (3 E-classified files + historical artifacts scope)

No staging / commit / push performed.
```
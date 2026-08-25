# P0-FINAL-12-R1-F — Root Hygiene Provenance Audit

**Date:** 2026-08-25  
**Baseline Commit:** 53e04767f9a1012641152e96786011fbb3b0e466 (B5 atomic commit)  
**Current HEAD:** 53e04767f9a1012641152e96786011fbb3b0e466  
**origin/main:** 53e04767f9a1012641152e96786011fbb3b0e466  
**Branch:** main  
**Status:** BLOCKED — Unexpected root-level files detected  

---

## 1. Git State Baseline

| Item | Value |
|------|-------|
| Branch | main |
| HEAD | 53e04767f9a1012641152e96786011fbb3b0e466 |
| origin/main | 53e04767f9a1012641152e96786011fbb3b0e466 |
| Staged files | 0 |
| Unstaged modified/deleted | 283 paths |
| Untracked files | 66 paths |

---

## 2. Complete Root-Level Inventory

### 2.1 Tracked Root Files (at HEAD 53e0476)

These are the 13 files tracked at repository root per `git ls-tree -r HEAD --name-only`:

| Path | Type | Size | Purpose |
|------|------|------|---------|
| .clineignore | File | 762 | Tool ignore patterns |
| .clinerules | File | 4,246 | Tool rules |
| .editorconfig | File | 571 | Editor configuration |
| .gitattributes | File | 74 | Git attributes |
| .gitignore | File | 2,179 | Git ignore patterns |
| launcher_translate.py | File | 328 | Legacy entry point (allowlisted) |
| ntpe_batch_monitor.py | File | 341 | Legacy entry point |
| ntpe_launcher.py | File | 9,920 | Production launcher (allowlisted) |
| ntpe_literary_evaluation.py | File | 14,896 | Production evaluation (allowlisted) |
| ntpe_literary_regression.py | File | 9,740 | Production regression (allowlisted) |
| ntpe_production_translate.py | File | 58,822 | Production translate (allowlisted) |
| ntpe_validate.py | File | 11,531 | Project validator (allowlisted) |
| pyproject.toml | File | 141 | Package manifest (allowlisted) |
| README.md | File | 1,820 | Repository documentation (allowlisted) |
| requirements.txt | File | 69 | Dependencies (allowlisted) |
| VERSION.txt | File | 45 | Version identifier (allowlisted) |

**Total tracked at root: 16 files**

### 2.2 Untracked Root Files (Current Working Tree)

| Path | Type | Size | Last Write | Status |
|------|------|------|------------|--------|
| audit_r1_e.py | File | 8,189 | 2026-08-24 23:39:47 | Unexpected |
| check_missing.py | File | 2,707 | 2026-08-24 23:30:56 | Unexpected |
| classify_changes.py | File | 5,454 | 2026-08-24 23:28:56 | Unexpected |
| diff_output.txt | File | 19,091 | 2026-08-25 00:09:33 | Unexpected |

**Total unexpected untracked root files: 4**

### 2.3 Root Directories (All Tracked/Allowed)

All root directories are permitted per REPOSITORY_STRUCTURE_SPEC.md:
.agents, .ai, .codex, .git, .kilo, .ntpe_test_sandbox, .pytest_cache, .vscode, analysis, archive, artifacts, backup, benchmark, benchmarks, cli, compatibility, config, context, core, docs, engine, external_api, integration, knowledge, logs, lts, manifests, memory, ntpe, output, packaging, performance, platform_services, profiles, prompt_packages, regression, release_candidate, runtime_api, schemas, scripts, sdk, stable_release, tests, tools, translated, translation, translation_cache, ui, verification, web, web_ui, workflow, __pycache__

---

## 3. Unexpected Root-Level Items — Detailed Classification

### Item 1: `audit_r1_e.py`

| Property | Value |
|----------|-------|
| **Exact Path** | `audit_r1_e.py` |
| **Type** | File (Python script) |
| **Tracked/Untracked/Ignored** | Untracked |
| **Modification Status** | New (not at HEAD) |
| **Creation/Last-Write Timestamp** | 2026-08-24 23:39:47 |
| **File Size** | 8,189 bytes |
| **Existed at HEAD 53e0476** | No |
| **In R1-E Inventory (349-path)** | Yes — classified as UNKNOWN, Item: "Audit scripts (this task)" |
| **In Protected Worktree (274)** | No |
| **In UNKNOWN Set (38)** | Yes — explicitly listed |
| **Likely Provenance** | Agent/tool execution artifact from R1-E commit boundary audit task |
| **Recommended Disposition** | Move to `tools/maintenance/` or `artifacts/`; not a root hygiene violation per se but violates Root Policy §3 (temporary utilities belong under tools/) |

### Item 2: `check_missing.py`

| Property | Value |
|----------|-------|
| **Exact Path** | `check_missing.py` |
| **Type** | File (Python script) |
| **Tracked/Untracked/Ignored** | Untracked |
| **Modification Status** | New (not at HEAD) |
| **Creation/Last-Write Timestamp** | 2026-08-24 23:30:56 |
| **File Size** | 2,707 bytes |
| **Existed at HEAD 53e0476** | No |
| **In R1-E Inventory (349-path)** | Yes — classified as UNKNOWN, Item: "Audit scripts (this task)" |
| **In Protected Worktree (274)** | No |
| **In UNKNOWN Set (38)** | Yes — explicitly listed |
| **Likely Provenance** | Agent/tool execution artifact from R1-E classification phase |
| **Recommended Disposition** | Move to `tools/maintenance/` or `artifacts/` |

### Item 3: `classify_changes.py`

| Property | Value |
|----------|-------|
| **Exact Path** | `classify_changes.py` |
| **Type** | File (Python script) |
| **Tracked/Untracked/Ignored** | Untracked |
| **Modification Status** | New (not at HEAD) |
| **Creation/Last-Write Timestamp** | 2026-08-24 23:28:56 |
| **File Size** | 5,454 bytes |
| **Existed at HEAD 53e0476** | No |
| **In R1-E Inventory (349-path)** | Yes — classified as UNKNOWN, Item: "Audit scripts (this task)" |
| **In Protected Worktree (274)** | No |
| **In UNKNOWN Set (38)** | Yes — explicitly listed |
| **Likely Provenance** | Agent/tool execution artifact from R1-E classification phase |
| **Recommended Disposition** | Move to `tools/maintenance/` or `artifacts/` |

### Item 4: `diff_output.txt`

| Property | Value |
|----------|-------|
| **Exact Path** | `diff_output.txt` |
| **Type** | File (Text diff output) |
| **Tracked/Untracked/Ignored** | Untracked |
| **Modification Status** | New (not at HEAD) |
| **Creation/Last-Write Timestamp** | 2026-08-25 00:09:33 |
| **File Size** | 19,091 bytes |
| **Existed at HEAD 53e0476** | No |
| **In R1-E Inventory (349-path)** | Yes — classified as UNKNOWN, Item: "Audit scripts (this task)" |
| **In Protected Worktree (274)** | No |
| **In UNKNOWN Set (38)** | Yes — explicitly listed |
| **Likely Provenance** | Agent/tool execution artifact from R1-E diff capture phase |
| **Recommended Disposition** | Move to `artifacts/` (diagnostic/validation artifact) |

---

## 4. Classification Summary

### 4.1 By Category

| Category | Count | Items |
|----------|-------|-------|
| **Protected Worktree** | 0 | None of the 4 unexpected items are in the 274 Protected Worktree paths |
| **UNKNOWN (R1-E set)** | 4 | All 4 items explicitly listed in UNKNOWN set of R1-E audit |
| **R1-Related** | 4 | All 4 are agent artifacts from R1-E audit execution |
| **Temporary/Generated** | 4 | All 4 are one-shot audit scripts and outputs |
| **Root Hygiene Violations** | 4 | All 4 violate Root Policy §3 (temporary utilities) and §4 (experimental/one-shot tools) |

### 4.2 Provenance Assessment

All 4 unexpected root files share the same provenance:
- **Created during:** R1-E commit boundary audit execution (2026-08-24 23:28–00:09)
- **Created by:** Agent/tool execution during the audit task
- **Purpose:** Audit script utilities and diff capture output
- **Classification in R1-E:** UNKNOWN — "Audit scripts (this task)"

These are **not**:
- P0-FINAL-12 / R1 work deliverables (R1-A through R1-D, R1-INVENTORY are separate)
- Protected Worktree items (pre-existing changes from before B5 commit)
- Historical artifacts requiring archival

---

## 5. Root Hygiene Policy Assessment

Per **ROOT_POLICY.md** (permanent, active):

| Policy Section | Violation | Details |
|----------------|-----------|---------|
| §3 — Temporary Utilities or One-shot Tools | **VIOLATED** | All 4 files are one-shot audit scripts created for a single task |
| §4 — Experimental Modules or Prototypes | **VIOLATED** | `audit_r1_e.py`, `check_missing.py`, `classify_changes.py` are experimental audit tools |
| §5 — Test Files | Not applicable | None are test files |
| §7 — Archive Files | **VIOLATED** | `diff_output.txt` is diagnostic output that belongs in `artifacts/` |

Per **ROOT_ALLOWLIST.md** (freeze snapshot):
- None of the 4 files appear on the allowlist
- `ntpe_validate.py` is the ONLY permitted Python script at root (as validator)

**Validation Result:** `python ntpe_validate.py` → **FAIL** — "Unexpected root items: audit_r1_e.py, check_missing.py, classify_changes.py, diff_output.txt"

---

## 6. Recommended Disposition

| Item | Disposition | Target Location | Rationale |
|------|-------------|-----------------|-----------|
| `audit_r1_e.py` | **MOVE** (not delete) | `tools/maintenance/audit_r1_e.py` | Audit utility; belongs under tools/ per TOOLS_POLICY.md |
| `check_missing.py` | **MOVE** (not delete) | `tools/maintenance/check_missing.py` | Classification utility; belongs under tools/ |
| `classify_changes.py` | **MOVE** (not delete) | `tools/maintenance/classify_changes.py` | Classification utility; belongs under tools/ |
| `diff_output.txt` | **MOVE** (not delete) | `artifacts/diff_output.txt` | Diagnostic artifact; belongs under artifacts/ per Root Policy §7 |

**No deletions authorized.** All items have clear provenance as R1-E audit artifacts.

---

## 7. Cleanup Authorization

| Question | Answer |
|----------|--------|
| **Is cleanup authorized?** | **YES — but only as explicit MOVE operations** to proper locations under `tools/maintenance/` and `artifacts/` |
| **Is deletion authorized?** | **NO** — All items have established provenance; deletion would destroy audit evidence |
| **Is staging authorized?** | **NO** — Root remains non-compliant; staging remains BLOCKED until all 4 items relocated |
| **Separate cleanup task required?** | **YES** — A dedicated task to relocate these 4 files to proper directories, then re-run `ntpe_validate.py` |

---

## 8. Final Verdict

### R1-F Root Hygiene Audit = **BLOCKED**

### Summary

| Metric | Value |
|--------|-------|
| Unexpected root paths | 4 (`audit_r1_e.py`, `check_missing.py`, `classify_changes.py`, `diff_output.txt`) |
| Count | 4 |
| Tracked/Untracked/Ignored | All 4 UNTRACKED |
| Protected Worktree items | 0 |
| UNKNOWN items | 4 (all from R1-E UNKNOWN set) |
| R1-related items | 4 (all from R1-E audit execution) |
| Suspected temporary/generated items | 4 (all confirmed) |
| Root Hygiene violations | 4 (Root Policy §3, §4, §7) |
| Cleanup authorized | YES — MOVE only, no DELETE |
| Staging remains blocked | **YES** |

### Deliverables Created

1. `docs/governance/repository/P0_FINAL_12_R1_F_ROOT_HYGIENE_PROVENANCE_AUDIT.md` (this file)
2. `artifacts/P0_FINAL_12_R1_F_Root_Hygiene_Provenance_Audit_Report.json`

**Neither staged nor committed** — audit artifacts only.

---

## 9. Next Steps (Not Part of This Audit)

1. Create `tools/maintenance/` directory if not exists
2. Move `audit_r1_e.py`, `check_missing.py`, `classify_changes.py` → `tools/maintenance/`
3. Move `diff_output.txt` → `artifacts/`
4. Re-run `python ntpe_validate.py` — must PASS
5. Only then may R1 commit proceed

---

**End of Audit Report**
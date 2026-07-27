# NTPE Tools Policy

Date: 2026-07-27T16:59:59+08:00
Version: 1.0
Status: PERMANENT — ACTIVE
Repository: NTPE

---

## Purpose

This policy defines the standard directory structure for developer-facing executable utilities in 	ools/, specifies what kinds of tools belong in which subdirectory, and sets rules for how tools interact with production code and tests.

---

## Tool Categories and Placement

Every new tool must be placed in the correct 	ools/<category>/ directory. Tools placed at 	ools/ root are considered uncategorized and must be moved or deleted during migration.

### 	ools/launchers/

**Stand-Alone Runnable Entry Points**

Executable scripts that launch a pipeline, trigger a stage execution, or invoke a runtime operation. These behave as CLI applications — they accept command-line arguments and are invoked from the shell.

Examples:
- launcher_pipeline_production.py (future location)
- launcher_translate.py (future location)
- Batch processing launchers

**Rules:**
- Must have a if __name__ == "__main__": main() guard
- Must be invokable via python tools/launchers/<name>.py --help
- Must not import from 	ools/launchers/ peers
- May import from core/

---

### 	ools/validators/

**Project and Code Validation Utilities.**

Validator scripts that check the health, layout, or compliance of the repository.

**Existing Examples:**
- 
tpe_validate.py (root shim delegate) → 	ools/validators/ntpe_validate.py (future location)
- 	ools/audit_project_layout.py

**Rules:**
- Must produce deterministic output (JSON or pass/fail exit codes)
- Must not have any side effects on production code
- Results must be serializable to JSON for CI integration

---

### 	ools/maintenance/

**Cleanup, Hygiene, and CI Support Utilities**

One-time or periodic maintenance scripts that clean up, reorganize, or produce reports.

**Examples:**
- 	ools/clean_project.py
- 	ools/package_audit.py
- 	ools/package_source.py
- 	ools/generate_* scripts that produce standardized manifests

**Rules:**
- Must document what it modifies and produce a revert plan in 	ools/maintenance/revert/
- Must not interact with production endpoints or external providers

---

### 	ools/monitoring/

**Observability, Metrics, and Dashboard Helpers**

Tools that produce observations of the running repository, performance dashboards, or pipeline metrics.

**Rules:**
- Must not modify any file under core/ or 	ests/
- May write output to rtifacts/monitoring/

---

### 	ools/recovery/

**Error Recovery and Rollback Utilities**

Recovery scripts for rollback or error recovery operations (provider failures, translation aborts, rollback operations).

**Rules:**
- Must have a reversible operation
- Must produce a relevance manifest
- Must be tested with a dedicated recovery test in 	ests/recovery/

---

### 	ools/migration/

**Data and Schema Migration Scripts**

One-time data migration scripts that transform data formats, upgrade schemas, or migrate configuration from vN to vN+1.

**Rules:**
- Must support a --dry-run flag that produces a plan without mutating
- Must be run with python tools/migration/<script> --plan before execution
- Must produce a migration manifest after execution

---

### 	ools/ Root Cleanup Rule

Files currently at 	ools/ root (not in a subdirectory) will be classified and moved during RM-3 migration:

- Generator scripts → 	ools/maintenance/ or 	ools/migration/
- Tool runners → 	ools/launchers/
- Validators → 	ools/validators/

New tools must always live in a category subdirectory.

---

## Cross-Tool Rules

1. **Tools must not import from other tools** across categories. A monitor must not import a migration script.
2. **Tools must not be imported by core/** or any production runtime code.
3. **Tools must not be imported by 	ests/** except for tests explicitly named testing-tools (i.e., placed in 	ests/tools/)
4. **Tools may produce artifacts** in rtifacts/ or rtifacts/tools/ — not in root.
5. **All executable tools must specify a main(argv) signature** in their module and accept --help, at minimum.

---

## Verification

`	ext
python ntpe_validate.py
`

The validator asserts:
- No tool imported by core/
- No tool at root (except existing wrappers post-migration)
- All tool categories have named subdirectories

---

## Future Contribution Rule

> Any new tool must be in a category subdirectory and must not be imported by production. Tools placed at root are a violation.

---

## Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-07-27 | RM-3.1 Governance Baseline | Initial tools policy |

---

Prepared by: AI assistant using Copilot CLI runtime in VS Code

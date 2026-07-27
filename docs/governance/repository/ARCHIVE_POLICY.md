# NTPE Archive Policy

Date: 2026-07-27T16:59:59+08:00
Version: 1.0
Status: PERMANENT — ACTIVE
Repository: NTPE

---

## Purpose

This policy defines what may be archived in the rchive/ directory, how archiving must be performed, and what constraints apply to archived content.

---

## What May Be Archived

The rchive/ directory is the canonical destination for:

### 1. Historical Stage Artifacts

- Frozen stage scripts and launchers that are no longer part of the active workflow
- Stage output bundles and manifest artifacts from completed stages
- Stage-specific verification reports

### 2. Frozen Validation Evidence

- SHA-256 freeze manifests
- Acceptance boundary contracts
- Regression comparison results from previously completed stages

### 3. Regression Snapshots

- Copy of a test result set used as a reference for future regression comparison
- Provider invocation logs and evidence that are no longer needed for active quality assessment

### 4. Retired Migration Scripts

- Data and schema migration scripts that have been executed and are no longer needed
- Medium-term utility scripts that were part of a one-time migration

### 5. Legacy Benchmarks

- Historical performance and quality benchmarks that are no longer run as part of CI
- Benchmark results and raw data archives

### 6. Deprecated Wrappers (Pre-Governance)

- Root wrappers and compatibility shims that have been migrated to 	ools/ and are covered by new compatibility shims

---

## What Must NOT Be Archived

- Active production code (must remain in core/)
- Active test files (must remain in 	ests/)
- Current configuration (must remain in config/)
- Development workflow tools in current use (must remain in 	ools/)
- The production seed or runtime manifest
- Current live manifests meant for CRUD pipeline

---

## Archive Lifecycle

### Archiving Procedure

1. **Inventory** — List the files to archive with SHA-256 hashes and current paths
2. **Freeze Manifest** — Create a JSON manifest rchive/archive_manifest_<id>.json that records:
   - Source path (before move)
   - Destination path (in rchive/)
   - SHA-256 hash before archiving
   - Human-readable description of what the file does
   - Date archived
3. **Move** — Move the file from original location to rchive/<category>/ where <category> is one of:

`
archive/stages/
archive/validations/
archive/regressions/
archive/migrations/
archive/benchmarks/
archive/wrappers/
archive/evidence/
`

4. **Verify** — Run 
tpe_validate.py after each move to verify no production dependency was broken

### Restore Procedure (if ever needed)

1. Locate the file in rchive/
2. Verify its SHA-256 hash against the frozen manifest
3. Copy (not move) to the target location
4. Run the full test suite
5. Document the restoration in docs/governance/repository/RESTORE_LOG.md

---

## Permanent Archive Rules

1. **Archived files are read-only.** No modification, no mutation, no deletion except via a new archive revision.
2. **Archived files must not be imported** by core/, 	ests/, or any production runtime code.
3. **Archived files must not be executed** by any CI pipeline.
4. **All archive manifests must be frozen** with SHA-256 before movement.
5. **No test coverage is expected or tracked** for files in rchive/.
6. **Every archive operation** must be accompanied by a commit message that includes the archive manifest file name.

---

## Verification

`	ext
python ntpe_validate.py
`

The validator checks that no file in rchive/ is imported by production or test code, and that archive manifests exist.

---

## Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-07-27 | RM-3.1 Governance Baseline | Initial archive policy |

---

Prepared by: AI assistant using Copilot CLI runtime in VS Code

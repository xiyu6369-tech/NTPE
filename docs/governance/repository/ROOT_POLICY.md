# NTPE Root Policy

Date: 2026-07-27T16:59:59+08:00
Version: 1.0
Status: PERMANENT — ACTIVE
Repository: NTPE

---

## Purpose

This policy defines what is permanently permitted and permanently forbidden at the NTPE repository root. The root directory is the most visible and most abused location in any large repository: this policy acts as a gatekeeper to prevent root pollution.

---

## Permitted at Root

Only the following categories of files and directories are permitted at the NTPE repository root:

### 1. Entry Points (Explicit Allowlist)

Production-ready, documented entry scripts that launch the NTPE translation pipeline. These may be:

- Migration-compatible root shims that re-import relocated implementations
- Primary production entry points for external automation and CI/CD
- Validator entry points

The allowlist is maintained in docs/governance/repository/ROOT_ALLOWLIST.md and enforced by 
tpe_validate.py.

### 2. Repository Metadata

- README.md — Repository description, setup instructions, and contribution guide
- VERSION.txt — Single-file version identifier
- equirements.txt — Minimal production dependency list (or any equivalent manifest file)

### 3. Version Control and Tooling Configuration

- .gitignore — Git ignore patterns
- .gitattributes — Git attributes
- .editorconfig — Editor configuration
- Tool-specific ignore and rule files: .clineignore, .clinerules
- CI/CD configuration files

### 4. Minimal Package/Manifest Files

- Package manifest (if applicable to the packaging format): pyproject.toml, setup.py, setup.cfg
- Distribution configuration

### 5. Top-Level Directory Containers

Only directories defined in the REPOSITORY_STRUCTURE_SPEC.md:

`
core/  config/  tools/  tests/  docs/  archive/  artifacts/
manifests/  lts/  protocols/  schemas/  sdk/  cli/  engine/
`

No other top-level directories are permitted without this policy amendment.

---

## Permanently Forbidden at Root

The following items are explicitly and permanently forbidden at the NTPE repository root:

1. **Stage Scripts**
   - Any file whose purpose is to execute or verify a single development stage
   - Any file prefixed with stage*, 
tpe_stage*, 	e_v*_stage*

2. **Verification Scripts**
   - Except 
tpe_validate.py, which is a root-allowlisted validator
   - Any file that performs project validation that belongs in 	ools/validators/

3. **Temporary Utilities or One-shot Tools**
   - Any utility created for a single-use task
   - Workshop scripts, proof-of-concept launchers, experimental modules

4. **Experimental Modules or Prototypes**
   - Any code that is not part of the production path
   - Aboulundered prototypes or feature flags that are not in core/

5. **Test Files**
   - All *_test.py files. All test files must be in 	ests/ or 	ests/<domain>/

6. **Backup Archives or ZIP Files**
   - Full work-tree backups, ZIP, or tar archives
   - Large binaries not managed by Git LFS

7. **Archive Files**
   - Historical documents, legacy scripts, or evidence files must be placed in rchive/ or 	ools/archive/

8. **Duplicate or Markdown Copies of Production Code**
   - Frozen snapshot copies of source code that mimic production

---

## Authorization

Additions to the root must be approved by amending this policy and updating ROOT_ALLOWLIST.md. An agent or developer must validate the addition via:

`	ext
python ntpe_validate.py
`

---

## Enforcement


tpe_validate.py is the root allowlist enforcer. Any file at root not present in the allowlist with a KEEP_ROOT classification is flagged as a policy violation.

`	ext
python ntpe_validate.py
`

The validator checks:
- Allowlist compliance
- Root file count
- Metadata presence
- Known disallowed patterns

---

## Transition Period

During the migration period (NTPE v2.0.0: RM-2 Executing), root files exist that exist pre-Governance. Until RM-2 has completed and all root files are moved or archived, root will contain legacy content. RM-2 will produce a wrapper/shim for each retained entry point that will eventually delegate to 	ools/.

Post-RM-2, root must comply 100% with this policy.

---

## Precedence

This policy overrides previous ad-hoc migration conventions. In case of conflict with any stage-specific plan, this policy wins.

---

## Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-07-27 | RM-3.1 Governance Baseline | Initial permanent root policy |

---

Prepared by: AI assistant using Copilot CLI runtime in VS Code

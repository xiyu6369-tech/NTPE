# NTPE Repository Governance Baseline

Date: 2026-07-27T16:59:59+08:00  
Version: 1.0  
Status: PERMANENT — ACTIVE — THE AUTHORITATIVE GOVERNANCE DOCUMENT  
Repository: NTPE  
Baseline commit: 806ac7c8f45b44dbdf17d1ca81ae9ad590f52d72

---

## What is the Repository Governance Baseline?

The Repository Governance Baseline is the single source of truth for NTPE repository behavior, structure, and contribution rules. It defines the permanent rules and principles that all future migration, development, and cleanup work must follow. This is not a stage plan or a temporary cleanup directive — it is the constitution of the NTPE repository going forward.

Every file, directory, and migration plan from now on must conform to the policies defined here.

---

## Repository Vision

NTPE is a production-grade translation engine repository whose root must remain clean, navigable, and governed. The repository must be understandable by new contributors, CI/CD systems, external agents, and future self. Governance is not optional — it is the precondition for all future work.

Every directory has a single, unambiguous purpose. Every file has a known location. Every migration is reversible and auditable. Every rule is enforced.

---

## Policies Governing the Repository

The following policies are contained in separate documents within docs/governance/repository/. Together they form a complete governance suite. All policies are PERMANENT and ACTIVE unless superseded by a later revision.

| Policy | Document | Description |
|--------|----------|-------------|
| **Structure Spec** | REPOSITORY_STRUCTURE_SPEC.md | Canonical top-level directory map with purposes and rules |
| **Root Policy** | ROOT_POLICY.md | What is permitted and forbidden at repository root |
| **Archive Policy** | ARCHIVE_POLICY.md | What, how, and when to archive into rchive/ |
| **Tools Policy** | TOOLS_POLICY.md | Tool categories, placement, and cross-tool rules |
| **Directory Ownership** | DIRECTORY_OWNERSHIP.md | Per-directory ownership, allowed content, and import boundaries |

All policies are mutually consistent. In case of interpretation conflict, the rule that is more restrictive wins. When multiple policies apply, the stricter interpretation is always the correct one.

---

## Migration Principle

> **No file moves without a plan. No plan without evidence. No evidence without a frozen manifest.**

Every migration or file move must:

1. **Plan** — produce a migration plan listing source, target, classification, and SHA-256 hash of every file to be moved
2. **Freeze** — produce a migration manifest with SHA-256 fingerprint and category
3. **Verify** — run 
tpe_validate.py and full test suite before any movement
4. **Move** — move only after plan, freeze, and verification are completed
5. **Validate** — validate after every batch with 
tpe_validate.py

Wrappers are always preferred over imports when a file was multiply referenced by manifests, artifacts, or external documentation.

---

## Compatibility Principle

When moving or refactoring a file that is referenced by other code, manifes, documentation, artifacts, or external automation:

- A root compatibility shim (wrapper or re-export) must exist with the original root filename
- The shim must preserve CLI semantics if the original was a direct shell invocation
- Compatibility shims must be documented in docs/governance/migration/RETAINED_ROOT_WRAPPERS.json
- Shim life cycle: new shims are allowed; after all consumers have migrated, the shim may be archived

---

## Wrapper Principle

A wrapper is a thin Python file at root (or migrated location) that delegates to the actual implementation. Wrappers are never more than 10 lines of Python.

Wrapper Types:
1. **Import Shipper:** rom tools.launchers.Launch_pipeline_production import main; main()
2. **Re-export Module:** rom providers.ntpe_provider_setup import * in 
tpe_provider_setup.py

All wrappers must:
- Be recorded in a consolidated manifest
- Not produce custom imports or extra surfaces beyond the original file
- Not contain business logic

---

## Archive Principle

Every file archived to rchive/ must be frozen with a SHA-256 manifest. No archived file is ever imported or referenced by production or tests. Archive is read-only.

Once archived, a file's SHA-256 must not change. Restored files are copied (not moved) and must be re-verified with come_ntpe_validate.py.

---

## Root Principle

Only Entry Points, Repository Metadata, and configuration files may live at the NTPE root. All other files must live in core/, 	ests/, 	ools/, rchive/, or other canonical directories defined in REPOSITORY_STRUCTURE_SPEC.md.

The root allowlist is enforced by 
tpe_validate.py.

---

## Future Contribution Rule

> **Any new file added to the repository must conform to the Repository Governance Baseline before it can be merged into the main branch.**

This applies to every new addition regardless of contributor, agent, or automation tool. No exception.

Validation steps before merge:
1. Does the file belong at its target location per REPOSITORY_STRUCTURE_SPEC.md?
2. Is it permitted by DIRECTORY_OWNERSHIP.md?
3. Does it violate ROOT_POLICY.md?
4. Is it properly categorized per TOOLS_POLICY.md?
5. Does 
tpe_validate.py pass with zero errors?
6. Are any new imports traversed of boundaries established in the Directory Ownership policy?

---

## Validation and Enforcement

### Primary Validator

`	ext
python ntpe_validate.py
`

### Checks enforced

- Root allowlist compliance (ROOT_ALLOWLIST.md)
- Root file count
- Archive integrity (no production/tests imports from archive)
- Tool placement rules and cross-boundary violations
- Regulation, and all metadata presence

### CI Integration

The governance baseline must be validated in CI on every commit to the main brach. A step running python ntpe_validate.py with a pass-or-block policy.

---

## Governance Hierarchy

`
REPOSITORY_GOVERNANCE_BASELINE.md  ← THIS DOCUMENT (master authority)
├── REPOSITORY_STRUCTURE_SPEC.md   ← structure rules
├── ROOT_POLICY.md                 ← root rules
├── ARCHIVE_POLICY.md              ← archive rules
├── TOOLS_POLICY.md                ← tools rules
└── DIRECTORY_OWNERSHIP.md         ← ownership rules
`

All migration plans (RM-0, RM-1, RM-2, RM-3, RM-4+) must align to these policies.

---

## Revision

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-07-27 | RM-3.1 Repository Governance Baseline | Initial permanent baseline. All prior migration plans are consistent with or upgraded towards this baseline. |

---

## End of Governance Baseline

This is the permanent, authoritative governance document for the NTPE repository. It may be superseded only by a subsequent version of this document.

All agents, contributors, and CMS maintainers must comply.

---

Prepared by: AI assistant using Copilot CLI runtime in VS Code

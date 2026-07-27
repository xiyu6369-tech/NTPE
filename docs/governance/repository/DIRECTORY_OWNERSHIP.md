# NTPE Directory Ownership

Date: 2026-07-27T16:59:59+08:00
Version: 1.0
Status: PERMANENT — ACTIVE
Repository: NTPE

---

## Purpose

This document defines ownership rules for every canonical top-level directory in the NTPE repository. Ownership includes who may add files, what types of files are permitted, and what boundaries are enforced.

---

## Ownership Table

### core/

| Attribute | Value |
|-----------|-------|
| **Purpose** | Production Runtime |
| **Owned By** | Core Engineering Team |
| **Permitted** | Python packages; production modules; provider adapters; quality, prompt, and translation engine |
| **Forbidden** | Test files; experimental code; one-shot launchers; stage scripts; historical snapshots |
| **Import Boundary** | All subpackages are core.*; must not import from 	ools/ or rchive/ |
| **Verification** | 
tpe_validate.py checks for forbidden patterns |

### 	ests/

| Attribute | Value |
|-----------|-------|
| **Purpose** | All pytest automated tests |
| **Allowed** | Test files (*_test.py); test fixtures (conftest.py); test resources; bench test files |
| **Forbidden** | Production launchers; executable entry points; standalone CLI scripts that are not tests |
| **Import Boundary** | May import from core/; may import from 	ools/ only for tool-validation tests |
| **Organization Rule** | Organized by domain: 	ests/architecture, 	ests/regression, 	ests/unit, 	ests/integration, etc. |

### 	ools/

| Attribute | Value |
|-----------|-------|
| **Purpose** | Developer-facing executable utilities |
| **Allowed** | Launchers, validators, maintenance, monitoring, recovery, migration scripts |
| **Forbidden** | Production runtime code; test files; historical archives |
| **Import Boundary** | Must not import from other tools across categories; must not be imported by core/ or 	ests/ |
| **Organization Rule** | All tools must be in a category subdirectory (see TOOLS_POLICY.md) |

### rchive/

| Attribute | Value |
|-----------|-------|
| **Purpose** | Read-only historical and legacy artifacts |
| **Allowed** | Historical stages; frozen validations; regression snapshots; retired migration scripts; legacy benchmarks; deprecated wrappers |
| **Forbidden** | Active production code; active tests; current configuration; files newer than the archive date |
| **Import Boundary** | Never imported by production, tests, or tools |
| **Mutation Rule** | Read-only; all archived files frozen with SHA-256 manifest |

### docs/

| Attribute | Value |
|-----------|-------|
| **Purpose** | Project documentation |
| **Allowed** | Governance docs; stage READMEs; SDK docs; release notes; roadmaps; architecture documents |
| **Forbidden** | Production code; scripts; large binary files |
| **Import Boundary** | Not importable; documentation only |

### rtifacts/

| Attribute | Value |
|-----------|-------|
| **Purpose** | Stage- and instance-frozen artifacts |
| **Allowed** | Move maps; validation manifests; freeze bundles; stage evidence; monitoring outputs |
| **Forbidden** | Active runtime code; test files |
| **Import Boundary** | Must not be imported by production code |

### config/

| Attribute | Value |
|-----------|-------|
| **Purpose** | Central configuration hub |
| **Allowed** | Project layout policy; character overrides; provider config; profile config; environment config; manifest references |
| **Forbidden** | Scripts; batch execution files; production runtime code |
| **Import Boundary** | May be consumed by core/ as read-only; never mutated by runtime |

### manifests/

| Attribute | Value |
|-----------|-------|
| **Purpose** | Automation and verification manifests |
| **Allowed** | JSON manifests; SHA freeze manifests; DAG definitions; acceptance contracts |
| **Forbidden** | Python source; executable scripts; documentation |
| **Import Boundary** | Consumed by tools and CI; never imported by production runtime or tests |

### lts/

| Attribute | Value |
|-----------|-------|
| **Purpose** | Long-Term Support Frozen Runtime |
| **Allowed** | Stable, frozen runtime distributions; LTS version manifests |
| **Forbidden** | Experimental code; development wrappers; test fixtures |
| **Import Boundary** | External versions; must not import from development-only code paths |

### ngine/ / cli/ / sdk/ / schemas/ / packaging/

| Attribute | Value |
|-----------|-------|
| **Purpose** | Supporting production development tools and distribution |
| **Allowed** | SDK libraries; CLI distribution; interface schemas; package scripts |
| **Forbidden** | Experimental changes; historical snapshots |
| **Import Boundary** | Interact via core/ but never import from non-production directories |

---

## Cross-Directory URL Violation Rules

1. No directory imports from a lower-authority directory. 	ests/ may import from 	ools/ only for tool tests.
2. No circular directory imports.
3. All core/* subpackages must provide a stable __init__.py that exports the public API.
4. All directories that produce frozen artifacts must provide an inventory with SHA-256.

---

## Contribution Procedure

1. Identify the correct directory per this ownership table
2. Verify that the addition is permitted by that directory's **Allowed** list
3. Validate via 
tpe_validate.py
4. Document the change in the corresponding policy if it introduces a new pattern

---

## Revision

| Attribute | Value |
|-----------|-------|
| **Version** | 1.0 |
| **Date** | 2026-07-27 |
| **Author** | RM-3.1 Repository Governance Baseline |

---

Prepared by: AI assistant using Copilot CLI runtime in VS Code

# NTPE Repository Structure Specification

Date: 2026-07-27T16:58:59+08:00
Version: 1.0
Status: ACTIVE
Repository: NTPE
Baseline commit: 806ac7c8f45b44dbdf17d1ca81ae9ad590f52d72

---

## Purpose

This specification defines the canonical top-level directory structure of the NTPE repository. Every directory listed here serves a distinct, non-overlapping purpose. No file may be placed at the root or within any directory unless its purpose matches the directory definition below.

---

## Canonical Top-Level Directory Map

### core/

**Production Runtime.**

Contains all production Python packages and modules that constitute the NTPE translation engine runtime. This includes:

- Translation pipeline orchestration
- AI provider adapters and routing
- Quality assessment and enforcement engines
- Prompt compilation and discipline frameworks
- Character memory and context intelligence
- Translation reliability and recovery subsystems
- Adaptive context engine
- Controlled runtime scheduling and admission

**Rules:**
- All code in core/ is production-grade
- No experimental or one-shot code
- No test files (tests belong in 	ests/)
- No historical or frozen stage snapshots
- All imports are from core.* subpackages

---

### 	ests/

**Automated Test Suite**

All pytest-based automated tests for the repository. Tests are organized by domain (architecture, regression, unit, integration, quality, etc.).

**Rules:**
- All files must be discoverable by a root-level pytest invocation
- No production launchers or executable entry points
- Test files may import from core/ and other production packages
- Test files may import from 	ools/ only for tool-validation tests

---

### 	ools/

**Developer-Facing Executable Utilities.**

Never imported by the NTPE runtime. Contains launchers, validators, code generators, maintenance scripts, recovery utilities, migration tools, and monitoring utilities. Subdivided by category:

- 	ools/launchers/ — stand-alone runnable entry points
- 	ools/validators/ — project validation and audit tools
- 	ools/maintenance/ — cleanup, migration, and CI support
- 	ools/monitoring/ — dashboard, metrics, and observability helpers
- 	ools/recovery/ — error recovery and rollback utilities
- 	ools/migration/ — schema and data migration scripts

**Rules:**
- Must not import from core/ unless operating as a controlled entry-point wrapper
- Must not be imported by core/ or any production runtime code
- All new tools must be placed here, not at root

---

### rchive/

**Read-Only Historical and Legacy Artifacts.**

Contains frozen stage snapshots, retired migration scripts, legacy benchmarks, historical validation reports, preserved regression evidence, and historical launchers that are no longer part of active workflow.

**Rules:**
- Read-only once archived
- Never imported by production runtime
- Never imported by 	ests/
- Archived files retain original SHA-256 hashes

---

### docs/

**Project Documentation.**

Repository-level documentation, including governance documents, stage READMEs, SDK documentation, release notes, roadmaps, and audit reports. Subdivided by domain:

- docs/governance/ — repository governance policies
- docs/stages/ — per-stage architecture and outcome documentation
- docs/releases/ — release notes and freeze documentation
- docs/sdk/ — developer SDK documentation
- docs/roadmap/ — product roadmap

---

### rtifacts/

**Freeze-Locked Stage and Instance Evidence.**

Machine-generated and human-verified artifacts produced during stage execution. Contents include move maps, verification manifests, freeze bundles, and stage evidence.

**Rules:**
- Read-only after stage freeze
- Never imported by production code
- Contains SHA-256 hashed manifests for every destructive operation

---

### config/

**Repository and Project Configuration.**

Configuration files consumed by the runtime and tools, including project layout policy, project profiles, deployment configuration, and launch manifests.

---

### lts/

**Long-Term Support Runtime.**

Stable, frozen, backwards-compatible runtime distributions for enterprise deployment. LTS packages must not be modified after freeze except for critical security patches.

**Rules:**
- Only production-stable runtimes
- Frozen after release candidate validation
- All changes require a new LTS version identifier

---

### manifests/

**Automation and Verification Manifests.**

JSON manifests that freeze hashes, DAGs, and acceptance boundaries for CI and validation pipelines.

---

## Forbidden Top-Level Patterns

The following directory patterns are **never permitted** at repository root:

- Stage-specific subdirectories (e.g., stage_7/)
- Workspace backup directories (e.g., ackup/, old/, NTPE.zip)
- Per-developer directories
- Chat/agent session files (.ai/, .codex/ excluded from root by tooling)
- Temporary runtime output directories (output/, 	mp/)

---

## Visual Reference (Target Layout)

`
NTPE/
├── README.md
├── VERSION.txt
├── requirements.txt
├── .gitignore
├── .gitattributes
├── .editorconfig
├── core/                   # Production runtime
├── tests/                  # Automated test suite
├── tools/                  # Developer utilities
│   ├── launchers/
│   ├── validators/
│   ├── maintenance/
│   ├── monitoring/
│   ├── recovery/
│   └── migration/
├── archive/                # Read-only historical artifacts
├── docs/                   # All documentation
├── artifacts/              # Freeze-locked stage artifacts
├── config/                 # Central configuration
├── manifests/              # Automation manifests
├── lts/                    # Long-term support runtimes
├── profiles/               # Deployment profiles
├── packaging/              # Distribution packaging
├── schemas/                # JSON and interface schemas
├── config/
├── engine/
├── sdk/
└── cli/
`

---

## Version History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-07-27 | RM-3.1 Governance Baseline | Initial specification |

---

Prepared by: AI assistant using Copilot CLI runtime in VS Code  
Approval: RM-3.1 Repository Governance Baseline

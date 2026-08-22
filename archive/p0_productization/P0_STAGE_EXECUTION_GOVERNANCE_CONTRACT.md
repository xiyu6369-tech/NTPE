# P0 Stage Execution Governance Contract

This contract establishes mandatory execution rules for all subsequent P0 Stages (Stage 3 and beyond) to ensure compliance with NTPE Repository Governance Baseline. Violations of any clause shall result in immediate Stage failure.

## 1. Root-Level Artifact Prohibition
- Creating any file or directory at the repository root is strictly prohibited.
- Only the following categories are permitted at root (as defined in `ROOT_POLICY.md` and `REPOSITORY_STRUCTURE_SPEC.md`):
  - Entry Points (e.g., `main.py`, `run.py`)
  - Repository Metadata (`.gitignore`, `.gitattributes`, `LICENSE`, `README.md`)
  - Version Control (`.git/` directory)
  - Minimal Package/Manifest (`pyproject.toml`, `setup.cfg`, `requirements.txt`)
  - Top-Level Directory Containers (`docs/`, `src/`, `tools/`, `artifacts/`, `tests/`, `archive/`, `config/`, `kilo/`)
- Any untracked or modified file/directory outside these categories at root triggers validation failure.

## 2. Artifact Output Location
- All reports, logs, intermediate files, and Stage-specific outputs must be placed under `artifacts/p0_productization/` or other explicitly approved subdirectories under `artifacts/`.
- No Stage output may be written to root, `src/`, `tools/`, `tests/`, `archive/`, or any other directory without explicit governance approval.

## 3. Pre‑Stage Root Hygiene Check
- Before Stage execution begins, the runner must invoke `ntpe_validate.py --root-only` (or equivalent) and verify a clean root state matching the baseline recorded in `P0_STAGE0_PREFLIGHT_COMPLETE.md`.
- Any deviation (new, modified, or deleted root items not permitted by the baseline) aborts the Stage.

## 4. Post‑Stage Validation
- At Stage completion, `ntpe_validate.py` must be executed with full scope and return **ALL PASS**.
- Validation includes: project layout compliance, import restrictions, compile‑all cleanliness, and git diff checks.

## 5. Governance References
This contract incorporates and enforces the following existing governance documents:
- `docs/governance/repository/ROOT_POLICY.md`
- `docs/governance/repository/REPOSITORY_STRUCTURE_SPEC.md`
- `docs/governance/repository/DIRECTORY_OWNERSHIP.md`
- `config/project_layout_policy.json`
- Validation logic in `tools/audit_project_layout.py` and `ntpe_validate.py`

## 6. Enforcement
- The contract is considered part of the Stage acceptance criteria.
- Stage automation scripts and human executors must treat these rules as non‑negotiable constraints.
- Failure to comply invalidates the Stage outcome and requires remediation before proceeding.

Effective immediately for all P0 Stage 3+ executions.
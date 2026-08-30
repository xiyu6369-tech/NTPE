# P0 Stage 5 Root-Level Inventory

## Scope

- Review type: read-only Root Hygiene inventory for the P0 Stage 5 Final Acceptance / Freeze Review.
- Repository: `D:\Python\NTPE`
- Review date: 2026-08-22
- Baseline: `61fc7d359a9e3e1e51c66b0909aec86a3baf3831`
- Covered delivery commits: Batch 5.1 through Batch 5.8.1 (`24f1dea` through `61fc7d3`).
- Restrictions honored: no deletion, move, content edit, staging, commit, or push of existing project files.

## Evidence Boundary

The local checkout is the source of truth. At review time, the worktree is intentionally dirty with pre-existing B/C/D changes. Git reports the following root-level items as untracked or changed:

- `P0_STAGE5_INTEGRATED_REVIEW.md` — untracked review draft.
- `dummy.txt` — untracked 36-byte glossary scratch file.
- Existing tracked root files and directories are otherwise present in `HEAD`; several older cleanup deletions and unrelated worktree changes are also present.

The earlier project ZIP mirror is not used for current-state classification because it predates the Stage 5 delivery commits and does not contain the current Final Acceptance material.

## Root-Level Classification

| Item | Current state | Classification | Decision for Stage 5 freeze |
|---|---|---|---|
| `README.md` | Tracked, established root metadata | `KEEP_ROOT` | Retain. Required for clone/download discoverability. |
| `VERSION.txt` | Tracked, established root metadata | `KEEP_ROOT` | Retain. |
| `requirements.txt`, `pyproject.toml` | Tracked project metadata | `KEEP_ROOT` | Retain. |
| `.gitignore`, `.gitattributes`, `.editorconfig`, `.clineignore`, `.clinerules` | Tracked repository/tooling metadata | `KEEP_ROOT` | Retain. |
| `ntpe_validate.py` | Tracked validator entrypoint | `KEEP_ROOT` | Retain at root or replace only through an approved shim plan. |
| `launcher_translate.py`, `ntpe_batch_monitor.py`, `ntpe_launcher.py`, `ntpe_production_translate.py` | Tracked production/compatibility entrypoints | `KEEP_ROOT` | Retain pending a separately approved migration. |
| `ntpe_*provider*`, `ntpe_controlled_real_provider_retry.py`, `ntpe_single_real_provider_invocation.py`, `ntpe_literary_*` | Tracked legacy/compatibility entrypoints; currently deleted in worktree | `PRE_EXISTING_WORKTREE_CHANGE` | Do not clean up during Stage 5 review. Preserve the user's existing deletion changes. |
| `core/`, `lts/`, `docs/`, `tests/`, `tools/`, `config/`, `manifests/`, `artifacts/`, `archive/`, `engine/`, `schemas/`, `sdk/`, `cli/`, and other tracked containers | Established repository structure | `PRE_EXISTING_TRACKED_STRUCTURE` | No Stage 5 root-hygiene action. |
| `P0_STAGE5_INTEGRATED_REVIEW.md` | Untracked, modified 2026-08-22 02:53 | `REVIEW_WORKING_FILE` | Preserve for the current review. After acceptance, move the finalized report under `docs/governance/rm8/` in a separate documented delivery. |
| `dummy.txt` | Untracked, created/modified 2026-08-20 23:49; content is two glossary mappings | `ROOT_HYGIENE_VIOLATION` | Do not delete now. Verify no consumer, then remove or archive only in the post-project cleanup stage. It must not enter the final deliverable root. |
| `.pytest_cache/`, `.kilo/`, `.vscode/`, `.ai/`, `.agents/`, `.codex/` | Local/tooling directories; not part of the Stage 5 production scope | `LOCAL_OR_PRE_EXISTING_METADATA` | Do not alter during this review. Confirm ignore/clone policy during final repository cleanup. |
| `logs/`, `output/`, `backup/`, `translation_cache/`, and similar runtime containers | Runtime/generated locations, ignored or operational | `RUNTIME_ARTIFACT_CONTAINER` | Keep operational behavior unchanged; ensure no generated contents are committed. |
| `RM_6_4_0_ACCEPTANCE_REPORT.md`, `RM_7_3_1_ACCEPTANCE_REPORT.md` | Older tracked root reports, currently deleted in worktree | `PRE_EXISTING_CLEANUP_CHANGE` | Leave untouched for this task; resolve only under the existing cleanup plan. |

## Batch 5.x Attribution

No Batch 5.1–5.8.1 commit adds a new root-level production file. The committed Batch 5 changes are under `core/`, `tests/`, and `docs/governance/rm8/`; Batch 5.8.1 is committed at `61fc7d3` with six paths and no root-level addition.

The root-level review draft and `dummy.txt` are not part of the Batch 5.8.1 atomic commit. Their timestamps overlap the Batch 5 work window, but timestamp overlap alone is insufficient to attribute them to a delivery batch. They remain untracked worktree artifacts and must be handled separately.

## Root Hygiene Findings

### BLOCKER / HIGH

None established from this read-only inventory.

### MEDIUM

1. `dummy.txt` violates the active root policy because it is an untracked scratch/data file at repository root. It is not required for Batch 5 runtime behavior based on the current inventory, but consumer absence should be confirmed before final cleanup.
2. `P0_STAGE5_INTEGRATED_REVIEW.md` is a useful review artifact but is incorrectly located at root for a final repository state. It should remain untouched during review and be relocated only after the review is finalized.

### LOW / ACCEPTED

1. Existing root wrappers, runtime containers, and local tool metadata are pre-existing or operational. They are not evidence of a Batch 5 regression by themselves.
2. Existing deleted root scripts and reports are preserved as user worktree changes and are outside this read-only audit's authority.

## Freeze Decision Input

Root-level state is **not clean enough to call the repository final-delivery ready** because of untracked root artifacts, especially `dummy.txt`. This does not invalidate the Batch 5.8.1 baseline or its atomic commit. For Stage 5 Final Acceptance, record Root Hygiene as:

> `ACCEPTED WITH NON-BLOCKING DEBT` for architecture freeze, with post-project cleanup required before the final clone/download release.

The final acceptance report should keep this repository-hygiene debt separate from the Stage 5 production architecture verdict. No cleanup should be performed as part of the Stage 5.8.1 delivery or this inventory.

## Required Follow-Up After Project Completion

1. Verify that `dummy.txt` has no runtime, test, manifest, or documentation consumer.
2. Move the finalized Stage 5 Final Acceptance report from root into `docs/governance/rm8/`.
3. Reconcile ignored/local directories against the active root policy and clone/download expectations.
4. Resolve pre-existing deleted root files and all unrelated B/C/D worktree changes in their own atomic cleanup batches.
5. Run the repository validator and root-hygiene checks only after the cleanup plan is approved; do not stage or commit as part of this review.


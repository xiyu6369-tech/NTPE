NTPE Root Allowlist (freeze snapshot)

Date: 2026-07-27T14:25:01+08:00

Purpose: Minimal list of files and directories that should remain at repository root by governance policy until migration is fully planned and executed.

Allowed at root (KEEP_ROOT):

- README.md  — Repository entry documentation
- VERSION.txt  — Repository version
- requirements.txt  — Dependencies listing
- .gitignore, .gitattributes, .editorconfig — VCS and tooling config
- config/ — Project configuration
- manifests/ — Release and automation manifests
- core/ — Core runtime package (production code)
- engine/ — Engine runtime package (production code)
- tools/ — Top-level tools directory (may contain launchers)
- docs/ — Documentation (including docs/governance/)
- tests/ — Test suite
- ntpe_validate.py — Project validator (must remain accessible at root or via shim)

Notes and rationale:
- Production entrypoints (launcher pipeline and production translate) are currently referenced by manifests/artifacts; keep them at root or provide compatibility shims if implementations move.
- The allowlist is intentionally conservative: anything not on this list should be reviewed (REVIEW classification) in the ROOT_INVENTORY_FREEZE.json before moving.

Next steps:
1. Use ROOT_INVENTORY_FREEZE.json to drive automated per-file dependency analysis for MOVE candidates.
2. For each MOVE candidate, produce a wrapper/shim plan if external references exist.
3. Approve and stage small atomic moves with tests/CI validation.

Prepared by: AI assistant using Copilot CLI runtime in VS Code

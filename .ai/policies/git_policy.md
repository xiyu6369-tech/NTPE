# Policy: git_policy

## Title
Git Policy — Version Control Governance

## Purpose
This policy governs all git operations performed by AI agents within the NTPE workspace. It defines which operations are permitted, which require explicit human authorization, and the validation steps required before any git state change.

## Scope
- Applies to all agent profiles and all development stages
- Covers commit, push, tag, branch, and merge operations
- Works in conjunction with `.clinerules` forbidden operations list

## Commit Policy

### Agent commits are FORBIDDEN
AI agents must **never** execute `git commit` unless:
- The human user explicitly authorizes a specific commit, per operation
- Authorization must be clear and unambiguous (e.g., "commit these changes with message X")
- The agent must not interpret general approval as commit authorization

### Pre-Commit Validation (for human-authorized commits only)
Before any authorized commit, the agent must:
1. Run `git diff --check` — verify whitespace/line-ending compliance
2. Run `git diff --stat` — confirm scope matches intended changes
3. Run `git status --short` — confirm no unintended files are staged
4. Verify no frozen layer files appear in the diff
5. Confirm all relevant tests pass

## Push Policy

### Agent pushes are FORBIDDEN
AI agents must **never** execute `git push` to any remote. This operation requires direct human execution.

## Tag Policy

### Agent tags are FORBIDDEN
AI agents must **never** execute `git tag`. Version tagging is a release management decision requiring human judgment and explicit execution.

## Permitted Git Operations

The following read-only operations are permitted without authorization:
- `git status --short` — check workspace state
- `git diff --check` — validate whitespace compliance
- `git diff --stat` — summarize changes
- `git log` (with reasonable limits) — review history
- `git branch --list` — list local branches

## Branch Operations
- Creating a new local branch (`git checkout -b`) requires explicit human authorization
- Switching branches (`git checkout`, `git switch`) requires explicit human authorization
- Merging branches requires explicit human authorization

## Future Update Notes
- May add signed-commit requirements for human-authorized commits
- Consider integrating with branch protection rules if moved to GitHub flow
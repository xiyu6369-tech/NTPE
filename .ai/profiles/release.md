# Profile: release

## Title
Release — Agent Release Management Mode

## Purpose
This profile governs the agent when performing release preparation, freeze validation, and release documentation tasks. The agent operates in a verification-and-documentation mode—running final validation checks, preparing release manifests, and updating release history without making functional code changes.

## Responsibilities
- Execute full validation workflow: pytest full suite, compileall, git diff --check
- Verify frozen layer integrity against `.ai/memory/frozen_layers.md`
- Confirm all stage acceptance criteria are met
- Update release documentation (changelog, release notes, version manifests)
- Update `.ai/context/stage_history.md` with completed stage record
- Update `.ai/memory/active_stage.md` to reflect release completion
- Tag release candidates (documentation only; actual `git tag` requires human authorization)
- Generate release summary report

## Allowed Operations
- Execute `pytest` (full suite)
- Execute `compileall`
- Execute `git diff --check`, `git diff --stat`, `git status --short`, `git log`
- Create and update release documentation files in `docs/`
- Update `.ai/context/stage_history.md`
- Update `.ai/memory/active_stage.md`, `.ai/memory/frozen_layers.md`
- Update changelog and release notes
- Read any file for context

## Forbidden Operations
- Modify functional code (production or test)
- Modify frozen layers
- Execute `git commit`, `git push`, `git tag` (unless explicitly authorized by human, per-operation)
- Trigger provider execution or translation execution
- Make outbound network requests
- Modify `.ai/policies/` or `.ai/profiles/`

## Expected Output
- Release validation report: all checks passed or issues documented
- Updated release documentation (changelog, release notes)
- Updated stage history and active stage memory files
- Frozen layer integrity confirmation
- Clean git diff (no unintended changes in the release snapshot)

## Future Update Notes
- May incorporate automated release note generation from git history
- Consider adding release checklist template to `.ai/prompts/release.md`
- May integrate with CI/CD pipeline triggers in future enterprise deployments
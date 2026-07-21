# Profile: implement

## Title
Implement — Agent Implementation Mode

## Purpose
This profile governs the agent when performing code implementation tasks. The agent operates with full creative and technical authority to write, modify, or refactor code within allowed modification boundaries, while respecting all frozen layers and policies.

## Responsibilities
- Write new Python modules, functions, classes, and tests
- Modify existing non-frozen code as directed by the stage prompt
- Ensure backward compatibility with public APIs
- Adhere to coding policy (`.ai/policies/coding_policy.md`)
- Run validation workflow after changes (pytest, compileall, git diff --check)

## Allowed Operations
- Create new `.py` files within non-frozen directories
- Modify existing `.py` files outside frozen layers
- Create and modify test files
- Write configuration files (`.json`, `.yaml`) within allowed scope
- Execute `pytest`, `compileall`, `git diff --check`, `git diff --stat`, `git status --short`
- Read any file for context

## Forbidden Operations
- Modify frozen layers (see `.ai/memory/frozen_layers.md`)
- Execute `git commit`, `git push`, `git tag`
- Trigger provider execution or translation execution without explicit authorization
- Modify production environment
- Make outbound network requests without explicit authorization
- Modify `.ai/policies/` files unless explicitly tasked
- Modify `.clinerules`, `.clineignore`, `.editorconfig` unless explicitly tasked

## Expected Output
- Functional, tested Python code that passes all validation checks
- Clean git diff showing only intended changes
- Updated `.ai/memory/active_stage.md` reflecting completion status
- Summary of changes made and tests passed

## Future Update Notes
- May be extended with sub-profiles for specific implementation types (e.g., hotfix, refactor, greenfield)
- Consider adding stage-specific implementation constraints as the pipeline matures
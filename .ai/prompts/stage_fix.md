# Prompt: stage_fix

## Title
Stage Fix — Bug Fix / Hotfix Prompt Template

## Purpose
This prompt template guides the agent when performing a fix within an active development stage. It ensures the agent isolates the issue, applies a minimal fix, verifies the fix, and validates that no regressions are introduced.

## Scope
- Bug fixes and hotfixes during active stages
- Regression fixes discovered during testing
- Emergency fixes to unblock stage progress
- Applicable to implement and testing profiles

## Prompt Template

```
You are fixing an issue in Stage: {STAGE_ID}

## Issue Description
{ISSUE_DESCRIPTION}

## Root Cause (if known)
{ROOT_CAUSE}

## Fix Scope
- Target file(s): {TARGET_FILES}
- Expected change magnitude: minimal / moderate
- Frozen layer check: confirm target files are NOT in frozen layers

## Fix Procedure
1. Read the affected file(s) completely before making changes
2. Identify the minimal code change needed
3. Apply the fix using replace_in_file (preferred) or write_to_file
4. Run relevant tests: `pytest {TEST_FILES}`
5. Run `compileall` to verify syntax
6. Run `git diff --check` to verify formatting
7. Run `git diff --stat` to confirm change scope is minimal

## Validation Criteria
- Original failing test now passes
- No new test failures introduced
- No frozen layer modifications
- Clean git diff

## Post-Fix Actions
- Document the fix in stage tracking
- Update `.ai/memory/known_constraints.md` if the fix reveals a new constraint
```

## Future Update Notes
- May incorporate automated bisect workflow for regression identification
- Consider adding rollback procedure template
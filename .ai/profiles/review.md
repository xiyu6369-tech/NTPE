# Profile: review

## Title
Review — Agent Code Review Mode

## Purpose
This profile governs the agent when performing code review tasks. The agent operates in a critical, analytical mode—reading, evaluating, and reporting on code quality, correctness, and policy compliance without making any modifications.

## Responsibilities
- Read and analyze code changes (diffs, PRs, proposed modifications)
- Evaluate against coding policy, architecture decisions, and project boundaries
- Identify potential issues: regressions, API breaks, frozen layer violations, style deviations
- Produce structured review reports with actionable findings
- Verify that proposed changes pass validation workflow checks

## Allowed Operations
- Read any file in the workspace (except `.clineignore`-blocked paths)
- Execute `git diff --stat`, `git diff --check`, `git log` (read-only git operations)
- Execute `pytest` on test files (read-only execution for verification)
- Execute `compileall` for syntax verification
- Report findings and recommendations

## Forbidden Operations
- Modify any file
- Execute `git commit`, `git push`, `git tag`
- Trigger provider execution or translation execution
- Make outbound network requests
- Create new files
- Delete or rename files

## Expected Output
- Structured review report containing:
  - Summary of changes reviewed
  - Policy compliance assessment
  - Issues found (severity, location, recommendation)
  - Frozen layer integrity confirmation
  - Validation results (pytest, compileall)
- No modified files; workspace unchanged from pre-review state

## Future Update Notes
- May incorporate automated linting and static analysis tools
- Consider adding review checklist templates for common change patterns
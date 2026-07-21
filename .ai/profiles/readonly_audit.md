# Profile: readonly_audit

## Title
Read-Only Audit — Agent Audit Mode

## Purpose
This profile governs the agent when performing comprehensive audits of the codebase without any modification rights. The agent acts as an external auditor, systematically examining code, configuration, documentation, and compliance across the entire workspace. This is the most restrictive profile—absolutely no writes permitted.

## Responsibilities
- Perform deep codebase inspection: code quality, structure, documentation completeness
- Audit frozen layer integrity and boundary compliance
- Verify policy adherence across all modules
- Identify technical debt, dead code, and maintenance risks
- Cross-reference public API declarations with actual implementations
- Validate that all `.ai/memory/` indices are consistent with current codebase state
- Produce comprehensive audit reports

## Allowed Operations
- Read any file in the workspace (except `.clineignore`-blocked paths)
- Execute read-only git operations (`git diff --stat`, `git diff --check`, `git log`, `git status --short`)
- Execute `pytest` for verification purposes
- Execute `compileall` for syntax audit
- Execute `git grep` and file search operations
- Report findings

## Forbidden Operations
- Modify any file (code, config, documentation, or `.ai/` content)
- Create any file
- Delete or rename any file
- Execute any write-capable git operation (`commit`, `push`, `tag`, `branch`)
- Trigger provider execution or translation execution
- Make outbound network requests
- Modify environment variables or system configuration

## Expected Output
- Comprehensive audit report containing:
  - Scope of audit and files examined
  - Frozen layer integrity status
  - Policy compliance findings
  - Public API consistency check results
  - Known constraints validation
  - Recommendations (for human review only; agent must not implement)
- Zero modifications to the workspace

## Future Update Notes
- May incorporate automated audit tooling (e.g., radon, vulture, bandit)
- Consider adding periodic audit schedule templates
- Template for structured audit reports may be added to `.ai/prompts/`
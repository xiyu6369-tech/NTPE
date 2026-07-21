# Memory: known_constraints

## Title
NTPE Known Constraints — Current Limitations and Issues

## Purpose
This memory file tracks known constraints, limitations, and technical debt in the NTPE project. AI agents reference this to understand what can't be done, why, and what workarounds exist. It prevents repeated investigation of known issues.

## Scope
- Technical limitations (design or platform constraints)
- Known bugs that cannot be immediately fixed
- Workarounds and their trade-offs
- Deprecated features and migration status
- Does not record stage-specific acceptance criteria (see `.ai/prompts/acceptance.md`)

## Known Constraints

### Constraint Template
When adding a new constraint:

```
### KC-{number}: {Title}

**Date Identified**: {YYYY-MM-DD}
**Status**: {ACTIVE / WORKAROUND / RESOLVED}
**Source**: {stage_id or context}

**Description**:
{What the constraint is}

**Impact**:
{What it affects}

**Workaround**:
{How to work around it, if any}

**Resolution Plan**:
{How/when this will be resolved, if planned}
```

### KC-001: Python Version Compatibility

**Date Identified**: 2026-07-21
**Status**: ACTIVE
**Source**: coding_policy

**Description**:
NTPE targets Python 3.x. Specific minimum version requirements are not yet documented. Some advanced language features (3.10+ pattern matching, 3.11+ exception groups) may not be available depending on deployment environment.

**Impact**:
New code must avoid features not available in the target Python version until the minimum version is formally specified.

**Workaround**:
Use Python 3.9+ compatible syntax as a conservative baseline until minimum version is documented.

**Resolution Plan**:
Document minimum Python version requirement in `.ai/policies/coding_policy.md` as part of a future stage.

### KC-002: Windows Path Handling

**Date Identified**: 2026-07-21
**Status**: ACTIVE
**Source**: environment context

**Description**:
The primary development platform is Windows. Path handling must use `os.path` or `pathlib` with Windows-compatible separators. Hardcoded Unix-style paths will fail.

**Impact**:
All file path operations must be platform-aware. Shell commands may require different syntax.

**Workaround**:
Use `pathlib.Path` for all file operations. Avoid hardcoded path separators.

**Resolution Plan**:
Add Windows-specific validation to the validation workflow.

## Constraint Log

| ID | Title | Status | Identified |
|----|-------|--------|------------|
| KC-001 | Python Version Compatibility | ACTIVE | 2026-07-21 |
| KC-002 | Windows Path Handling | ACTIVE | 2026-07-21 |

## Update Rules
- Add entries when new constraints are discovered
- Mark as RESOLVED when no longer applicable (with resolution date)
- Mark as WORKAROUND when a viable workaround exists
- Do not delete entries—mark as RESOLVED instead

## Future Update Notes
- Add more constraints as they are discovered during development
- Consider linking to GitHub issues if migrated to issue tracker
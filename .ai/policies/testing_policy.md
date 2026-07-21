# Policy: testing_policy

## Title
Testing Policy — Validation and Quality Gate Standards

## Purpose
This policy defines the mandatory testing and validation procedures that all AI agents must follow when making code changes. It establishes the minimum quality bar for any modification to pass before being considered complete.

## Scope
- Applies to implement, testing, and release profiles
- Mandatory for any stage that produces or modifies code
- Referenced by `.clinerules` Validation Workflow

## Required Validation Tools

### 1. pytest
- **When**: After any code modification, before reporting completion
- **Command**: `pytest` (targeted) or `pytest` (full suite if scope is wide)
- **Requirement**: All previously-passing tests must still pass
- **New Tests**: Any new functionality must include corresponding test cases
- **Failure Handling**: New failures must be fixed or documented as known constraints

### 2. compileall
- **When**: After any Python file creation or modification
- **Command**: `python -m compileall -q {DIRECTORY}` or `python -m compileall -q .`
- **Requirement**: Zero syntax errors in all modified files
- **Scope**: Run on all modified directories, not just the changed files

### 3. git diff --check
- **When**: Before reporting completion of any file modification
- **Command**: `git diff --check`
- **Requirement**: Zero whitespace/line-ending violations
- **Purpose**: Ensures `.editorconfig` compliance and clean git history

### 4. git diff --stat
- **When**: After any file modification
- **Command**: `git diff --stat`
- **Requirement**: Scope matches intended changes; no unexpected files touched
- **Purpose**: Visual confirmation of modification scope

### 5. git status --short
- **When**: Before declaring completion
- **Command**: `git status --short`
- **Requirement**: Only intended files show as modified; no untracked artifacts
- **Purpose**: Final state verification

## Test Quality Standards
- Tests must be independent (no order dependency)
- Tests must be repeatable (no reliance on external state)
- Tests must not invoke real AI providers (use mocks)
- Test names must describe what is being tested
- Test files must follow naming convention: `*_test.py`

## Frozen Layer Testing
- Tests for frozen modules may be added or modified
- Tests must validate frozen module behavior without changing it
- If a test reveals a frozen layer bug, escalate to human review

## Future Update Notes
- May add coverage thresholds (e.g., 80% line coverage minimum)
- Consider adding performance regression benchmarks
- Could integrate linting tools (flake8, pylint) into mandatory validation
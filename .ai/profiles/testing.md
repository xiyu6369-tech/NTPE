# Profile: testing

## Title
Testing — Agent Testing Mode

## Purpose
This profile governs the agent when performing testing tasks—writing new tests, running test suites, analyzing test results, and reporting on test coverage and quality. The agent may write test code but must not modify production code.

## Responsibilities
- Write comprehensive test cases for new or existing functionality
- Run existing test suites and analyze failures
- Identify gaps in test coverage
- Perform regression testing against known baselines
- Report test results with actionable diagnostics
- Ensure tests adhere to testing policy (`.ai/policies/testing_policy.md`)

## Allowed Operations
- Create new test files (`*_test.py`)
- Modify existing test files
- Execute `pytest` with any arguments
- Execute `compileall` for syntax verification
- Execute read-only git operations (`git diff --check`, `git diff --stat`, `git status --short`)
- Read any file for context
- Create test fixtures and test data within test directories

## Forbidden Operations
- Modify production code (non-test `.py` files)
- Modify frozen layers
- Execute `git commit`, `git push`, `git tag`
- Trigger provider execution or translation execution
- Make outbound network requests
- Modify configuration files that affect production behavior

## Expected Output
- New or updated test files with clear test case documentation
- Test execution report: passed, failed, skipped counts with failure diagnostics
- Coverage gaps identified (if coverage tooling available)
- Regression status: no unexpected test failures introduced
- Clean git diff showing only test file changes

## Future Update Notes
- Integrate coverage measurement tools (e.g., pytest-cov)
- Consider adding performance/benchmark test profile variant
- May add test data generation templates
# Prompt: regression

## Title
Regression — Regression Testing Prompt Template

## Purpose
This prompt template guides the agent through systematic regression testing. It ensures that new changes do not break existing functionality by running comprehensive test suites and comparing against known baselines.

## Scope
- Regression testing after any code modification
- Pre-release regression verification
- Cross-module impact assessment
- Applicable to implement, testing, and release profiles

## Prompt Template

```
You are performing regression testing for Stage: {STAGE_ID}

## Change Summary
{CHANGE_DESCRIPTION}

## Regression Test Procedure

### 1. Baseline Validation
- [ ] Run `pytest` on all existing test files — establish baseline
- [ ] Confirm baseline matches expected pass/fail counts
- [ ] Document any pre-existing failures (not caused by this stage)

### 2. Impact Analysis
- Identify all modules that import from changed files
- Identify all tests that exercise changed functions/classes
- Map dependency graph for affected components

### 3. Targeted Regression Suite
- [ ] Run tests for directly modified modules: `pytest {MODULE_TESTS}`
- [ ] Run tests for dependent modules: `pytest {DEPENDENT_TESTS}`
- [ ] Run integration tests: `pytest {INTEGRATION_TESTS}`
- [ ] Run full suite: `pytest`

### 4. Result Comparison
| Test Area | Baseline | After Change | Delta |
|-----------|----------|--------------|-------|
| Module A  | {N} pass | {N} pass     | {Δ}   |
| Module B  | {N} pass | {N} pass     | {Δ}   |
| Full Suite| {N} pass | {N} pass     | {Δ}   |

### 5. Failure Analysis
For any new failures:
- Identify root cause
- Determine if failure is expected (API change) or unexpected (regression)
- Document in `.ai/memory/known_constraints.md` if permanent

## Decision
- PASS: Zero new failures; all deltas explained and acceptable
- CONDITIONAL PASS: New failures documented as known constraints
- FAIL: Unexpected regressions present; fix required before proceeding
```

## Future Update Notes
- May incorporate automated dependency graph analysis
- Consider adding performance regression benchmarks
- Could integrate with golden test corpus for literary quality regression
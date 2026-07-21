# Prompt: canary

## Title
Canary — Canary Deployment / Early Validation Prompt Template

## Purpose
This prompt template guides the agent through canary-style early validation of a change before full integration. It ensures that risky or experimental changes are tested in isolation on a small, controlled subset before broader rollout.

## Scope
- Experimental features and architectural changes
- Provider configuration changes
- Performance-sensitive modifications
- Any change flagged as high-risk by the architecture profile
- Applicable to implement and testing profiles

## Prompt Template

```
You are performing canary validation for Stage: {STAGE_ID}

## Change Under Test
{CHANGE_DESCRIPTION}

## Risk Assessment
- Risk Level: LOW / MEDIUM / HIGH
- Affected Modules: {MODULES}
- Potential Impact: {IMPACT_DESCRIPTION}

## Canary Procedure

### 1. Isolation
- [ ] Identify minimal test scope for the change
- [ ] Select representative test cases (not full suite)
- [ ] Define canary pass/fail threshold

### 2. Controlled Execution
- [ ] Run canary test subset: `pytest {CANARY_TESTS}`
- [ ] Monitor for unexpected side effects
- [ ] Compare output against pre-change baseline

### 3. Canary Results
| Metric | Baseline | Canary | Status |
|--------|----------|--------|--------|
| Tests Passed | {N} | {N} | ✓/✗ |
| Execution Time | {T} | {T} | ✓/✗ |
| Output Consistency | - | - | ✓/✗ |

### 4. Decision Gates
- GATE 1: All canary tests pass → proceed to Gate 2
- GATE 2: No unexpected side effects detected → proceed to Gate 3
- GATE 3: Performance within acceptable threshold → FULL ROLLOUT APPROVED

## Post-Canary Actions
- If PASSED: proceed with full implementation
- If FAILED: document failure in `.ai/memory/known_constraints.md`, revert or redesign
- If CONDITIONAL: document constraints, proceed with guardrails

## Rollback Plan
{ROLLBACK_PROCEDURE}
```

## Future Update Notes
- May incorporate automated canary traffic splitting for provider changes
- Consider adding statistical significance thresholds for canary results
- Could integrate with feature flag system for runtime canary toggles
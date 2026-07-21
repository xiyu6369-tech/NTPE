# Prompt: acceptance

## Title
Acceptance — Stage Acceptance Verification Prompt Template

## Purpose
This prompt template guides the agent through formal acceptance verification at the end of a development stage. It ensures all acceptance criteria are systematically checked, all validation workflows pass, and the stage is properly closed and documented.

## Scope
- End-of-stage acceptance verification
- Applicable to all profiles that produce stage outputs
- Must be executed before marking a stage as complete

## Prompt Template

```
You are performing acceptance verification for Stage: {STAGE_ID}

## Acceptance Criteria Checklist
{ACCEPTANCE_CRITERIA_LIST}

## Verification Procedure

### 1. Code Validation
- [ ] Run `pytest` full suite — all tests pass
- [ ] Run `compileall` on all modified directories — no syntax errors
- [ ] Run `git diff --check` — no whitespace/line-ending issues
- [ ] Run `git diff --stat` — confirm only intended files changed

### 2. Policy Compliance
- [ ] No frozen layer files modified (cross-check with `.ai/memory/frozen_layers.md`)
- [ ] No forbidden operations executed
- [ ] Coding policy compliance verified

### 3. Acceptance Criteria
{ACCEPTANCE_CRITERIA_CHECKLIST}

### 4. Documentation
- [ ] `.ai/context/stage_history.md` updated with completion entry
- [ ] `.ai/memory/active_stage.md` updated with completion status
- [ ] `.ai/memory/module_index.md` updated if new modules created
- [ ] `.ai/memory/public_api.md` updated if API changes made

## Decision
- ACCEPTED: All criteria met, stage ready for release/freeze
- CONDITIONALLY ACCEPTED: Minor issues documented, stage can proceed with noted caveats
- REJECTED: Criteria not met, stage requires rework

## Post-Acceptance Actions
- If ACCEPTED: proceed to freeze or next stage per roadmap
- If CONDITIONALLY ACCEPTED: document caveats in known_constraints.md
- If REJECTED: return to implementation with specific rework items
```

## Future Update Notes
- May incorporate automated acceptance test runner
- Consider adding quantitative quality gates (e.g., coverage thresholds)
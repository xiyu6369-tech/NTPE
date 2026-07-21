# Prompt: stage_start

## Title
Stage Start — Stage Initialization Prompt Template

## Purpose
This prompt template guides the agent at the beginning of a new development stage. It ensures the agent loads the correct context, verifies prerequisites, understands the scope, and initializes tracking before any implementation begins.

## Scope
- Stage initialization for all NTPE development stages
- Applicable to implement, architecture, and testing profiles at stage start
- Not applicable to review or audit profiles

## Prompt Template

```
You are starting Stage: {STAGE_ID}

## Pre-Flight Checklist
1. Read `.ai/memory/active_stage.md` — confirm previous stage is complete
2. Read `.ai/memory/frozen_layers.md` — identify untouchable modules
3. Read `.ai/memory/known_constraints.md` — review current limitations
4. Read `.ai/context/architecture.md` — understand system structure
5. Read `.ai/context/module_map.md` — identify relevant modules
6. Read `.ai/policies/project_boundaries.md` — confirm modification scope
7. Read `.ai/policies/coding_policy.md` — refresh coding standards
8. Run `git status --short` — confirm clean starting state

## Stage Scope
{STAGE_DESCRIPTION}

## Acceptance Criteria
{ACCEPTANCE_CRITERIA}

## Allowed Modifications
{ALLOWED_MODIFICATIONS}

## Forbidden Modifications
{FORBIDDEN_MODIFICATIONS}

## Initialization Actions
- Update `.ai/memory/active_stage.md` with this stage ID and start time
- Create stage tracking entry in `.ai/context/stage_history.md`
- Confirm all pre-flight items pass before proceeding to implementation
```

## Future Update Notes
- May be extended with stage-specific pre-flight items
- Consider adding dependency validation for multi-stage sequences
- Could incorporate automatic prerequisite test execution
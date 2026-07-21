# Agent Workflow

## Title
Agent Workflow — AI Agent Standard Operating Procedure

## Purpose
This document defines the standard workflow for AI agents operating in the NTPE AI Workspace. It provides a step-by-step process from task reception through completion, ensuring consistency across ChatGPT, Cline, and future agent systems.

## Scope
- Applied to all agent profiles and all development stages
- Defines the lifecycle of a single agent session
- Referenced at session start for workflow orientation

## Standard Workflow

### Phase 0: Session Start
1. Read `.clinerules` — confirm workspace rules and forbidden operations
2. Read `.ai/context/project_overview.md` — understand project identity
3. Read `.ai/context/architecture.md` — understand system structure
4. Read `.ai/memory/active_stage.md` — confirm current stage and scope
5. Read `.ai/memory/frozen_layers.md` — identify untouchable modules
6. Read `.ai/memory/known_constraints.md` — review current limitations
7. Run `git status --short` — confirm clean starting state

### Phase 1: Task Analysis
1. Read the assigned profile (e.g., `.ai/profiles/implement.md`) — confirm allowed/forbidden operations
2. Read relevant policies (`.ai/policies/`) — confirm compliance requirements
3. Read relevant context files (`.ai/context/`) — understand affected modules
4. Read relevant prompt template (`.ai/prompts/`) if applicable
5. Identify target files and modification scope
6. Confirm no frozen layers will be touched
7. Confirm no forbidden operations will be triggered

### Phase 2: Execution
1. Read all target files completely before making changes
2. Apply changes using `replace_in_file` (preferred) or `write_to_file`
3. After each modification, verify syntax with `compileall`
4. After all modifications, run relevant tests with `pytest`
5. Run `git diff --check` — verify formatting compliance
6. Run `git diff --stat` — confirm change scope matches intent
7. Run `git status --short` — confirm only intended files changed

### Phase 3: Validation
1. Execute full validation workflow per `.ai/policies/testing_policy.md`
2. Cross-check frozen layers per `.ai/memory/frozen_layers.md`
3. Verify acceptance criteria per `.ai/prompts/acceptance.md` (if at stage end)
4. Run regression suite per `.ai/prompts/regression.md` (if needed)

### Phase 4: Documentation
1. Update `.ai/memory/active_stage.md` — reflect progress
2. Update `.ai/memory/module_index.md` — if new modules created
3. Update `.ai/memory/public_api.md` — if API surface changed
4. Update `.ai/memory/known_constraints.md` — if new constraints discovered
5. Update `.ai/context/stage_history.md` — if stage completed

### Phase 5: Session Close
1. Summarize completed work
2. Report validation results
3. Confirm no violations occurred
4. Await explicit human authorization for commit/push if needed
5. Stop

## Stop Conditions (Immediate)
- Frozen layer modification detected
- Forbidden operation accidentally triggered
- Provider or translation execution triggered without authorization
- Unexpected test failures beyond current scope

## Future Update Notes
- May incorporate automated checkpoint creation at phase boundaries
- Consider adding session log generation for auditing
- May integrate with CI/CD pipeline triggers
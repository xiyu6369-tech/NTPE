# Prompt: release

## Title
Release — Stage Release / Freeze Prompt Template

## Purpose
This prompt template guides the agent through the formal release or freeze process for a completed stage. It ensures all validation, documentation, and versioning steps are executed before declaring a stage released or frozen.

## Scope
- Stage release and freeze ceremonies
- Version manifest creation
- Release note generation
- Applicable to release profile primarily; also used by implement profile at stage completion

## Prompt Template

```
You are performing release/freeze for Stage: {STAGE_ID}

## Pre-Release Checklist

### 1. Acceptance Confirmation
- [ ] All acceptance criteria met (per acceptance prompt)
- [ ] Regression testing passed (per regression prompt)
- [ ] Canary validation passed (if applicable)

### 2. Code Freeze Validation
- [ ] `pytest` full suite — 100% pass (or documented exceptions)
- [ ] `compileall` — zero syntax errors
- [ ] `git diff --check` — clean
- [ ] `git diff --stat` — only intended files
- [ ] Frozen layers intact (cross-check `.ai/memory/frozen_layers.md`)

### 3. Documentation Updates
- [ ] Update `docs/CHANGELOG.md` with stage changes
- [ ] Create/update release notes in `docs/releases/`
- [ ] Update `.ai/context/stage_history.md` with release entry
- [ ] Update `.ai/memory/active_stage.md` to mark stage complete
- [ ] Update `.ai/memory/frozen_layers.md` if new layers are frozen
- [ ] Update `.ai/memory/module_index.md` if module set changed
- [ ] Update `.ai/memory/public_api.md` if API surface changed

### 4. Version Manifest
Create manifest entry:
```
Stage: {STAGE_ID}
Version: {VERSION}
Date: {DATE}
Status: RELEASED / FROZEN
Artifacts: {ARTIFACT_LIST}
Frozen Layers Added: {NEW_FROZEN_LAYERS}
```

### 5. Final Git State
- [ ] `git status --short` — review final state
- [ ] All changes staged and documented (commit pending human authorization)

## Release Decision
- RELEASED: All checks passed, stage delivered
- FROZEN: All checks passed, stage locked against further modification
- DEFERRED: Issues documented, release postponed

## Post-Release
- Human authorization required for: `git commit`, `git tag`, `git push`
- Agent must NOT execute these without explicit per-operation authorization
```

## Future Update Notes
- May incorporate semantic versioning automation
- Consider adding changelog generation from git history
- Could integrate with artifact packaging step
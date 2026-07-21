# Acceptance Checklist

## Title
Acceptance Checklist — Stage Completion Verification Checklist

## Purpose
This document provides a standardized checklist for verifying that a development stage meets all acceptance criteria before being declared complete. It ensures consistent quality gates across all stages and all agents.

## Scope
- Applied at the end of each development stage
- Covers code quality, testing, documentation, and governance
- Referenced by `.ai/prompts/acceptance.md` and `.ai/profiles/release.md`

## Acceptance Checklist

### A. Code Quality
- [ ] All modified files pass `compileall` syntax validation
- [ ] No linter errors introduced (check `.editorconfig` compliance)
- [ ] No dead code or commented-out blocks left behind
- [ ] All new public functions/classes have docstrings
- [ ] Import statements are organized and minimal

### B. Testing
- [ ] All existing tests pass (`pytest` on relevant test suites)
- [ ] No existing test modified to accommodate new bugs
- [ ] New functionality covered by tests (if applicable)
- [ ] Regression suite passes (per `.ai/prompts/regression.md`)

### C. Documentation
- [ ] `.ai/memory/active_stage.md` updated to reflect completion
- [ ] `.ai/context/stage_history.md` updated with stage entry
- [ ] `.ai/memory/module_index.md` updated for new modules
- [ ] `.ai/memory/public_api.md` updated for new APIs
- [ ] `.ai/memory/frozen_layers.md` updated if layers frozen
- [ ] `.ai/memory/known_constraints.md` updated if new constraints found
- [ ] `.ai/memory/architecture_decisions.md` updated if decisions made

### D. Governance
- [ ] No frozen layer modified (verified against `.ai/memory/frozen_layers.md`)
- [ ] No forbidden operation triggered (commit, push, tag, unauthorized provider/translation)
- [ ] Policy compliance confirmed (`project_boundaries`, `git_policy`, `provider_policy`)
- [ ] Profile scope respected — no operations outside assigned profile

### E. Version Control
- [ ] `git diff --check` passes with zero whitespace violations
- [ ] `git diff --stat` matches expected change scope
- [ ] `git status --short` confirms only intended files changed
- [ ] No commit executed without explicit human authorization

### F. Stage-Specific Criteria
- [ ] All stage scope items completed (per `.ai/memory/active_stage.md`)
- [ ] No scope creep — only specified deliverables produced
- [ ] Stage output matches expected format and content

## Sign-Off
When all checklist items pass, the stage is ready for formal acceptance:
1. Mark stage as COMPLETED in `.ai/memory/active_stage.md`
2. Add entry to `.ai/context/stage_history.md`
3. If applicable, execute freeze ceremony per `.ai/profiles/release.md`
4. Report completion to human operator

## Rejection Conditions
- Any checkbox fails
- Human operator identifies quality issues
- Scope creep detected (extra deliverables beyond specification)
- Policy violation detected during audit

## Future Update Notes
- Consider adding automated checklist validation script
- May integrate with CI/CD pipeline for automated gate checks
- Score thresholds may be added for quantitative quality metrics
# Memory: architecture_decisions

## Title
NTPE Architecture Decision Log

## Purpose
This memory file records significant architecture decisions made during NTPE development. Each entry documents the context, decision, consequences, and date. AI agents reference this to understand why the codebase is structured as it is and to avoid revisiting closed decisions.

## Scope
- Architecture decisions that affect module boundaries, dependencies, and design patterns
- Decisions that result in frozen layers or policy changes
- Decisions with cross-module impact
- Does not record routine implementation decisions

## Decision Log

### Decision Template
When adding a new decision:

```
### ADR-{number}: {Title}

**Date**: {YYYY-MM-DD}
**Status**: {ACCEPTED / SUPERSEDED / DEPRECATED}
**Stage**: {stage_id}
**Author**: {profile / human}

**Context**:
{Why this decision was needed}

**Decision**:
{What was decided}

**Consequences**:
{What changed as a result}

**References**:
- Related files or policies
```

### ADR-001: AI Workspace Governance Structure

**Date**: 2026-07-21
**Status**: ACCEPTED
**Stage**: AW-1 Foundation
**Author**: implement

**Context**:
NTPE needs a structured workspace for multiple AI agents (ChatGPT, Cline, future agents) to collaborate without conflicts, ambiguous permissions, or undocumented constraints. Previous development lacked a governance framework.

**Decision**:
Establish `.ai/` workspace with profiles, prompts, policies, context, and memory directories. Each component has a specific role: profiles define agent behavior, prompts guide workflows, policies set rules, context provides project knowledge, memory tracks evolving state.

**Consequences**:
- All agents now have documented role definitions
- Modification permissions are explicitly governed
- Stage history provides traceability
- Frozen layers prevent accidental regression
- Decision log preserves rationale for future reference

**References**:
- `.ai/policies/project_boundaries.md`
- `.ai/memory/frozen_layers.md`

## Update Rules
- Add new entries when significant architecture decisions are made
- Mark entries as SUPERSEDED when replaced by newer decisions
- Do not delete or edit historical entries (add supersession note instead)

## Future Update Notes
- Consider numbering scheme (ADR-001, ADR-002, etc.)
- May link to design documents in `docs/`
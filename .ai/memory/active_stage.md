# Memory: active_stage

## Title
NTPE Active Stage — Current Development Stage

## Purpose
This memory file tracks the currently active development stage. It provides a single source of truth for what stage is in progress, what its scope is, and what stage preceded it. Updated at stage start and stage completion.

## Scope
- Tracks one active stage at a time
- Cleared only when stage completes and `.ai/context/stage_history.md` is updated
- Referenced at session start by stage start prompt

## Current Stage

| Field | Value |
|-------|-------|
| **Stage ID** | AW-1 Foundation |
| **Status** | IN PROGRESS |
| **Started** | 2026-07-21 |
| **Profile** | implement |
| **Description** | Establish NTPE AI Workspace v2.0 foundation — create `.ai/` governance structure, root configuration files, profiles, prompts, policies, context, memory, and documentation for multi-agent collaboration. |

## Stage Scope
- Create `.ai/` directory tree with profiles, prompts, policies, context, memory
- Create root configuration files (`.clinerules`, `.clineignore`, `.editorconfig`)
- Create `docs/ai_workspace/` documentation
- **No Python code modifications** — workspace infrastructure only

## Previous Stage
- **Stage ID**: (none — first stage)
- **Status**: N/A

## Next Stage
- **Stage ID**: (to be determined after AW-1 completion)

## Update Rules
- Set at stage start with stage ID and description
- Clear and mark complete at stage completion
- Update status field as stage progresses
- Do not modify scope after stage has started (scope changes require new stage)

## Future Update Notes
- Add completion date when stage finishes
- Reference the release manifest for completed stage details
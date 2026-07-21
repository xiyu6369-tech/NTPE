# .ai — NTPE AI Workspace v2.0

## Title
NTPE AI Workspace — Shared AI Agent Collaboration Environment

## Purpose
The `.ai/` directory serves as the canonical workspace for all AI agents (ChatGPT, Cline, and future agents) operating within the NTPE project. It provides a structured, policy-governed environment where agents can:
- Understand project context and architecture
- Follow consistent behavioral profiles
- Reference shared prompts, policies, and memory
- Maintain a persistent, updatable knowledge base

This workspace ensures that all AI agents operate with the same baseline understanding, reducing inconsistency and drift across sessions.

## Scope
- **Profiles** — Agent behavioral modes (implement, review, audit, architecture, testing, release)
- **Prompts** — Reusable stage-level prompt templates
- **Policies** — Governance rules for code, git, providers, testing, and project boundaries
- **Context** — Project overview, architecture, module map, glossary, and stage history
- **Memory** — Persistent indices: modules, public API, frozen layers, active stage, architecture decisions, known constraints

All content is NTPE-specific. No external, personal, or unrelated content is permitted.

## Directory Layout

```
.ai/
├── README.md                  ← This file
├── profiles/                  ← Agent behavioral profiles
│   ├── implement.md
│   ├── review.md
│   ├── readonly_audit.md
│   ├── architecture.md
│   ├── testing.md
│   └── release.md
├── prompts/                   ← Reusable stage prompt templates
│   ├── stage_start.md
│   ├── stage_fix.md
│   ├── acceptance.md
│   ├── regression.md
│   ├── canary.md
│   └── release.md
├── policies/                  ← Governance and constraint policies
│   ├── project_boundaries.md
│   ├── git_policy.md
│   ├── provider_policy.md
│   ├── testing_policy.md
│   └── coding_policy.md
├── context/                   ← Project knowledge (read-only reference)
│   ├── project_overview.md
│   ├── architecture.md
│   ├── module_map.md
│   ├── glossary.md
│   └── stage_history.md
└── memory/                    ← Persistent, updatable working memory
    ├── module_index.md
    ├── public_api.md
    ├── frozen_layers.md
    ├── active_stage.md
    ├── architecture_decisions.md
    └── known_constraints.md
```

## How Agents Should Use This Workspace

1. **On session start** — Read active profile from `.ai/profiles/` to determine behavioral mode
2. **Before any operation** — Consult `.ai/policies/` for governance rules
3. **For project understanding** — Reference `.ai/context/` files
4. **For persistent state** — Read and update `.ai/memory/` files as needed
5. **During stages** — Use prompt templates from `.ai/prompts/` as starting points
6. **On completion** — Update `.ai/memory/active_stage.md` and `.ai/context/stage_history.md`

## Update Strategy
- **Policies** — Updated deliberately; require team review
- **Context** — Updated when architecture, modules, or terminology changes
- **Memory** — Updated continuously as stages progress
- **Profiles** — Stable; updated only when new agent modes are needed
- **Prompts** — Evolve with stage patterns; updated per release cycle

## Future Update Notes
- This workspace is designed to be extended for new agent types without restructuring
- Memory files use templates that support incremental append-only updates
- All Markdown files maintain consistent section structure (Title, Purpose, Scope, Future Update Notes)
- New profiles, prompts, or policies can be added by creating new `.md` files in the respective directories
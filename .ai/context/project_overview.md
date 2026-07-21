# Context: project_overview

## Title
NTPE — Novel Translation Pipeline Engine

## Purpose
NTPE is a Python-based literary translation pipeline that orchestrates multi-provider AI models to produce high-quality novel translations. It combines AI translation, quality engineering, and enterprise deployment into a unified, policy-governed pipeline.

This context file provides a high-level overview for AI agents newly entering the workspace.

## Scope
- Covers project identity, goals, and high-level structure
- Referenced at session start for orientation
- Does not replace detailed architecture or module documentation

## Project Identity
- **Name**: NTPE (Novel Translation Pipeline Engine)
- **Language**: Python 3.x
- **Platform**: Windows 10 / cross-platform compatible
- **Repository**: https://github.com/xiyu6369-tech/NTPE.git
- **Version**: 2.0 (AI Workspace era)

## Core Capabilities
- **Multi-Provider AI Orchestration** — Route translation tasks across multiple AI providers
- **Literary Translation Quality Engine** — Semantic, stylistic, and structural quality assurance
- **Translation Intelligence** — Context-aware, character-aware, narrative-aware translation
- **Production Platform** — Workflow engine, job scheduling, resource optimization
- **Enterprise Deployment** — Configuration center, deployment profiles, monitoring
- **Plugin Marketplace** — Extensible architecture for custom translation plugins

## High-Level Architecture
NTPE is organized into layered functional domains:
1. **Core** — Fundamental utilities, data structures, shared contracts
2. **Engine** — Translation engine, quality engine, intelligence modules
3. **Provider** — AI provider abstraction, routing, observability
4. **Runtime** — Job scheduling, resource management, resume/recovery
5. **Launcher** — Entry points, pipeline orchestration, CLI
6. **Enterprise** — Deployment, configuration, monitoring, documentation

See `.ai/context/architecture.md` for detailed architecture.
See `.ai/context/module_map.md` for module responsibilities.

## Current State
- Multiple stages have been completed, tested, and frozen
- Active development continues under AI Workspace governance
- See `.ai/memory/active_stage.md` for current stage
- See `.ai/context/stage_history.md` for completed stages

## Future Update Notes
- Update when major architectural shifts occur
- Keep in sync with `.ai/context/architecture.md`
- Version tag should reflect current release status
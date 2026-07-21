# AI Workspace Overview

## Title
NTPE AI Workspace v2.0 — Overview

## Purpose
This document provides a comprehensive overview of the NTPE AI Workspace, the structured environment designed to enable multiple AI agents (ChatGPT, Cline, and future agent systems) to collaborate effectively on the Novel Translation Pipeline Engine project.

## Scope
- This overview covers the entire workspace structure and purpose.
- It is the entry point for any AI agent being introduced to the project.
- It references but does not replace detailed documents in .ai/ and docs/ai_workspace/.

## What is the AI Workspace?
The AI Workspace is a set of directories, files, and conventions that:

- Provide a shared context between human developers and AI agents
- Define clear roles (profiles) for different types of tasks
- Establish policies that govern what AI agents can and cannot do
- Track the history and status of all development stages
- Record decisions and constraints for future reference

## Directory Structure

### Root Files
| File | Purpose |
|------|---------|
| `.clinerules` | Defines base rules for the Cline agent operating in this workspace |
| `.clineignore` | Lists files and directories the agent should never read or modify |
| `.editorconfig` | Defines coding style and formatting conventions for all files |

### .ai/ Directory
| Subdirectory | Purpose |
|-------------|---------|
| `.ai/profiles/` | Defines roles for the AI agent (implement, review, etc.) |
| `.ai/prompts/` | Templates for common tasks and workflows |
| `.ai/policies/` | Rules and constraints governing behavior |
| `.ai/context/` | Background information about the project |
| `.ai/memory/` | Dynamic state tracking during development |

### docs/ai_workspace/ Directory
| File | Purpose |
|------|---------|
| AI_WORKSPACE_OVERVIEW.md | This document |
| AGENT_WORKFLOW.md | How the agent should process tasks |
| MODEL_SELECTION.md | Guidelines for selecting AI models |
| ACCEPTANCE_CHECKLIST.md | Checklist for evaluating work quality |

## Key Principles

1. **Clarity**: All rules, roles, and constraints are documented explicitly.
2. **Consistency**: All agents are expected to follow the same processes.
3. **Transparency**: All decisions and changes are tracked and auditable.
4. **Safety**: Critical operations (commit, push, provider calls) require explicit human authorization.
5. **Evolution**: The workspace itself can be updated as the project grows.

## How to Use This Workspace

1. **Start Here**: Read this overview to understand the workspace structure.
2. **Read the Profile**: Locate the appropriate .ai/profile/ file for your task.
3. **Consult the Policies**: Review relevant .ai/policies/ for constraints.
4. **Check the Context**: Use .ai/context/ for background information.
5. **Update the Memory**: Modify .ai/memory/ files to track progress.
6. **Follow the Workflow**: Refer to AGENT_WORKFLOW.md for step-by-step guidance.

## Update Notes
- This file should be updated if the workspace structure changes significantly.
- Last updated: 2026-07-21.
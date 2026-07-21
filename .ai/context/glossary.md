# Context: glossary

## Title
NTPE Fixed Terminology Glossary

## Purpose
This glossary defines the fixed terminology used throughout the NTPE project. AI agents must use these terms consistently in code, documentation, and communication to avoid ambiguity.

## Scope
- Standardized terms for translation pipeline concepts
- NTPE-specific acronyms and abbreviations
- Terms that must not be paraphrased or substituted

## Core Terms

| Term | Definition |
|------|------------|
| **NTPE** | Novel Translation Pipeline Engine — the project name and acronym |
| **Chunk** | A segment of source text processed as a single translation unit |
| **Provider** | An external AI service (e.g., OpenAI, Anthropic, DeepSeek) that performs inference |
| **Pipeline** | The end-to-end translation workflow from input to output |
| **Stage** | A defined development phase with specific scope and acceptance criteria |
| **Freeze** | Locking a module/layer against further modification after validation |
| **Frozen Layer** | A module or set of modules declared immutable per release ceremony |
| **Launcher** | An entry-point script that initiates a pipeline run |
| **Quality Engine** | The subsystem that evaluates and ensures translation quality |
| **Intelligence Module** | A subsystem providing context, narrative, or character awareness |
| **Semantic Verification** | Quality check ensuring translated meaning matches source |
| **Regression** | A test verifying that new changes do not break existing functionality |
| **Acceptance** | Formal verification that a stage meets all criteria |

## Profile Terms

| Term | Definition |
|------|------------|
| **Implement** | Profile for active code development |
| **Review** | Profile for code review with modification permission |
| **Readonly Audit** | Profile for read-only inspection and analysis |
| **Architecture** | Profile for architecture design and decision-making |
| **Testing** | Profile for test creation and validation |
| **Release** | Profile for release/freeze ceremonies |

## Prompt Terms

| Term | Definition |
|------|------------|
| **Stage Start** | Prompt for initializing a new development stage |
| **Stage Fix** | Prompt for bug fixes and hotfixes |
| **Acceptance** | Prompt for stage acceptance verification |
| **Regression** | Prompt for regression testing |
| **Canary** | Prompt for canary/early validation |
| **Release** | Prompt for release/freeze ceremonies |

## Policy Terms

| Term | Definition |
|------|------------|
| **Project Boundaries** | Policy defining frozen layers and modification scope |
| **Git Policy** | Policy governing version control operations |
| **Provider Policy** | Policy governing AI provider and translation execution |
| **Testing Policy** | Policy defining validation and quality gate standards |
| **Coding Policy** | Policy defining Python style and API standards |

## Future Update Notes
- Add new terms as the project vocabulary expands
- Keep in sync with code documentation
- Do not redefine existing terms; add only new ones
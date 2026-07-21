# Model Selection

## Title
Model Selection — AI Model Selection Guidelines for NTPE

## Purpose
This document provides guidelines for selecting the appropriate AI model for a given task within the NTPE project. It helps agents and humans choose between available models based on task complexity, cost sensitivity, and required capabilities.

## Scope
- Applies to provider invocation decisions (when authorized)
- Covers model selection criteria for translation, quality evaluation, and development tasks
- Does not prescribe specific provider configurations (see `.ai/policies/provider_policy.md`)

## Model Selection Criteria

### Translation Tasks
| Criterion | Recommended Model Tier | Rationale |
|-----------|----------------------|-----------|
| Standard prose translation | Mid-tier / High-tier | Literary quality requires strong language understanding |
| Poetry / stylized content | High-tier only | Nuanced style reproduction needs top-tier models |
| Terminology-heavy technical passages | Mid-tier + glossary injection | Terminology accuracy matters more than creativity |
| Dialogue translation | Mid-tier | Conversational tone is well-handled by mid-tier |
| Batch production translation | Mid-tier (cost-optimized) | Volume requires cost-performance balance |

### Quality Evaluation Tasks
| Criterion | Recommended Model Tier | Rationale |
|-----------|----------------------|-----------|
| Semantic accuracy check | Mid-tier | Factual comparison, lower creative demand |
| Literary style evaluation | High-tier | Requires nuanced literary judgment |
| Repetition detection | Low-tier / algorithmic | Pattern matching, not creative |
| Structure integrity check | Low-tier / algorithmic | Format validation, deterministic |

### Development Tasks
| Criterion | Recommended Model Tier | Rationale |
|-----------|----------------------|-----------|
| Code generation (Python) | Mid-tier / High-tier | Depends on complexity |
| Test generation | Mid-tier | Pattern-based, moderate complexity |
| Documentation writing | Low-tier / Mid-tier | Structured output, lower creative demand |
| Architecture design review | High-tier | Requires broad system understanding |

## Tier Definitions
| Tier | Description | Use Case |
|------|-------------|----------|
| **High-tier** | Top-performing models with strongest reasoning and creativity | Literary evaluation, architecture design, stylized translation |
| **Mid-tier** | Balanced performance and cost | Standard translation, code generation, quality checks |
| **Low-tier / Algorithmic** | Lightweight, deterministic, or rule-based | Format validation, pattern matching, documentation drafting |

## Cost-Aware Selection
- Prefer mid-tier for bulk operations (batch translation, regression testing)
- Reserve high-tier for quality-critical single-pass evaluations
- Use algorithmic/low-tier for deterministic validations that do not require AI inference
- Never invoke a provider without confirming the model tier is appropriate for the task

## Authorization Requirement
All provider invocations require explicit human authorization per `.ai/policies/provider_policy.md`, regardless of model tier selected. This document guides the *selection* only — it does not grant execution permission.

## Future Update Notes
- Update as new models become available and tier boundaries shift
- May incorporate quantitative benchmark results from `.ai/memory/`
- Consider adding provider-specific model mapping tables
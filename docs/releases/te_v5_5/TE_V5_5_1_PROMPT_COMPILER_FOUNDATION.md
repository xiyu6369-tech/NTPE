# TE v5.5.1 Prompt Compiler Foundation

## Scope

Introduces a structured Prompt Compiler boundary while preserving the exact provider-facing literary prompt text produced by the existing builder.

## Behavior

- No Prompt Discipline rule is injected into live translation prompts in this stage.
- No Provider, Runtime retry, timeout, 40 RPM, Quality Gate, or resume behavior changes.
- `LiteraryPromptBuilder` delegates deterministic section assembly to `PromptCompiler`.
- Prompt metadata gains an additive `prompt_compiler` record.
- Synthetic offline fixtures establish the regression corpus for future Prompt Discipline stages.

## Compatibility

Existing `system_prompt`, `user_prompt`, prompt profile, prompt mode, glossary, narrative, and character context remain compatible. The new metadata is additive.

# TE v6.0 Stage 01 — Discipline Architecture Foundation

## Scope

This stage adds a unified, read-only discipline architecture over the existing v5.5.3.3 prompt and quality components. It does not change provider prompt text, token settings, quality scoring, retry policy, or provider execution.

## Architecture

- `DisciplineRule` defines the common rule schema and validates phase/category values.
- `DisciplineRuleRegistry` registers the eight existing Prompt Discipline rules with unique codes.
- `TranslationDisciplineEngine` selects the `literary_balanced` profile and emits additive metadata/reports.
- `PromptCompilerAdapter` delegates to the existing compiler without rewriting output.
- `AdaptiveFeedbackAdapter` maps existing issue codes to registered rules.
- `UnifiedQualityGateAdapter` annotates copied reports without changing score or decision.

## Compatibility

Old imports and runtime paths remain authoritative. Existing metadata (`prompt_compiler`, `prompt_discipline_enabled`, `discipline_rule_count`, `runtime_wiring_verified`) is retained, while v6 metadata is added. `NTPE_PROMPT_DISCIPLINE=0` and `NTPE_ADAPTIVE_PROMPT_FEEDBACK=0` remain supported.

## Safety boundary

No Provider Client or HTTP path was added. No NVIDIA API is called by this stage or its tests. Stage 02 is explicitly out of scope.

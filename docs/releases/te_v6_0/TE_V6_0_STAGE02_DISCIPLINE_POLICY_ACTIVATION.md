# TE v6.0 Stage 02 — Discipline Policy Activation

Stage 02 activates the Stage 01 Translation Discipline Engine as the canonical policy source for generation prompt rendering and adaptive issue-to-rule metadata.

## Guarantees

- Provider-ready discipline text remains byte-for-byte equivalent to TE v5.5.2.1.
- Prompt token counts and translation behavior do not change solely because of policy activation.
- Existing Prompt Compiler and Runtime metadata remain available.
- New metadata identifies `6.0.0-stage02` as the discipline policy version and `core.translation_discipline` as the policy source.
- Adaptive feedback records mapped discipline rule codes without changing existing directives, retry decisions, or Provider calls.
- `NTPE_PROMPT_DISCIPLINE=0` remains a complete rollback switch.

No NVIDIA API request is made by Stage 02 tests.

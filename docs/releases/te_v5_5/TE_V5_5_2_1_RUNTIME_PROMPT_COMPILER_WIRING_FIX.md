# TE v5.5.2.1 Runtime Prompt Compiler Wiring Fix

## Purpose

Guarantee that regression and TXT runtime packages use the v5.5.2 Prompt Compiler discipline block in the provider-ready prompt.

## Changes

- Adds a final runtime wiring guard in `build_prompt_package()`.
- Ensures `【翻譯紀律】` is present before `【Korean】` when discipline is enabled.
- Records compiler version, enabled state, rule count, and verification metadata.
- Includes discipline tokens in the runtime prompt profile.
- Preserves `NTPE_PROMPT_DISCIPLINE=0` rollback behavior.

## Compatibility

No Provider, timeout, retry, 40 RPM, resume, Quality Gate, or output behavior is removed.

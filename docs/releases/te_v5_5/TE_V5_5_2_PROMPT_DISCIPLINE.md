# TE v5.5.2 Prompt Discipline

TE v5.5.2 activates a compact literary generation-discipline block through the Prompt Compiler.

## Active constraints

- no added plot, setting, transitions, psychology, or summaries;
- no restatement of previous or already translated content;
- preserve information order and paragraph intent;
- previous context is reference-only and must not appear in output.

## Compatibility

Set `NTPE_PROMPT_DISCIPLINE=0` to restore the v5.5.1 discipline-free prompt assembly. Provider, Runtime, Quality Gate, retry, resume, timeout, and 40 RPM behavior are unchanged.

# TE v5.5.3.3 Segment-Level Completeness Recovery

When the unified quality gate reports a blocking completeness issue, the second QA attempt no longer retranslates the entire source chunk as one request. The runtime splits the source conservatively on paragraph and sentence boundaries, translates each smaller segment in source order, combines the results, and runs the existing quality gate again.

Safety constraints:

- No source text is discarded.
- Recovery never guesses which sentence is missing.
- Recovery does not delete or rewrite the previous translation.
- Each recovery segment uses the existing Prompt Discipline, glossary, Provider rate limiter, timeout, and quality pipeline.
- Segment requests default to one Provider attempt each to prevent retry multiplication.
- If any recovery segment fails, the existing best-attempt fallback preserves the earlier candidate and the chunk remains failed.

Environment controls:

- `NTPE_SEGMENT_COMPLETENESS_RECOVERY=0` disables this feature.
- `NTPE_SEGMENT_RECOVERY_CHARS=280` controls approximate segment size (180-420).
- `NTPE_SEGMENT_RECOVERY_PROVIDER_ATTEMPTS=1` controls attempts per recovery segment (1-2).

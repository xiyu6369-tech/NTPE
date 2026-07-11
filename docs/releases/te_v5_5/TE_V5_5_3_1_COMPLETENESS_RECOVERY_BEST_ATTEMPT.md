# TE v5.5.3.1 Completeness Recovery Feedback & Best Attempt Selection

## Scope

- Adds completeness metrics to adaptive retry prompts.
- Requires retries to restore omitted information without restating covered content.
- Ranks QA attempts by unified decision, score, blocking issue count and issue count.
- Prevents a worse retry from replacing a better earlier result.
- Saves the best failed candidate for inspection when all QA attempts remain blocking.

## Compatibility

Provider configuration, 40 RPM throttling, timeout, backpressure, resume, Smart Local Repair and Unified Quality Gate behavior remain unchanged.

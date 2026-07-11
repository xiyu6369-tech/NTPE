# TE v5.5.3.2 Adaptive Retry Failure Fallback

## Purpose

Preserve the best completed QA attempt when a later adaptive repair request fails before producing a translation because of timeout, capacity exhaustion, rate limiting, or another provider error.

## Behavior

- A successful QA attempt is registered immediately as a candidate.
- A later provider failure does not erase or replace that candidate.
- Runtime records `selection_reason=later_provider_error` and classifies the provider error.
- Runtime emits `best-attempt-fallback` progress output.
- If the selected candidate still has blocking quality issues, regression remains failed.
- The selected candidate is saved as `*_best_failed_zh.txt` for inspection.
- Resume continues to retry the failed chunk on the next run.

## Compatibility

No changes are made to provider retry counts, timeout propagation, 40 RPM throttling, quality thresholds, or resume success criteria.

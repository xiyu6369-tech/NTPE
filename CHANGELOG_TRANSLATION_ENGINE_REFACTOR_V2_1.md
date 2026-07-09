# TER-v2.1 Provider Degraded Fallback

- Treat NVIDIA `DEGRADED function cannot be invoked` responses as retryable provider-state failures.
- Add CLI `--fallback-models` for txt, batch, and regression commands.
- Add `NTPE_FALLBACK_MODELS` doctor visibility.
- Fast-fail degraded primary model when no fallback is configured instead of wasting long retry cycles.
- Use zero-delay fallback when a degraded-model error occurs and a fallback chain is configured.

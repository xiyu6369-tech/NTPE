# TE v5.2.2 Provider Timeout Resilience

Incremental, backward-compatible runtime update.

- Keeps explicit `--api-timeout` authoritative.
- Adds `--provider-attempts` to txt, batch, and regression commands.
- Uses configurable timeout retry waits from `NTPE_TIMEOUT_RETRY_DELAYS` (default `5,15,30`).
- Replaces the misleading timeout message that suggested the timeout already in use.
- Preserves fail-closed chunk behavior to prevent silently incomplete translations.

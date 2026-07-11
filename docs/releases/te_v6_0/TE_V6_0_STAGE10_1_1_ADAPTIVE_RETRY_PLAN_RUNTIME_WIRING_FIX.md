# TE v6.0 Stage 10.1.1 — Adaptive Retry Plan Runtime Wiring Fix

This patch makes the Stage 10 adaptive retry plan authoritative in the production TXT runtime.

- `targeted_retry` executes bounded targeted units.
- `full_retry` executes one full recovery request within the chunk recovery budget.
- legacy segment recovery is used only when no Stage 10 retry tier exists.
- tier, execution mode, fallback reason, and persistent provider budget are written to logs and package metadata.
- no quality thresholds, provider settings, RPM limits, or resume behavior are changed.

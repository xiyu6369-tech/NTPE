# TE v6.0 Stage 06 — Discipline Runtime Orchestrator

Stage 06 introduces one runtime coordination boundary for the existing discipline pipeline.

Flow:

1. Read the Unified Quality report.
2. Determine the initial Stage 05 action.
3. Run Stage 04 deterministic local repair only when routed locally.
4. Invoke the existing runtime quality callback after a text change.
5. Apply the Stage 05 final retry decision.
6. Record one orchestration metadata object.

The orchestrator adds no new quality rule and makes no Provider request. Prompt text, token profile, score, severity, timeout, retry, 40 RPM, resume, best-attempt and segment recovery contracts remain unchanged.

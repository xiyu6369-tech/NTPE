# TE v7.0 Stage 08.3 — Adaptive Context Strategy Selection

## Purpose

Stage 08.3 combines the Stage 08.1 production activation policy decision with the Stage 08.2 profile-aware context budget decision. It selects a single deterministic ACE strategy only when both evidence streams are ready and profile-consistent.

## Selected strategy

`safe_extractive_production_canary`

The strategy remains limited to the rollout percentage already authorized by Stage 08.1 and to the effective context budget produced by Stage 08.2.

## Fail-closed requirements

Selection requires explicit opt-in, an eligible profile (`literary` or `novel`), a ready `production_canary` policy decision, a ready profile budget decision, matching profiles, rollout from 1% through 5%, and an effective budget within both the profile cap and model hard limit.

Any missing or inconsistent evidence returns `strategy=disabled`.

## Boundary

Stage 08.3 does not install a runtime hook, modify prompts, modify Provider policy, change Quality v5, or activate rollout automatically. It only emits a redacted deterministic decision report.

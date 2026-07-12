# TE v7.0 Stage 08.1 — Production Activation Policy

Stage 08.1 introduces a deterministic, fail-closed policy gate for future ACE production activation. It does not activate ACE in the runtime and does not modify Provider, Prompt, Quality, Retry, LTS, or TE v6 frozen contracts.

## Eligibility

A decision is eligible only when all conditions hold:

- explicit opt-in is present;
- kill switch is disabled;
- profile is `literary` or `novel`;
- requested rollout is between 1% and 5%;
- Stage 07.5 A/B quality report is `pass` and `ready=true`;
- exactly one canary activation was observed;
- token saving is positive;
- no Provider call was added;
- target chunk completed;
- no fallback reason is present;
- canary status is eligible.

Any unknown or missing evidence returns `mode=disabled`.

## CLI

```cmd
python launcher_translate.py regression ^
--profile literary ^
--ace-production-policy-validate ^
--ace-production-policy-ab-report artifacts\te_v7_stage075\TE_V7_STAGE075_CANARY_AB_QUALITY_VALIDATION.json ^
--ace-production-policy-canary-report artifacts\te_v7_stage06\TE_V7_STAGE06_CANARY_PRODUCTION_VALIDATION.json ^
--ace-production-rollout-percent 5 ^
--ace-production-enable
```

The command performs evidence evaluation only and never calls Provider.

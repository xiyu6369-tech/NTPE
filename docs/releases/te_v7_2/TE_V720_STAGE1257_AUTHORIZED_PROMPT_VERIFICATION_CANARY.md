# TE v7.2 Stage 12.5.7 — Authorized Prompt Verification Canary

Stage 12.5.7 uses the immutable Stage 12.5.6A exact corpus resolver to map logical ID
`canary-001` to canonical ID `canary-001-character-honorific`. Git, artifact, readiness,
historical seal, authorization, corpus/hash, request-plan, and claim-eligibility checks all occur
before creation of the new single-use Stage 12.5.7 claim.

The authorized execution is limited to one baseline request followed by one candidate request to
NVIDIA `meta/llama-3.2-90b-vision-instruct`. Retry, fallback, parallel execution, automatic rerun,
alternate corpus, Provider, or model are prohibited. Stage 12.5.6 historical evidence is immutable.

Before ChatGPT manual review, activation is provisional and the gate remains
`translation_quality_integration_ready_for_controlled_canary`. Production, rollout, and formal
output replacement remain unauthorized.

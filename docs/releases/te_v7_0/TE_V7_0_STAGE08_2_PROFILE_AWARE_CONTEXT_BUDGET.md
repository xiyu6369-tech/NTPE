# TE v7.0 Stage 08.2 — Profile-aware Context Budget

Stage 08.2 adds a deterministic, profile-aware context budget decision layer. It does not activate ACE in production and does not modify Provider, Prompt policy, QA, Retry, LTS, or TE v6 frozen contracts.

## Profile caps

- fast: 64
- balanced: 96
- novel: 160
- literary: 192
- quality: 224
- premium: 256

The effective budget is the minimum of the profile cap, an optional requested budget, and the model hard limit after fixed prompt, source, and output reservations. Invalid profiles and zero capacity fail closed.

## Safety

- deterministic decisions
- content-redacted reports
- no Provider calls
- no runtime auto-hook
- no quality or latency improvement claim

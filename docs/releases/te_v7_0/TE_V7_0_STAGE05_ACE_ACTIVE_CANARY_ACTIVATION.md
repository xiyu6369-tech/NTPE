# TE v7.0 Stage 05 — ACE Active Canary Activation

Stage 05 adds an explicit `canary` mode. It may alter only one configured chunk and only the exact `previous_chunk_tail` occurrence in the provider prompt. The candidate is deterministic, extractive, sentence-complete, token-reducing, and fail-closed. Default mode remains `disabled`; no automatic expansion is permitted. Provider timeouts are external outcomes and are not classified as ACE failures. Audit and reports redact content.

Environment:
- `NTPE_TE_V7_ACE_MODE=canary`
- `NTPE_TE_V7_ACE_CANARY_CHUNK=2`
- `NTPE_TE_V7_ACE_CANARY_CONTEXT_TOKENS=128`
- optional `NTPE_TE_V7_ACE_CANARY_AUDIT=<jsonl path>`

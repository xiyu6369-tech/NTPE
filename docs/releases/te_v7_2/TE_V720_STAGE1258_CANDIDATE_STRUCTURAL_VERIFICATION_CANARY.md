# TE v7.2 Stage 12.5.8 — Candidate-Only Prompt Contract Structural Verification Canary

## Scope

Stage 12.5.8 prepares a candidate-only structural verification canary. It does not run a Baseline arm and does not claim that translation quality improved. The preparation is offline-only and adds zero Provider requests and zero network requests.

The formal Candidate request is not authorized by this preparation. Execution requires the framework to be committed and pushed, the worktree to be clean and synchronized with origin/main, and a separate ChatGPT confirmation.

## Frozen inputs

The preparation reuses the Stage 12.5.6A exact corpus resolver:

- logical ID: canary-001
- canonical ID: canary-001-character-honorific
- source SHA-256: 614a4ad6a8025a05ca165e6a7b35e8524ac3e0010649af081c47ab65a1bdf0f3
- fixture SHA-256: 53fe975f20561e65061488c82a47bc87838b911a5150df0324760bb11ed6bca5

No Prompt, Prompt Contract, Literary Prompt Builder, Provider layer, Runtime request path, frozen Baseline, or historical claim is modified.

## Formal execution contract

The future formal run is fixed to NVIDIA meta/llama-3.3-70b-instruct, Candidate arm only, one request, one attempt, no retry, no fallback, no cross-provider fallback, parallelism one, and no automatic rerun. Corpus resolution and request-plan construction occur before a new Stage 12.5.8 single-use claim is created.

Any failure in preflight steps 1–13 blocks before Provider execution with no claim and no request. After claim creation, the claim cannot be deleted, overwritten, or replayed, including after a timeout or local exception.

## Structural verification

The contract checks Provider outcome, source echo and Hangul residue, forbidden labels, Markdown/JSON/XML or explanatory wrappers, empty or abnormally short output, truncation, duplication and repeated blocks, malformed dialogue fragments, and a Traditional Chinese target signal. Provider raw response is evidence and is never repaired by the verifier.

The only result classes are:

- candidate_structural_verified
- candidate_structural_failed
- inconclusive_provider_timeout
- inconclusive_provider_error
- blocked_before_provider

This stage does not set candidate_improved, translation_quality_passed, production_ready, or rollout authorization.

## Activation boundary

A structural pass can advance only to translation_quality_prompt_contract_structurally_verified. A timeout, Provider error, or structural failure retains translation_quality_integration_ready_for_controlled_canary.

Production, automatic rollout, and formal output replacement remain unauthorized in every result.

## Preparation status

- Provider requests: 0
- Network requests: 0
- Formal claim created: no
- Formal Candidate response created: no
- Provider execution authorized: no
- Commit: HOLD
- Push: NO
- Tag: NO

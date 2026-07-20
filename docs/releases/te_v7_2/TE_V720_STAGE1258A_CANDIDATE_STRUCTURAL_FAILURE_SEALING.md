# TE v7.2 Stage 12.5.8A — Candidate Structural Failure Evidence Sealing

## Scope

Stage 12.5.8A is an offline evidence-sealing and root-cause-classification stage. It performs no Provider or network request, retry, fallback, Candidate rerun, claim replay, response repair, production activation, rollout, or formal-output replacement.

## Sealed execution result

Stage 12.5.8 completed one successful Candidate Provider request. The response was non-empty and did not time out, but structural verification failed because three Hangul characters remained inline in an otherwise Traditional Chinese response.

The final classification remains candidate_structural_failed. This is not a Provider error, timeout, source echo, incomplete output, quality-pass claim, or Candidate-improved claim. The activation gate remains translation_quality_integration_ready_for_controlled_canary.

## Failure classification

- Primary failure class: target_language_name_resolution_failure
- Structural failure class: mixed_language_inline_output
- Failure subtype: inline_hangul_name_residual
- Observed residuals: 영희 and 수

The residual names are separated from full or partial Korean source-passage echo. The response is retained byte-for-byte and is not repaired.

## Root cause

The immutable corpus contains the source names but no formal name mapping, and the rendered glossary is empty. Character Memory selected one qualified record mapping 영희 to Yeong-hui; that mapping was rendered in the Candidate prompt and was not dropped by budget, but the Provider still returned 영희.

No formal mapping for 민수 exists in the reviewed repository evidence. The response converted only part of that name to 民수. The evidence therefore supports multiple contributing causes:

- mapping_present_provider_ignored for 영희
- missing_name_mapping for 민수
- incomplete_name_normalization for 民수

No target representation for 민수 is invented by this stage.

## Frozen evidence

The Stage 12.5.8 claim remains consumed, single-use, and non-replayable. Its SHA-256 remains 81736fc37a12df55c3ce16ad8f09c3b7dd1c45f8a755b49a4c292f36c28acd8c. The Candidate response SHA-256 remains df46eddcc4360b0257a2347beeb0652a731c3752df3b8453ee33a53cbdc12873.

Commit is HOLD. Push and tag are NO. No new Provider Canary is authorized.

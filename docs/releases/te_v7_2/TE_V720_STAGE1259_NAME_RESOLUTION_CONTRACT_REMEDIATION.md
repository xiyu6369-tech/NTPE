# TE v7.2 Stage 12.5.9 — Offline Name Resolution Contract Remediation

## Scope

Stage 12.5.9 is a pure offline contract and candidate implementation. It performs no Provider or network request, creates no execution claim, and does not modify the Stage 12.5.8 claim, response, execution evidence, Frozen Baseline, Provider layer, or Runtime request path.

Runtime activation, production integration, automatic rollout, formal-output replacement, and the next Candidate Canary remain unauthorized.

## Identity and target-name separation

The immutable model separates source identity, identity transliteration, approved Traditional Chinese display name, resolution status, evidence provenance, prompt eligibility, and output-validation status.

Romanization is not an approved Traditional Chinese name. In particular, Yeong-hui is retained only as an identity transliteration and cannot be rendered as an approved zh-Hant target mapping.

For the current fixed evidence:

- 영희 is identity_only with identity transliteration Yeong-hui. It has no approved zh-Hant name and is not prompt eligible.
- 민수 has no authoritative target mapping or trusted identity transliteration. It remains unresolved and is not prompt eligible.

No Chinese name is inferred or invented for 민수.

## Eligibility and resolution

Only an approved, traceable, non-conflicting, non-expired, non-superseded zh-Hant name with valid target script may be rendered. Hangul, Latin-only transliteration, mixed-script targets, rejected mappings, and unresolved names fail closed.

Resolution priority is approved human-reviewed glossary, approved corpus, approved Character Memory target mapping, identity transliteration only, and unresolved. Conflicting approved target names are never selected by first-match, newest, longest, alphabetical, filesystem, or model-inference heuristics.

## Prompt candidate and budget

The candidate adapter is disabled by default and leaves the existing prompt and Provider payload unchanged. When explicitly enabled in offline tests, only approved target mappings render in a high-priority name-mapping block. Identity-only and unresolved entries consume no formal target-mapping budget.

Unresolved names use blocked_pending_policy. This stage does not choose romanization, Hangul preservation, partial translation, Chinese transliteration, or invention as a runtime fallback.

## Output validation

The validate-only extension distinguishes source echo, lexical Hangul residue, full proper-name residue, partial normalization, mixed Han/Hangul names, mixed Latin/Hangul names, inline mixed-script names, and approved-name mapping violations.

It never repairs output, deletes Hangul, rewrites a sentence, or calls a Provider.

## Activation boundary

The offline status may be name_resolution_contract_remediation_prepared. The formal activation gate remains translation_quality_integration_ready_for_controlled_canary.

Provider requests are zero. Production, rollout, formal replacement, and another Canary are not authorized.

Commit is HOLD. Push and tag are NO.

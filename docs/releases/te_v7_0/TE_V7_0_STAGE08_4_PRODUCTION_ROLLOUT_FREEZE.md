# TE v7.0 Stage 08.4 — ACE Production Rollout & Stage 08 Freeze

## Scope

Stage 08.4 connects the ready Stage 08.1 activation policy, Stage 08.2 profile budget, and Stage 08.3 strategy decision to a separate production-rollout integration layer. The layer is disabled by default and is not the TE v7 Final Release.

## Admission contract

Production ACE requires explicit `--ace-production-rollout`, a literary or novel profile, matching fresh and structurally safe Stage 08.1/08.2/08.3 reports, rollout from 1% through 5%, the selected `safe_extractive_production_canary` strategy, inherited A/B and single-canary evidence from the frozen Stage 08.1 evaluator, a closed kill switch, deterministic sampling, and a valid package-bound anchor. Missing, stale, malformed, unsafe, or inconsistent evidence fails closed.

The Stage 08.1 ready decision is the version-pinned attestation that the A/B gate passed and the canary produced exactly one activation, positive token saving, zero additional Provider calls, a complete target chunk, and no fallback. Stage 08.4 does not reinterpret or weaken those frozen conditions.

## Deterministic sampling

The sampling key is `source_hash + chunk_index + profile + rollout_policy_version`, delimited and hashed with SHA-256. The first 64 digest bits map into 10,000 stable buckets. A package is sampled only when `bucket < rollout_percent * 100`. Python `hash`, random state, wall-clock time, process identity, and plaintext persistence are not used. Zero percent and values above five percent never activate.

## Runtime boundary

The production hook wraps prompt-package assembly and runs once per chunk. Only the package-bound context anchor may change. System prompt fields, generation rules, Provider model, max tokens, timeout, attempts, retry, RPM, backpressure, QA, recovery, and Provider client behavior remain owned by the existing runtime. A failed admission or replacement restores the complete original package; partial merge is forbidden. The hook adds no Provider call.

The kill switch is read for every chunk. Once it is observed, rollback mode is latched to `disabled` for all following chunks in the session. Existing translations and output artifacts are never deleted or rewritten by rollback.

## Rollback contract

Automatic rollback is fail closed for new omission or unsupported-detail issues, quality-score or QA-failure regression, Provider-call growth, anchor mismatch, non-single replacement, missing metrics, evidence mismatch, kill switch, and production-artifact integrity failure. Provider timeout and HTTP 503 are reported as external limitations and do not by themselves become ACE functional failures.

## Metrics and privacy

The Stage 08.4 metrics schema contains package counts, admission block categories, context-token totals, estimated saving and reduction ratio, payload change counts, Provider-call invariant, QA outcomes, Provider timeout/503 counts, bucket, percentage, policy version, and strategy version. Records contain only hashes, counters, booleans, versions, and reason codes. Source text, translation text, prompt text, previous context, and API keys are forbidden.

## Validation harness

The production CLI supports assembly-only dry run, shadow-compatible execution, real Provider validation, resume seeding, target-chunk stop, inherited A/B admission, rollback simulation, and kill-switch simulation. It does not increase Provider attempts or change timeout. Real Provider timeout/503 must be reported separately and is never represented as a Stage functional pass.

## Frozen boundary

The Stage 08 freeze locks Activation Policy 08.1, Profile Budget 08.2, Strategy Selection 08.3, SHA-256 deterministic rollout, package-bound anchor, fail-closed admission, redacted metrics, rollback, next-chunk kill switch, maximum rollout 5%, zero additional Provider calls, and TE v6 backward compatibility. It does not authorize automatic expansion or Stage 09.

Historical TE v7 manifests no longer pin `ntpe_production_translate.py` by SHA-256 because it is a legal cross-Stage evolution entrypoint. Their inventories and Stage-local immutable files remain intact; this removes a brittle historical hash chain without deleting any historical Stage or test.

# TE v7.0 Stage 09 — ACE Production Performance & Quality Benchmark

## Status

- Version: `7.0.0-stage09`
- Baseline: ACE disabled
- Candidate: explicitly opted-in Stage 08.4/08.4.1 production rollout, capped at 5%
- Real provider benchmark in this delivery: `not_executed_with_provider`
- Stage 10: not started

Stage 09 adds a repeatable, redacted and auditable benchmark. It does not claim production performance or quality improvement from assembly-only evidence.

## Architecture and modes

Benchmark logic lives in `core/adaptive_context_production_benchmark/`; the production CLI only validates arguments, dispatches the run, and writes reports.

- `assembly`: requires `--dry-run`, records only prompt/context assembly evidence, and has no Provider or quality claim.
- `provider`: runs exactly one baseline or candidate through the existing regression path. Baseline omits production rollout; candidate must explicitly supply the Stage 08.4 rollout flags and evidence. It collects persisted Provider/QA/Quality evidence without changing timeout, attempts, or Provider policy.
- `comparison`: reads completed baseline and candidate artifacts, verifies integrity and contract equality, and never calls Provider.

## Contract and pairing

The comparison contract covers test set, source-file hash, chunk count and boundaries/hashes, profile, model, API timeout, provider attempts, chunk size, maximum output tokens, Prompt Policy version, Quality v5 version, and retry/recovery policy version. Any mismatch returns `benchmark-comparison-invalid` with `ready=false`.

Chunks pair by set name, chunk index, source hash, source offset, and chunk hash. Completion is classified as Provider completed, resume, skipped, or failed. Candidate ACE state is separately classified as activated, sampled fallback, or not sampled. Only Provider-completed chunks with complete QA/quality evidence enter paired quality comparison. Resume evidence has zero current-run calls, attempts, and latency.

## Performance schema

The comparison reports baseline/candidate/delta Provider calls and attempts, total request latency and reduction ratio, timeout and HTTP 503 counts, total execution time, prompt/context token totals and savings, and activated/fallback/sampled/paired chunk counts. Provider latency is accepted only from persisted request timing fields. Assembly time and whole-run elapsed time are never substituted.

The TE v6 frozen runtime currently does not persist per-request latency in its chunk result. A real Provider run lacking that evidence is retained but remains `provider-timing-evidence-incomplete` and cannot become ready.

## Quality and readiness

Quality comparison reports average Quality v5 score, accepted rate, omission, unsupported detail, completeness, recovery, and naturalness action/warning counts. An activated chunk blocks readiness if it adds omission, unsupported detail, or completeness issues; changes accepted to failed; or scores below its paired baseline. Averages cannot hide these per-chunk regressions.

Readiness also requires contract equality, at least one activated paired chunk, no added Provider call, no aggregate accepted/score/completeness regression, no rollback, complete quality and artifact evidence, and rollout at or below 5%. No token or latency gain produces `pass_without_performance_gain` and `ready=false`.

Timeout or HTTP 503 produces `incomplete_external_provider_limitation`. Existing paired evidence remains available, but Stage 09 does not increase timeout/attempts, loop indefinitely, claim gains, or classify the external failure as an ACE functional regression.

## CLI

The regression command supports:

```text
--ace-production-benchmark
--ace-production-benchmark-mode {assembly,provider,comparison}
--ace-production-benchmark-report
--ace-production-benchmark-baseline-stage
--ace-production-benchmark-candidate-stage
--ace-production-benchmark-target-chunk
--ace-production-benchmark-resume-from-stage
```

Baseline provider execution does not include `--ace-production-rollout`. Candidate execution must include the existing Stage 08.4 rollout opt-in, evidence reports, rollout percentage, metrics, and rollback report. Comparison accepts artifact paths or the standard stage names and does not execute translation.

## Artifacts and privacy

Mutable structured artifacts live under `artifacts/te_v7_stage09/`:

- `TE_V7_STAGE09_BASELINE.json`
- `TE_V7_STAGE09_CANDIDATE.json`
- `TE_V7_STAGE09_COMPARISON.json`
- `TE_V7_STAGE09_READINESS.json`

Each completed artifact has `content_redacted=true` and a canonical payload SHA-256 integrity envelope. The stage manifest deliberately labels these as mutable rather than pinning their changing contents. Artifacts reject raw source/translation text, prompts, prior context, API keys, Provider responses, and response bodies.

## Frozen boundary and limitations

Stage 09 does not modify TE v6 runtime, LTS, Provider client/policy, timeout/retry/RPM/backpressure, Quality v5/unified gate, discipline/evidence/naturalness, Prompt Policy/generation rules, Golden Set sources, or Stage 08 freeze invariants. It reuses Stage 08.4.1 rollback results and fails closed when rollback is active.

No real Provider benchmark was run during this implementation. The verified evidence is contract, comparison, privacy/integrity, compatibility, and an actual assembly-only CLI harness. Therefore this delivery makes no real production performance, quality, latency, or API-cost claim.

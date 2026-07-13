# TE v7.0 Stage 08.4.1 — Production Quality Rollback Wiring

Stage 08.4.1 closes the Stage 08.4 production-canary feedback loop. It does not start Stage 09 and does not modify TE v6 frozen runtime, LTS, Provider, Quality v5, prompt, or API contracts.

## Outcome contract

`ProductionOutcome` is an immutable, redacted contract. It records observed and activated chunk counts, QA outcomes, current and baseline scores, new issue codes, omission and unsupported-detail issue codes, anchor/replacement counts, Provider timeout/503 counts, baseline coverage, and evidence completeness. It cannot retain source text, translated text, prompts, previous context, or API keys.

## Evidence mapping

The quality bridge reads existing regression records and resume-state QA summaries. Only a rollout record marked `activated=true`, matched by chunk index and the SHA-256 of its source hash, can contribute ACE quality evidence. Pre-existing resume chunks are snapshotted before regression and excluded. Not-sampled, fallback, shadow-compatible, and Provider-incomplete chunks cannot become ACE regression evidence.

Baseline evidence comes from `--previous-stage` for the same test set, chunk index, and source hash. The baseline must contain an accepted QA result and a real quality score. No fixed or invented baseline is used. Missing, mismatched, rejected, or incomplete baseline evidence produces `quality-evidence-incomplete` and fails closed in Provider validation mode.

Quality v5 and unified QA data are consumed through the QA summary already persisted in resume state. The bridge extracts score, decision, retry state, and issue codes only. It does not create a Provider call or read translated output text.

## Rollback wiring

After the Stage 08.4 regression finishes, the CLI passes real activated-chunk outcomes into `evaluate_automatic_rollback()`: new issue codes, current/baseline quality scores, current/baseline QA failure rates, Provider-call count, anchor mismatch, replacement count, evidence state, kill switch, artifact integrity, and Provider status.

New omission, new unsupported detail, a lower quality score, or a higher QA failure rate produces `rollback=true` and `mode=disabled`. The rollback controller is latched. A disabled rollback report is read before a later resume/session, so later chunks fail closed without deleting existing output. Assembly-only validation remains non-executing: it reports quality evidence as incomplete and `quality_rollback_evaluated=false` rather than claiming a quality pass.

Provider timeout and HTTP 503 remain external limitations and do not directly count as functional ACE regressions. If an activated chunk cannot complete QA because of that limitation, quality evidence is incomplete and the production quality gate cannot pass.

## Metrics

The Stage 08.4 metrics report now replaces default QA and Provider counters with collected outcome values and includes:

- `quality_evidence_complete`
- `quality_rollback_evaluated`
- `quality_rollback_triggered`
- `quality_rollback_reasons`

All metrics, outcome, audit, and rollback payloads remain content-redacted. `provider_calls_added` remains zero.

## Compatibility and boundaries

- Stage 08.4 public APIs and default behavior remain compatible.
- TE v6 Final Release Freeze remains unchanged.
- No LTS, Provider, HTTP, API-key, launcher, Quality v5, or prompt source was modified.
- Production artifacts remain mutable structured artifacts.
- The Stage 08.4.1 manifest is self-describing and does not create a nested SHA-256 manifest chain.
- Stage 09 is not started.

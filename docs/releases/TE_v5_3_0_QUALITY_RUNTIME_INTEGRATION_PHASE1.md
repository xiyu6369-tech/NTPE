# TE v5.3.0 Quality Runtime Integration — Phase 1

## Scope

This stage connects the frozen TE v5.0–v5.2 quality components to the TXT
translation runtime after each provider output and before the existing Runtime
QA decision.

## Runtime flow

```text
Provider output
  -> existing formatter and locked-term normalization
  -> TE v5 QualityRepairPipeline analysis
  -> conservative safe normalization only
  -> per-attempt Quality v5 JSON report
  -> merge critical/high v5 issues into existing Runtime QA
  -> existing retry/fail/warn policy
  -> save accepted chunk
```

## Safety boundary

Phase 1 does not perform semantic rewriting and does not call a provider. It
only applies conservative Unicode/Traditional-Chinese normalization, existing
terminology replacements, and unambiguous orthography repairs such as
`一周 -> 一週`.

High-risk issues such as Hangul residue, abnormal short output, suspected
omission, duplicate paragraphs, or missing locked terminology are reported to
the existing Runtime QA and can trigger its established retry path.

## Compatibility and rollback

Quality v5 integration is enabled by default. Immediate rollback is available:

```text
--no-quality-v5
--no-quality-v5-report
```

Existing provider, timeout, backpressure, resume, output naming, and final
merge behavior are unchanged.

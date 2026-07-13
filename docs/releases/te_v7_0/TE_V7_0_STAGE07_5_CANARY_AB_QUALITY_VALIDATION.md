# TE v7.0 Stage 07.5 — Canary A/B Quality Validation

Adds a redacted, fail-closed quality gate comparing completed baseline and Canary evidence for the same source chunk. The gate requires identical source hash, completed Provider evidence, accepted Canary output, non-regressing quality score, no new omission or unsupported-detail issue, and non-regressing paragraph/length coverage. It does not call Provider and does not auto-enable active mode.

CLI:

```cmd
python launcher_translate.py regression --ace-canary-ab-validate --ace-canary-chunk 3 --ace-canary-ab-baseline-stage <baseline> --ace-canary-ab-canary-stage <canary>
```

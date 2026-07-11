# TE v7.0 Stage 04 — Production Shadow Validation

Stage 04 adds an opt-in production validation harness around literary regression. It forces ACE shadow mode for the duration of the run, preserves the original prompt payload, collects redacted runtime records, restores the caller environment, and writes a JSON validation report.

## CLI

```cmd
python launcher_translate.py regression --set golden --stage TE-v7.0-Stage04-ProductionShadowValidation --profile literary --chunk-size 600 --api-timeout 180 --overwrite --ace-shadow-validate
```

Add `--dry-run` for assembly-only validation without NVIDIA API calls. The report does not contain novel text or prompt text. Stage 04 does not claim translation-quality, provider-latency, timeout, or cost improvement unless a real provider run is separately completed and evidenced.

## Frozen boundary

Only the non-frozen production launcher receives two opt-in arguments and a validation wrapper. TE v6 contracts, LTS runtime, Provider, prompt rules, QA and retry policies remain unchanged.

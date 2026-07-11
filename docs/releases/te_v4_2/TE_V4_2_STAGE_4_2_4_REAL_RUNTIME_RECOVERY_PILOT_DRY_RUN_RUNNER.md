# TE v4.2 Stage-4.2.4 Real Runtime Recovery Pilot Dry-Run Runner

Adds `RealRuntimeRecoveryPilotDryRunRunner`.

The runner accepts only caller-supplied metadata and an injected handler. It does not accept raw source text, does not call providers, does not call HTTP, does not read API keys, and does not modify Translation Runtime or launcher code.

Validation:

```powershell
python ntpe_te_v42_stage424_real_runtime_recovery_pilot_dry_run_runner_test.py
python -m pytest tests\integration\translation_reliability_stage424_real_runtime_recovery_pilot_dry_run_runner_test.py -q
python ntpe_validate.py
```

Next stage: TE v4.2 Stage-4.2.5 Dry-Run Result Bundle.

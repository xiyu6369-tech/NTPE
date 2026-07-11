# TE v3.5 Stage-3.5.1 Runtime Disabled Trial Contract

Stage-3.5.1 defines the contract for a disabled runtime adapter hook integration trial.

## Scope

- Adds `RuntimeDisabledTrialContract`.
- Keeps the trial disabled by default.
- Keeps enabled behavior mock-only.
- Sets runtime, launcher, and provider touch modes to `none`.
- Requires feature flag, opt-in hook guard, and opt-in hook mock bridge prechecks.
- Does not call the mock bridge, create scheduler jobs, connect Translation Runtime, trigger Provider Runtime, call HTTP clients, read API keys, modify launcher flow, or perform real translation.

## Contract Shape

```python
{
    "version": "TE-v3.5",
    "stage": "3.5.1",
    "trial_layer": "runtime_adapter_hook_disabled_trial",
    "default_mode": "disabled",
    "enabled_mode": "mock_only",
    "runtime_touch_mode": "none",
    "launcher_touch_mode": "none",
    "provider_touch_mode": "none",
    "real_translation": False,
}
```

## Next Stage

Recommended next stage: TE v3.5 Stage-3.5.2 Runtime Disabled Trial Guard.

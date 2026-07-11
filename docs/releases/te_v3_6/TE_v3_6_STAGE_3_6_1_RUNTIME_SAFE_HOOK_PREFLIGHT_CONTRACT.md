# TE v3.6 Stage-3.6.1 Runtime Safe Hook Preflight Contract

Stage-3.6.1 defines the contract for safe runtime adapter hook preflight checks.

## Scope

- Adds `RuntimeSafeHookPreflightContract`.
- Keeps preflight disabled by default.
- Keeps enabled behavior mock-only.
- Sets runtime, launcher, and provider touch modes to `none`.
- Requires TE v3.2, TE v3.3, TE v3.4, and TE v3.5 frozen layers.
- Requires feature flag, opt-in hook guard, disabled trial guard, and disabled trial mock bridge prechecks.
- Does not call the disabled trial mock bridge, create scheduler jobs, connect Translation Runtime, trigger Provider Runtime, call HTTP clients, read API keys, modify launcher flow, or perform real translation.

## Contract Shape

```python
{
    "version": "TE-v3.6",
    "stage": "3.6.1",
    "preflight_layer": "runtime_safe_adapter_hook_preflight",
    "default_mode": "disabled",
    "enabled_mode": "mock_only",
    "runtime_touch_mode": "none",
    "launcher_touch_mode": "none",
    "provider_touch_mode": "none",
    "real_translation": False,
}
```

## Next Stage

Recommended next stage: TE v3.6 Stage-3.6.2 Runtime Safe Hook Preflight Guard.

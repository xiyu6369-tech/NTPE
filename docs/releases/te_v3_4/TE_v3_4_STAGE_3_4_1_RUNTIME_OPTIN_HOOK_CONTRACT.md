# TE v3.4 Stage-3.4.1 Runtime Opt-in Hook Contract

Stage-3.4.1 defines the contract for a future optional Translation Runtime adapter hook.

## Scope

- Adds `RuntimeOptInHookContract`.
- Keeps the hook disabled by default.
- Requires explicit opt-in only.
- Keeps execution mode mock-only.
- Defines `translation_runtime` as the only planned caller.
- Requires Stage-3.3 feature flag, disabled guard, and mock orchestrator prechecks.
- Does not execute the mock orchestrator, create scheduler jobs, connect Provider Runtime, call HTTP clients, read API keys, modify launcher flow, or perform real translation.

## Contract Shape

```python
{
    "version": "TE-v3.4",
    "stage": "3.4.1",
    "hook_layer": "runtime_optin_adapter_hook",
    "enabled_by_default": False,
    "activation_mode": "explicit_opt_in_only",
    "execution_mode": "mock_only",
    "allowed_callers": ["translation_runtime"],
    "forbidden_side_effects": [
        "provider_runtime",
        "http_client",
        "api_key",
        "launcher_flow",
        "real_translation",
    ],
    "required_prechecks": [
        "RuntimeIntegrationFeatureFlag",
        "RuntimeIntegrationDisabledGuard",
        "RuntimeIntegrationMockOrchestrator",
    ],
}
```

## Next Stage

Recommended next stage: TE v3.4 Stage-3.4.2 Runtime Opt-in Hook Guard.

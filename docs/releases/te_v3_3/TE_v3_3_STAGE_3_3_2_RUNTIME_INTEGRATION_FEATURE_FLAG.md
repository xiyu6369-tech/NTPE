# TE v3.3 Stage-3.3.2 Runtime Integration Feature Flag

Stage-3.3.2 adds a disabled-by-default feature flag resolver for future runtime scheduler integration.

## Scope

- Adds `RuntimeIntegrationFeatureFlag`.
- Resolves explicit opt-in from provided config or env mappings.
- Gives config precedence over env.
- Does not read real environment variables.
- Does not execute scheduler jobs, connect Provider Runtime, call HTTP clients, read API keys, or modify launcher flow.

## Enable Rules

Integration is enabled only when one of these explicit inputs is provided:

- `config["runtime_scheduler_integration_enabled"] is True`
- `env["NTPE_RUNTIME_SCHEDULER_INTEGRATION"]` is one of `1`, `true`, `yes`, or `enabled`

If config and env conflict, config wins.

## Flag State

```python
{
    "enabled": False,
    "source": "default",
    "reason": "default_disabled",
    "stage": "3.3.2",
    "safety_boundaries": {
        "provider_runtime": "external",
        "http_client": "forbidden",
        "api_key": "forbidden",
        "launcher_flow": "unchanged",
        "translation_runtime_flow": "unchanged",
    },
    "metadata": {},
}
```

## Next Stage

Recommended next stage: TE v3.3 Stage-3.3.3 Runtime Integration Disabled Path Guard.

# TE v3.4 Stage-3.4.2 Runtime Opt-in Hook Guard

Stage-3.4.2 adds a guard for future optional Translation Runtime hook requests.

## Scope

- Adds `RuntimeOptInHookGuard`.
- Validates hook request caller, feature flag state, and contract execution mode.
- Blocks missing requests, invalid callers, disabled flags, and non-mock execution modes.
- Allows only `translation_runtime` caller with enabled flag and `mock_only` contract mode.
- Does not call the mock orchestrator, create scheduler jobs, connect Provider Runtime, call HTTP clients, read API keys, modify launcher flow, or perform real translation.
- Request summaries do not store `source_text`, `text`, or `chunks`.

## Guard Result

```python
{
    "allowed": False,
    "blocked": True,
    "reason": "runtime_integration_disabled",
    "stage": "3.4.2",
    "caller": "translation_runtime",
    "request_summary": {
        "request_type": "unknown",
        "runtime_id": "runtime-state-unknown",
        "chunk_count": 0,
        "has_source_text": False,
        "keys": [],
    },
    "safety_boundaries": {
        "provider_runtime": "external",
        "http_client": "forbidden",
        "api_key": "forbidden",
        "launcher_flow": "unchanged",
        "translation_runtime_flow": "unchanged",
        "real_translation": "forbidden",
    },
}
```

## Next Stage

Recommended next stage: TE v3.4 Stage-3.4.3 Runtime Opt-in Hook Mock Bridge.

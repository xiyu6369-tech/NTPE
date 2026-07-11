# TE v3.6 Stage-3.6.2 Runtime Safe Hook Preflight Guard

Stage-3.6.2 adds `RuntimeSafeHookPreflightGuard`.

## Scope

- Validates safe hook preflight requests against the Stage-3.6.1 contract.
- Blocks missing requests, unsafe default mode, non-mock enabled mode, unsafe touch modes, real translation, and disabled feature flag state.
- Allows a request only when the contract is safe, the feature flag state is explicitly enabled, and a request is present.
- Keeps request summaries free of `source_text`, `text`, and `chunks` content.
- Does not call the disabled trial mock bridge, create scheduler jobs, connect Translation Runtime, trigger Provider Runtime, call HTTP clients, read API keys, modify launcher flow, or perform real translation.

## Guard Result Shape

```python
{
    "allowed": False,
    "blocked": True,
    "reason": "runtime_integration_disabled",
    "stage": "3.6.2",
    "preflight_status": "blocked",
    "request_summary": {...},
    "safety_boundaries": {...},
}
```

## Next Stage

Recommended next stage: TE v3.6 Stage-3.6.3 Runtime Safe Hook Preflight Mock Bridge.

# TE v3.5 Stage-3.5.2 Runtime Disabled Trial Guard

Stage-3.5.2 adds a guard for disabled runtime adapter hook trial requests.

## Scope

- Adds `RuntimeDisabledTrialGuard`.
- Validates the Stage-3.5.1 disabled trial contract before any trial can proceed.
- Blocks missing requests, disabled feature flags, unsafe touch modes, unsafe enabled/default modes, and real translation.
- Allows only safe contract + explicit enabled flag + request, and even then only as a guard decision.
- Does not call `RuntimeOptInHookMockBridge`, create scheduler jobs, connect Translation Runtime, trigger Provider Runtime, call HTTP clients, read API keys, modify launcher flow, or perform real translation.

## Result Shape

```python
{
    "allowed": False,
    "blocked": True,
    "reason": "runtime_integration_disabled",
    "stage": "3.5.2",
    "trial_status": "blocked",
    "request_summary": {
        "request_type": "disabled_trial",
        "runtime_id": "demo-352",
        "chunk_count": 2,
        "has_source_text": True,
        "keys": ["request_type", "runtime_id"],
    },
}
```

## Safety

`request_summary` never stores raw `source_text`, `text`, or `chunks` values.

## Next Stage

Recommended next stage: TE v3.5 Stage-3.5.3 Runtime Disabled Trial Mock Bridge.

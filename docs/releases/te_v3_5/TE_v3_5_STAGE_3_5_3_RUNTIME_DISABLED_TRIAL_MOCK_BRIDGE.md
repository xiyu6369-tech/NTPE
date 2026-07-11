# TE v3.5 Stage-3.5.3 Runtime Disabled Trial Mock Bridge

Stage-3.5.3 adds a mock bridge for disabled runtime adapter hook integration trials.

## Scope

- Adds `RuntimeDisabledTrialMockBridge`.
- Builds the Stage-3.5.1 disabled trial contract.
- Resolves the disabled-by-default runtime integration feature flag.
- Runs the Stage-3.5.2 disabled trial guard.
- Returns `trial_blocked` without calling the hook bridge when the guard blocks.
- Calls the Stage-3.4.3 `RuntimeOptInHookMockBridge` only after the trial guard allows the request.
- Does not connect Translation Runtime, Provider Runtime, HTTP clients, API keys, launcher flow, or real translation.

## Result Shape

```python
{
    "status": "trial_blocked",
    "allowed": False,
    "blocked": True,
    "trial_guard_result": {"reason": "runtime_integration_disabled"},
    "hook_bridge_result": {},
    "runtime_report": {},
    "export_outputs": {},
}
```

## Safety

The bridge keeps enabled behavior mock-only. It does not store raw `source_text`, `text`, or `chunks` values in returned summaries or outputs.

## Next Stage

Recommended next stage: TE v3.5 Stage-3.5.4 Runtime Disabled Trial Boundary Regression.

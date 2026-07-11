# TE v3.2 Stage-3.2.5 Runtime Scheduler Resume Contract

Stage-3.2.5 adds a pure resume contract for scheduler/runtime snapshots.

## Scope

- Adds `RuntimeSchedulerResumeContract`.
- Builds a `resume_plan` from scheduler-compatible or runtime-readable snapshots.
- Validates resume plan structure.
- Does not connect Provider Runtime, HTTP clients, API keys, translation runtime, or launcher flow.

## Public API

```python
contract.build_resume_plan(snapshot)
contract.validate_resume_plan(plan)
```

## Resume Plan

```python
{
    "runtime_id": "runtime-state-unknown",
    "chunks_total": 0,
    "resume_chunks": [],
    "skip_chunks": [],
    "failed_chunks": [],
    "merge_ready": False,
    "resumable": False,
    "reason": "no_chunks",
    "metadata": {},
}
```

## Rules

- `done_chunks` become `skip_chunks`.
- `pending_chunks` and `failed_chunks` become `resume_chunks`.
- `failed_chunks` are preserved.
- `chunks_total == 0` is not resumable.
- complete snapshots return `reason == "already_complete"`.
- snapshots with pending or failed chunks return `resumable == True`.

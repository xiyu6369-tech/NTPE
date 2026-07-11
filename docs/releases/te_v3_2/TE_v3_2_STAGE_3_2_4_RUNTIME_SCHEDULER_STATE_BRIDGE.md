# TE v3.2 Stage-3.2.4 Runtime Scheduler State Bridge

Stage-3.2.4 defines a pure state bridge between runtime-shaped state and scheduler-shaped reports.

## Scope

- Adds `RuntimeSchedulerStateBridge`.
- Converts runtime chunks/session/job state into a scheduler-compatible snapshot.
- Converts scheduler report bundles into runtime-readable snapshots.
- Provides safe defaults for missing fields.
- Does not connect Provider Runtime, HTTP clients, API keys, translation runtime, or launcher flow.

## Public API

```python
bridge.build_scheduler_snapshot(runtime_state)
bridge.build_runtime_snapshot(scheduler_bundle)
bridge.validate_snapshot(snapshot)
```

## Scheduler Snapshot

```python
{
    "runtime_id": "runtime-state-unknown",
    "chunks_total": 0,
    "pending_chunks": [],
    "done_chunks": [],
    "failed_chunks": [],
    "merge_ready": False,
    "metadata": {},
}
```

## Runtime Snapshot

```python
{
    "runtime_id": "runtime-state-unknown",
    "scheduler_summary": {},
    "collector_manifest": {},
    "outputs_count": 0,
    "merge_ready": False,
    "failed_chunk_report": [],
    "metadata": {},
}
```

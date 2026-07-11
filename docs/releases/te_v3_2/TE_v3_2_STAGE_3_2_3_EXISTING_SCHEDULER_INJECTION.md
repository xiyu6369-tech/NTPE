# TE v3.2 Stage-3.2.3 Existing Scheduler Injection

Stage-3.2.3 adds an existing scheduler injection path to `RuntimeSchedulerAdapter`.

## Scope

- Uses a caller-provided `TranslationScheduler` instance.
- Supports dry-run/mock chunks and externally injected mock handlers.
- Returns a runtime report bundle compatible with Stage-3.2.1 and Stage-3.2.2 fields.
- Does not connect Provider Runtime, HTTP clients, API keys, or launcher flow.

## Public API

```python
adapter.run_with_scheduler(chunks, scheduler, handler=None, metadata=None)
```

The method enqueues mock jobs into the provided scheduler, runs them through the injected handler or default mock handler, and returns:

```python
{
    "scheduler_summary": {},
    "collector_manifest": {},
    "failed_chunk_report": [],
    "dashboard_report": {},
    "outputs_count": 0,
    "merge_ready": False,
    "export_outputs": {},
}
```

For this injection path, `merge_ready` is true only when all injected jobs finish successfully.

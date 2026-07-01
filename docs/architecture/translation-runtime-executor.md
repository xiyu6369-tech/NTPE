# Foundation-06.5 Translation Runtime Executor

This module connects Prompt Runtime output to a model adapter and normalizes the returned text into an executor result.

## Flow

```text
Translation Job
  -> Segment
  -> Context Bundle
  -> Prompt Package
  -> Translation Runtime Executor
  -> Model Adapter
  -> Executor Result
  -> Segment Status / Job Results / Trace / Metrics
```

## Compatibility

Foundation-06.5 is additive. It introduces `translation/executor/` and does not modify existing Foundation-06.0 to 06.4 contracts.

## Default Adapter

`MockModelAdapter` is deterministic and offline-safe. It is intended for unit, integration, smoke, and CI tests before real model adapters are attached in later foundations.

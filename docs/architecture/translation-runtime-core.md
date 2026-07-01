# NTPE Foundation-06.6 Translation Runtime Core

Foundation-06.6 integrates the Translation Runtime layers delivered in 06.0 through 06.5 into one runtime entry point.

## Runtime Flow

```text
Translation Job
  -> Translation Session
  -> Segment iteration
  -> Context Runtime
  -> Prompt Runtime
  -> Translation Runtime Executor
  -> Translation Result
  -> Session progress / events / manifest
```

## Public Entry Point

```python
from translation.runtime import create_translation_runtime

runtime = create_translation_runtime()
result = runtime.execute(job)
```

## Added Contracts

- `translation_runtime_session`
- `translation_runtime_core_result`
- `translation_runtime_core` manifest

## Compatibility

This update is additive and dictionary-compatible with Foundation-06.0 to Foundation-06.5. It does not require migration of existing Job, Segment, Context Bundle, Prompt Package, or Executor Result dictionaries.

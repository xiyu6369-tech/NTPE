# NTPE Translation Runtime Flow

Foundation-06.3 introduces the Translation Context Runtime. It builds a versioned context bundle for each segment before the prompt and model layers run.

```text
Translation Job
  -> Segment Queue
  -> Translation Context Runtime
  -> Production Runtime
  -> Translation Result
```

The context bundle is intentionally dictionary-compatible and preserves existing metadata. It can be cached by job id, segment id, and version.

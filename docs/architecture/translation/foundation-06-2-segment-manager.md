# Foundation-06.2 Translation Segment Manager

Foundation-06.2 adds a segment orchestration layer above the Foundation-06.1 Translation Job Manager.

## Responsibilities

- Normalize dictionary-based segment payloads.
- Maintain segment ordering by priority and index.
- Provide a ready queue for translation execution.
- Respect simple segment dependencies.
- Track retry attempts without losing the original segment payload.
- Split oversized segments into mergeable child segments.
- Merge child segment outputs back into a stable result payload.
- Export segment metrics and manifest data for runtime, UI, and adapters.

## Queue Model

A segment queue contains:

- `segments`
- `cursor`
- `events`
- `status`
- `created_at`
- `updated_at`

The manager does not replace the Foundation-06.0/06.1 contracts. It accepts existing segment dictionaries and preserves unknown fields during normalization.

## Retry Model

Each managed segment contains a `retry` object:

```json
{
  "attempts": 0,
  "max_attempts": 3
}
```

A failed segment returns to `pending` while retry capacity remains. After retry capacity is exhausted, it becomes `failed`.

## Compatibility

Foundation-06.2 is additive. Existing Translation Job and Segment contracts remain valid.

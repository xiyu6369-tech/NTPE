# Foundation-06.1 Translation Job Manager

Foundation-06.1 adds a non-destructive management layer above the Foundation-06.0 translation runtime contracts.

## Responsibilities

- Create translation jobs from segment dictionaries.
- Normalize legacy or partial job payloads.
- Validate job and segment structure.
- Update segment lifecycle state.
- Calculate job progress counters.
- Export a stable job manifest for runtime, adapter, and UI usage.

## Status Model

Segment statuses:

- `pending`
- `running`
- `completed`
- `failed`
- `skipped`

Job statuses:

- `pending`
- `running`
- `completed`
- `failed`
- `partial`

## Compatibility

This module accepts dictionary-based contracts and does not require existing Foundation-06.0 objects to be replaced. Existing fields are preserved during normalization.

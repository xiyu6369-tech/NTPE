# Chunk Cache V2 Design

Status: design-only; not implemented or production-connected.

- Cache hits require exact source/prompt/provider/model identity and accepted quality status.
- Partial and timed-out output is never completed; retry only the failed chunk.
- Assembly refuses gaps and duplicates and preserves current collector ordering.
- ResumeJournal stores references; there is no second runtime.

Canonical machine-readable design: companion JSON file.

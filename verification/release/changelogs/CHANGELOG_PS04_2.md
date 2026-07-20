# NTPE 1.2 PS-04.2 — Translation Progress Visibility Hotfix

## Purpose

Improve usability during long translation/regression runs by showing live progress steps and writing a live progress JSON file.

## Added

- `[NTPE PROGRESS]` messages for input reading, splitting, package creation, provider request attempts, QA attempts, chunk saving, final assembly, and completion.
- Per-file live progress file: `<output>/<stem>_live_progress.json`.
- `--no-progress` CLI switch for `txt`, `batch`, and `regression`.
- Dry-run tests validating progress output without calling provider APIs.

## Compatibility

- Fully backward compatible.
- No Foundation v1.0 or NTPE 1.1 LTS frozen behavior is removed.
- Progress logging is additive and can be disabled with `--no-progress` or `set NTPE_PROGRESS=0`.


## NTPE 1.2 Production Stabilization — PS-02 Literary Regression Runner

- Added `launcher_translate.py corpus list/init`.
- Added `launcher_translate.py regression` for Smoke_Set/A/B.
- Separated real translation input from literary regression corpus.
- Added PS-02 integration/smoke/root tests.

# NTPE 1.2 Professional - Stage-17.8 Production Platform Freeze

## Added
- Production platform freeze manifest for Stage-17.1 through Stage-17.7.
- Non-invasive production platform freeze audit.
- Stage-17.8 launcher and integration tests.

## Compatibility
- Additive-only update; no frozen Foundation v1.0 or NTPE 1.1 LTS behavior is modified.
- Keeps Stage-17.7 Production Runtime Integration operational.
- Preserves Stage-17 public workflow/runtime compatibility.

---

# NTPE 1.2 Professional - Stage-17.7 Production Runtime Integration

## Added
- Production runtime integration bridge for Stage-17 workflow execution.
- Runtime context/result/event/metric helpers for production execution.
- Optional integration points for scheduler, resource optimizer, review, export, and dashboard layers.
- Stage-17.7 launcher and integration test.

## Compatibility
- Keeps Stage-17.1 Workflow Engine public API intact.
- Does not modify frozen Stage-14 Provider Framework, Stage-15 Translation Quality Engine, or Stage-16 Intelligence Layer.


## Stage-18.11 Translation Timeout & Debug Hotfix

- Added explicit connect/read timeout tuple for NVIDIA API requests.
- Added `NTPE_TRANSLATE_DEBUG=1` request progress output.
- Added clearer timeout/request errors.
- Added doctor output for timeout/debug environment variables.

## NTPE 1.2 Stage-18.14 — Simplified Chinese QA Hotfix

- Changed simplified-Chinese QA from hard failure to default normalize/metric behavior.
- Added `--simplified-chinese-policy normalize|warn|fail` to production translator CLI.
- Preserved strict mode through `fail` for audit-focused runs.
- Kept simplified-hit metrics visible in manifests and QA reports.
## PS-03 Translation Corpus Evaluation Engine

- Added literary quality evaluation reports for regression outputs.
- Added `launcher_translate.py evaluate --stage <stage>`.
- Added diff and regression history reports under `tests/literary/outputs/`.
- Added PS-03 tests and documentation.



## PS-04.1 Regression Timeout & Encoding Hotfix

- Added regression CLI timeout options.
- Added `golden` / `smoke` / `regression` aliases.
- Replaced mojibake-prone timeout guidance with ASCII-safe text.

## Translation Engine Refactoring v1.2

- Added Literary Style Engine for conservative Chinese-novel phrasing cleanup.
- Strengthened simplified-to-traditional normalization for provider output.
- Updated compact literary prompt policy for idiom, action, and narrative style.
- Added TER-v1.2 validation, integration, and smoke tests.
## Translation Engine Refactoring v1.3

- Added speed/prompt compression pass for literary translation.
- Reduced fixed prompt policy/context text.
- Reduced default max output token budget for faster small-regression runs.
- Added max token visibility to progress/debug output.
- Added TER-v1.3 regression tests.



## Translation Engine Refactoring v1.4
- Added speed-oriented prompt compression and semantic accuracy cleanup.
- Lowered short-segment max output tokens for Smoke_Set speed.
- Preserved TER-v1.3 compact prompt structure.

## Translation Engine Refactoring v1.5 — Literary Polish v2

- Preserves TER-v1.4 prompt compression.
- Improves Smoke_Set literary phrasing for eyebrows, ambiguous short replies, and worst-case situation wording.
- Adds TER-v1.5 tests.
## Translation Engine Refactoring v1.6

- Added semantic guard for literary polish regressions.
- Prevents ambiguous-answer cleanup from producing `留下了鄭泰義一個回答`.
- Deduplicates repeated disappearance descriptions in Smoke/Golden style passages.
## Translation Engine Refactoring v1.7

- Added TER-v1.7 Narrative Naturalness cleanup.
- Improved imminent-action wording, viewpoint pronouns, and fatigue narration.
- Preserved TER-v1.6 semantic guards and prompt compression.



## Translation Engine Refactoring v1.8

- Added Character Tone guard for Ilay.
- Added adaptive short-chunk first-attempt timeout.
- Kept TER-v1.7 Prompt/profile structure unchanged.

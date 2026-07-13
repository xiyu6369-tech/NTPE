# TE v6.0.0 Stable Final Release Freeze

TE v6.0 freezes the completed Translation Discipline, Translation Evidence, and Translation Naturalness lines without adding translation behavior. Stages 01 through 12.5, including 08.1, 10.1.1, and 12.4.1, are covered by the final immutable release contract.

## Production validation

`TE-v6.0-Stage10.1-ProductionValidation` completed successfully: 1 success, 0 skipped, 0 failed, 1 total. Final freeze reuses the saved Golden Set evidence and never modifies Golden Set source files or calls a Provider.

## Frozen behavior

- Provider: NVIDIA routing, `meta/llama-3.3-70b-instruct`, 40 RPM, timeout propagation, attempts, retry wait, 503 backpressure, request accounting, and budget remain unchanged.
- Prompt: one injection source, discipline/adaptive feedback/naturalness feature flags, rollback, and token observability remain unchanged; eight active generation rules remain active.
- Quality and retry: Quality v5, legacy adapter, unified gate, local repair, best attempt, completeness, repetition, unsupported-detail blocking, retry tiers, evidence requirement, fail-closed merge, and resume remain unchanged.
- Evidence: offsets, monotonic alignment, confidence/reliability, evidence-to-retry, targeted merge, and audit are frozen. Unreliable evidence cannot authorize targeted retry.
- Naturalness: faithful, period-appropriate fluent Traditional Chinese is preferred without forced Taiwan-specific localization. Canonicalization is safe-only; voice/register remains non-blocking and cannot rewrite meaning, viewpoint, emotion, relationship distance, or period diction.

## Retry and output contracts

Chunk resume, cached output, failure manifest, best failed candidate, package metadata, output naming, and Golden Set output structure are frozen. Provider retry remains budgeted and best-attempt fallback remains available.

## Known limitations

- Stable freeze validates recorded production evidence; it deliberately does not make a live NVIDIA request.
- Voice/register feedback is advisory and does not enter the active generation rule count.
- Targeted retry remains unavailable when evidence is missing, unreliable, or unsafe to merge.

## Upgrade, rollback, and release checklist

Existing v6.0 integrations should use `core.translation_release.build_te_v6_release_contract()` and `validate_te_v6_release()`. Roll back prompt behavior with the existing `NTPE_PROMPT_DISCIPLINE`, `NTPE_ADAPTIVE_PROMPT_FEEDBACK`, and `NTPE_NATURALNESS_POLICY` controls; no new rollback mechanism is introduced.

- [x] Stage 01-12.5 freeze APIs importable
- [x] Golden Set production validation successful
- [x] Freeze readiness fail-closed gate ready with no blockers
- [x] Comparison and final validation reports regenerated
- [x] Manifest inventory and SHA-256 verified
- [x] DELTA ZIP inventory verified
- [ ] Commit `release(te-v6.0): finalize translation engine stable freeze`
- [ ] Tag `te-v6.0.0`

Commit and tag entries intentionally remain pending; this stage does not commit, push, or tag.

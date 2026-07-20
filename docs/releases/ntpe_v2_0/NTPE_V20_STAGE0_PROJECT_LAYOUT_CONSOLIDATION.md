# NTPE 2.0 Stage 0 — Project Layout Consolidation

## Outcome

Stage 0 performs low-risk root-directory organization only. Existing historical Root Wrappers remain in place and are not deduplicated, consolidated, or deleted. Historical non-Python instruction, changelog, and patch files are stored under `verification/`.

## Root Layout

- Initial root files: 424
- Final root files: 348
- Initial root Python files: 339
- Final root Python files: 339
- Non-Python historical files moved: 76
- Historical Root Wrappers retained: 321
- Unexpected root files: 0
- Unclassified root files: 0

The root Python target of 20 or fewer is intentionally deferred by the corrected scope. `RETAINED_ROOT_WRAPPERS.json` is the handoff inventory for a possible later cleanup stage.

## Compatibility and Manifests

- Existing Root Wrappers retain their original paths and contents.
- 321 historical Root Wrappers and 49 consumer files are explicitly excluded and verified identical to HEAD.
- Wrapper deduplication and test-entry consolidation are not performed.
- Frozen manifests are not rewritten.
- Additional compatibility wrappers created: 0.

## Boundaries

- Provider requests: 0
- Network requests: 0
- Provider files modified: 0
- Runtime files modified: 0
- Production hooks added: 0
- Translation output behavior modified: false
- Frozen manifests modified: 0
- Stage 12.5.8 claim or response regenerated: no
- Commit: HOLD
- Push: NO
- Tag: NO

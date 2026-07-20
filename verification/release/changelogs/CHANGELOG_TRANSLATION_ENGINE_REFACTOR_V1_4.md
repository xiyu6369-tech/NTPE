# Translation Engine Refactoring v1.4

## Focus
- Speed + Semantic Accuracy.
- Preserve TER-v1.3 prompt compression while lowering short-text max output tokens.
- Improve semantic cleanup for ambiguous short replies and common Korean-to-Chinese literary phrasing.

## Changes
- Prompt v5: shorter policy and output contract.
- Dynamic max output token sizing for short smoke/regression segments.
- Added conservative cleanup for ambiguous reply constructions such as 「當然」後離去.
- Improved awkward phrasing cleanup: duplicated particles, semantic over-explanation, and literal fatigue phrases.

## Validation
- Unit launcher: PASS
- Integration launcher: PASS
- Smoke launcher: PASS
- ntpe_validate.py: ALL PASS

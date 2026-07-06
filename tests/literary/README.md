# NTPE Literary Regression Corpus

NTPE Production Stabilization uses this folder to validate translation quality, not only program execution.

## Test sets

- `Test_Set_0`: tiny smoke corpus for quick API/prompt/name-lock checks.
- `Test_Set_A`: golden regression corpus. Keep this stable once selected.
- `Test_Set_B`: rotating regression corpus. Replace periodically to avoid overfitting one passage.
- `outputs/PS-xx`: store generated outputs for manual comparison between Production Stabilization stages.

## Rule

Do not optimize only for one passage. A PS stage passes only when it improves or preserves literary quality on Test_Set_A and does not regress on Test_Set_B.

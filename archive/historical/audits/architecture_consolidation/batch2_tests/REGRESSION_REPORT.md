# Batch 2 Critical Regression Report

## Required families

| Family | Command | Result |
|---|---|---|
| Runtime | `python ntpe_te_v37_runtime_readiness_freeze_test.py` | PASS |
| Provider security | `python ntpe_stage14_6_provider_security_test.py` | PASS |
| Resume/recovery | `python ntpe_te_v31_stage314_resume_journal_test.py` | PASS |
| Output assembly | `python ntpe_te_v31_stage313_result_collector_test.py` | PASS |
| Output merge integrity | `python ntpe_te_v611_stage114_safe_targeted_merge_validation_test.py` | PASS |
| Translation quality critical path | `python ntpe_te_v540_smart_local_repair_pipeline_test.py` | PASS |

All commands use local, fake, mock, or static evidence paths. No real Provider
authorization was supplied and no real Provider was executed.

## Additional legacy observation

`python -m pytest -q tests/lts_stage_05/launcher_output_formatter_test.py`
failed because the current launcher rejects the historical
`--no-output-formatter` and `--no-taiwan-normalization` CLI flags. Neither that
protected test nor the production launcher was modified in Batch 2. Current
Result Collector and Safe Targeted Merge output-assembly regressions passed.

# TE v5.1 Quality Repair Pipeline Milestone

## Stages

1. Stage-5.1.1 Quality Repair Planner
2. Stage-5.1.2 Quality Retry Orchestrator
3. Stage-5.1.3 Quality Chunk Rebuild Planner
4. Stage-5.1.4 Quality Repair Pipeline
5. Stage-5.1.5 Boundary Regression
6. Stage-5.1.6 Freeze

## Flow

Quality Core Pipeline
→ Quality Repair Planner
→ Adaptive Retry Policy
→ Adaptive Chunk Split Planner
→ Retry / rebuild mapping

This milestone only produces retry and rebuild decisions. It does not call a
provider, execute translation, modify Translation Runtime, or modify launcher.

## Validation

```powershell
python tools\apply_te_v51_quality_repair_pipeline.py
python ntpe_te_v50_quality_core_milestone_test.py
python ntpe_te_v50_stage506_quality_core_freeze_test.py
python ntpe_te_v51_quality_repair_pipeline_milestone_test.py
python ntpe_te_v51_stage515_quality_repair_boundary_regression_test.py
python ntpe_te_v51_stage516_quality_repair_pipeline_freeze_test.py
python -m pytest tests\integration\translation_quality_v50_quality_core_milestone_test.py tests\integration\translation_quality_v50_stage506_freeze_test.py tests\integration\translation_quality_v51_quality_repair_pipeline_test.py tests\integration\translation_quality_v51_stage515_boundary_regression_test.py tests\integration\translation_quality_v51_stage516_freeze_test.py -q
python ntpe_validate.py
```

# NTPE 1.0 Beta — Stage-12.4 REST Pipeline API

## Added

- `external_api/rest_pipeline.py`
- REST Pipeline API adapter
- Pipeline create/list/get routes
- Pipeline stage append route
- Pipeline lifecycle routes
- Pipeline status and summary routes
- Stage-12.4 REST Pipeline API tests
- Stage-12.4 Translation Validation report

## Changed

- `external_api/rest_api.py` now registers `RestPipelineApi`.
- `external_api/__init__.py` exports REST Pipeline API symbols.

## Compatibility

- Uses frozen Runtime Pipeline API only.
- Does not modify frozen Runtime API, Platform Services, Workflow, Integration, CLI, SDK, or Foundation modules.
- Additive-only update.

## Test Result

```text
Stage-12.4 REST Pipeline API: PASS
Translation Validation Stage-12.4: PASS
Stage-12.3 REST Job API: PASS
```

## Commit

```bash
git add external_api/rest_pipeline.py external_api/rest_api.py external_api/__init__.py tests/beta_stage_12_4 README_NTPE_1_0_Beta_Stage_12_4.txt CHANGELOG_Stage_12_4.md Translation_Validation_Report_Stage_12_4.md
git commit -m "Stage-12.4 REST Pipeline API"
git push
git tag beta-stage-12.4-rest-pipeline-api
git push origin beta-stage-12.4-rest-pipeline-api
```

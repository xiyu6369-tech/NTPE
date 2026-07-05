# NTPE 1.0 Beta — Stage-12.1 External API / REST Core

## Added

- Added `external_api/rest_models.py`.
- Added `external_api/rest_router.py`.
- Added `external_api/rest_api.py`.
- Added REST facade routes:
  - `GET /health`
  - `GET /v1/runtime/manifest`
  - `POST /v1/runtime/execute`
- Added Stage-12.1 REST tests.
- Added Stage-12.1 Translation Validation report.

## Changed

- No frozen modules were modified.
- Runtime API is used only through its public frozen facade.

## Compatibility

- Foundation v1.0: PASS
- CLI: PASS
- SDK: PASS
- Integration: PASS
- Workflow: PASS
- Platform Services: PASS
- Runtime API Freeze: PASS

## Tests

```text
Stage-12.1 External API / REST Core: PASS
Translation Validation Stage-12.1: PASS
Stage-11.8 Runtime API Freeze: PASS
```

## Commit

```bash
git add external_api tests/beta_stage_12_1 README_NTPE_1_0_Beta_Stage_12_1.txt CHANGELOG_Stage_12_1.md Translation_Validation_Report_Stage_12_1.md
git commit -m "Stage-12.1 External API REST Core"
git push
git tag beta-stage-12.1-external-api-rest-core
git push origin beta-stage-12.1-external-api-rest-core
```

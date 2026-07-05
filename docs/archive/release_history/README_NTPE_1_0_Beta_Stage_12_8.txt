NTPE 1.0 Beta — Stage-12.8 External API Freeze

Status: PASS

Purpose:
Freeze the External API / REST Layer public contract introduced during Stage-12.1 through Stage-12.7.

Scope:
- REST Core
- REST Session API
- REST Job API
- REST Pipeline API
- REST Event API
- REST Resource API
- REST Middleware
- REST Auth Hooks

Compatibility:
- Foundation v1.0: Frozen compatible
- CLI: Frozen compatible
- SDK: Compatible
- Integration: Frozen compatible
- Workflow: Frozen compatible
- Platform Services: Frozen compatible
- Runtime API: Frozen compatible

Rules after freeze:
- Do not mutate existing public REST request/response contracts.
- Do not remove existing routes.
- Do not bypass Runtime API when calling lower layers.
- Future changes must be additive or introduced in a new stage.

Test:
python tests/beta_stage_12_8/launcher_external_api_freeze_test.py
python tests/beta_stage_12_8/launcher_translation_validation_stage_12_8_test.py

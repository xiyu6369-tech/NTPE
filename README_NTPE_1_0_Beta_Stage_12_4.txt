NTPE 1.0 Beta — Stage-12.4 REST Pipeline API

Status: PASS

This stage adds the external REST Pipeline API adapter.

Added:
- external_api/rest_pipeline.py
- REST pipeline routes for create/list/get/stage/validate/start/pause/resume/complete/fail/cancel/status/summary
- Runtime Pipeline API bridge through the frozen Runtime API layer only
- Stage-12.4 tests
- Translation validation report

Compatibility:
- Foundation v1.0: compatible
- CLI: compatible
- SDK: compatible
- Integration: compatible
- Workflow: compatible
- Platform Services: compatible
- Runtime API Freeze: compatible

This stage is additive only and does not modify frozen internal runtime or workflow implementations.

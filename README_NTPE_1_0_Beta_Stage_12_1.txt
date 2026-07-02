NTPE 1.0 Beta — Stage-12.1 External API / REST Core

Status: PASS

Stage-12.1 adds the initial External API / REST layer as an additive facade over
the frozen Runtime API surface. It does not call Runtime, Workflow, Platform
Services, Foundation, CLI, SDK, or Integration internals directly.

Added modules:
- external_api/__init__.py
- external_api/rest_models.py
- external_api/rest_router.py
- external_api/rest_api.py

Core routes:
- GET  /health
- GET  /v1/runtime/manifest
- POST /v1/runtime/execute

Compatibility:
- Foundation v1.0: preserved
- CLI: preserved
- SDK: preserved
- Integration: preserved
- Workflow: preserved
- Platform Services: preserved
- Runtime API Freeze: preserved

Validation:
- Stage-12.1 External API / REST Core: PASS
- Translation Validation Stage-12.1: PASS
- Stage-11.8 Runtime API Freeze: PASS

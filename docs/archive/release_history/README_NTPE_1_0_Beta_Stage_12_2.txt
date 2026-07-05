NTPE 1.0 Beta — Stage-12.2 REST Session API

Scope
-----
Stage-12.2 adds HTTP-like REST session routes to the External API layer.
The implementation is additive and delegates session operations to the frozen
Runtime Session API surface introduced in Stage-11.2 and frozen in Stage-11.8.

Added
-----
- external_api/rest_session.py
- REST session route adapter
- Session create/list/get routes
- Session transition routes
- Resume-state route
- Stage-12.2 tests
- Translation validation report

Routes
------
POST /v1/sessions
GET  /v1/sessions
GET  /v1/sessions/{session_id}
POST /v1/sessions/{session_id}/activate
POST /v1/sessions/{session_id}/pause
POST /v1/sessions/{session_id}/complete
POST /v1/sessions/{session_id}/fail
POST /v1/sessions/{session_id}/cancel
GET  /v1/sessions/{session_id}/resume-state

Compatibility
-------------
Foundation v1.0: preserved
CLI: preserved
SDK: preserved
Integration: preserved
Workflow: preserved
Platform Services: preserved
Runtime API: preserved
External API Stage-12.1: preserved

Test
----
python tests/beta_stage_12_2/launcher_rest_session_api_test.py
python tests/beta_stage_12_2/launcher_translation_validation_stage_12_2_test.py

# NTPE 1.0 Beta — Stage-12.2 REST Session API

## Added
- `external_api/rest_session.py`
- REST Session API adapter backed by frozen Runtime Session API operations
- Session create/list/get endpoints
- Session transition endpoints
- Session resume-state endpoint
- Stage-12.2 REST session tests
- Stage-12.2 translation validation report

## Changed
- `external_api/rest_api.py` now registers session routes through an additive adapter.
- `external_api/__init__.py` exports REST Session API symbols.

## Compatibility
- Foundation v1.0: PASS
- CLI: PASS
- SDK: PASS
- Integration: PASS
- Workflow: PASS
- Platform Services: PASS
- Runtime API Freeze: PASS
- External API Stage-12.1: PASS

## Tests
```text
Stage-12.2 REST Session API: PASS
Translation Validation Stage-12.2: PASS
Stage-12.1 External API REST Core: PASS
Stage-11.8 Runtime API Freeze: PASS
```

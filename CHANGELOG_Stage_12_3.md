# NTPE 1.0 Beta — Stage-12.3 REST Job API

## Added
- Added `external_api/rest_job.py`.
- Added REST-style job collection routes:
  - `POST /v1/jobs`
  - `GET /v1/jobs`
- Added REST-style job item and lifecycle routes:
  - `GET /v1/jobs/{job_id}`
  - `POST /v1/jobs/{job_id}/start`
  - `POST /v1/jobs/{job_id}/pause`
  - `POST /v1/jobs/{job_id}/resume`
  - `POST /v1/jobs/{job_id}/stop`
  - `POST /v1/jobs/{job_id}/cancel`
  - `POST /v1/jobs/{job_id}/complete`
  - `POST /v1/jobs/{job_id}/fail`
  - `GET /v1/jobs/{job_id}/status`
  - `GET /v1/jobs/{job_id}/result`
- Added Stage-12.3 REST Job API tests.
- Added Stage-12.3 Translation Validation report.

## Changed
- Updated `external_api/rest_api.py` to register the REST Job API adapter.
- Updated `external_api/__init__.py` public exports.

## Compatibility
- Uses only the frozen Runtime Job API operation surface.
- No changes to Foundation, CLI, SDK, Integration, Workflow, Platform Services, or Runtime API internals.
- Additive update only.

## Test Result
```text
Stage-12.3 REST Job API: PASS
Translation Validation Stage-12.3: PASS
Stage-12.2 REST Session API: PASS
Stage-12.1 External API REST Core: PASS
Stage-11.8 Runtime API Freeze: PASS
```

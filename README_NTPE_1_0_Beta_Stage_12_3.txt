NTPE 1.0 Beta — Stage-12.3 REST Job API

Scope
-----
Stage-12.3 adds REST-style job endpoints on top of the frozen Runtime Job API.
It does not mutate Runtime, Workflow, Foundation, CLI, SDK, Integration, Platform
Services, or Runtime API frozen contracts.

Added
-----
- external_api/rest_job.py
- REST Job route registration through RestApi
- /v1/jobs collection endpoints
- /v1/jobs/{job_id} item endpoint
- /v1/jobs/{job_id}/start|pause|resume|stop|cancel|complete|fail transition endpoints
- /v1/jobs/{job_id}/status and /result read endpoints
- Stage-12.3 REST Job API tests
- Stage-12.3 Translation Validation report

Compatibility
-------------
- Foundation v1.0: compatible
- CLI Frozen: compatible
- SDK: compatible
- Integration Frozen: compatible
- Workflow Frozen: compatible
- Platform Services Frozen: compatible
- Runtime API Frozen: compatible

Result
------
PASS

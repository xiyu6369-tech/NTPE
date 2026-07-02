NTPE 1.0 Beta - Stage-13.4 Web UI Job Page

Scope
-----
Stage-13.4 adds a framework-neutral Web UI Job Page.

Added
-----
- web_ui/job_models.py
- web_ui/job_page.py
- WebUiRestClient job helpers
- WebUiApp /jobs rendering
- Stage-13.4 tests

Compatibility
-------------
- Uses External API / REST layer only.
- Uses REST Job API only for job data and actions.
- Does not access Workflow or Runtime internals directly.
- Does not modify frozen Runtime API or External API contracts.
- Additive only.

Validation
----------
- Stage-13.4 Web UI Job Page: PASS
- Translation Validation Stage-13.4: PASS
- Stage-13.3 Web UI Session Page: PASS

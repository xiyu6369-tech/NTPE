# NTPE 1.0 Beta - Stage-13.4 Web UI Job Page

## Added
- Framework-neutral Web UI Job Page.
- Job page view model and declarative job actions.
- REST Job API-backed Web UI client helpers.
- `/jobs` render integration in WebUiApp.
- Stage-13.4 Web UI and Translation Validation tests.

## Changed
- `web_ui/__init__.py` exports Stage-13.4 job page API.
- `web_ui/web_app.py` reports `job_page_stage` in manifest.

## Compatibility
- External API / REST layer remains frozen-compatible.
- Runtime API remains frozen-compatible.
- Web UI uses REST Job API only.
- No direct access to job/workflow internals.

## Test Result
PASS

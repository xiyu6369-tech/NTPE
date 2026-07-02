NTPE 1.0 Beta - Stage-13.7 Web UI Resource Page

Status: PASS

Summary
- Adds a framework-neutral Web UI Resource Page.
- Uses only the REST Resource API surface.
- Does not call Runtime, Workflow, Platform Services, or Translation internals directly.
- Preserves all Frozen module compatibility.

Added
- web_ui/resource_models.py
- web_ui/resource_page.py
- WebUiRestClient resource methods
- WebUiApp resource page rendering and manifest surface
- tests/beta_stage_13_7/

Validation
- Stage-13.7 Web UI Resource Page: PASS
- Translation Validation Stage-13.7: PASS
- Stage-13.6 Web UI Event Page: PASS

Commit
- Stage-13.7 Web UI Resource Page

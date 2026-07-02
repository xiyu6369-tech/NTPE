# NTPE 1.0 Beta — Stage-13.5 Web UI Pipeline Page

## Added
- `web_ui.pipeline_models` for framework-neutral pipeline page view models.
- `web_ui.pipeline_page` for REST-backed pipeline page rendering.
- Pipeline helper methods on `WebUiRestClient`.
- `/pipelines` rendering integration in `WebUiApp`.
- Stage-13.5 Web UI Pipeline Page tests.
- Stage-13.5 Translation Validation report.

## Changed
- `web_ui.__init__` now exports Pipeline Page public symbols.
- `web_ui.web_app` now exposes `pipeline_view()` and manifest metadata.

## Compatibility
- Uses REST Pipeline API only.
- Does not access Runtime Pipeline internals directly.
- Does not modify frozen Runtime API or External API contracts.
- Additive Web UI update only.

## Result
PASS

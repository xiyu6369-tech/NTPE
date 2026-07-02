NTPE 1.0 Beta — Stage-13.6 Web UI Event Page

Status: PASS

This stage adds the Web UI Event Page as an additive, framework-neutral UI view.
The page communicates only through the REST Event API and does not access runtime,
workflow, or event internals directly.

Added:
- web_ui/event_models.py
- web_ui/event_page.py
- WebUiRestClient event helpers
- WebUiApp /events render integration
- Stage-13.6 tests

Compatibility:
- Foundation v1.0 Frozen: PASS
- Runtime API Frozen: PASS
- External API Frozen: PASS
- Web UI Core: PASS
- Translation Validation: PASS

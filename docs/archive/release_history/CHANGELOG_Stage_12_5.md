# NTPE 1.0 Beta — Stage-12.5 REST Event API

## Added
- REST Event API adapter.
- Event publish/get/list/filter/summary/clear routes.
- Runtime Event API bridge through the frozen Runtime API surface.
- Stage-12.5 REST Event API tests.
- Stage-12.5 Translation Validation report.

## Changed
- `external_api/rest_api.py` now registers REST Event API routes.
- `external_api/__init__.py` exports REST Event API symbols.

## Compatibility
- Additive only.
- No frozen module API changes.
- Uses frozen Runtime Event API only.

## Tests
- Stage-12.5 REST Event API: PASS
- Translation Validation Stage-12.5: PASS
- Stage-12.4 REST Pipeline API: PASS

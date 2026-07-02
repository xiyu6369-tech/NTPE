# NTPE 1.0 Beta — Stage-12.6 REST Resource API

## Added
- REST Resource API adapter.
- Resource create/get/list/filter/summary routes.
- Resource reserve/attach/release/delete transition routes.
- Runtime Resource API bridge through the frozen Runtime API facade.
- Stage-12.6 REST Resource API tests.
- Stage-12.6 Translation Validation report.

## Changed
- Extended `external_api.RestApi` manifest with `resource_api`.
- Extended `external_api.__init__` public exports with REST Resource API symbols.

## Compatibility
- Additive only.
- Does not modify frozen Foundation, CLI, Integration, Workflow, Platform Services, or Runtime API public contracts.
- REST layer delegates to Runtime Resource API only.

## Tests
- Stage-12.6 REST Resource API: PASS
- Translation Validation Stage-12.6: PASS
- Stage-12.5 REST Event API: PASS

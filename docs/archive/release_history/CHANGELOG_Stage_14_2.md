# NTPE 1.0 Beta — Stage-14.2 Release Manifest

## Added
- Release manifest schema.
- Component manifest model.
- Dependency manifest model.
- Release manifest builder and loader.
- Stage-14.2 release manifest validation tests.
- Release validation and translation validation reports.

## Changed
- `packaging/__init__.py` exports Stage-14.2 release manifest interfaces.

## Compatibility
- Foundation v1.0: compatible.
- CLI: compatible.
- SDK: compatible.
- Integration: compatible.
- Workflow: compatible.
- Platform Services: compatible.
- Runtime API: compatible.
- External API: compatible.
- Web UI: compatible.

## Notes
This is an additive packaging-layer update. It does not modify frozen runtime,
REST, Web UI, workflow, or translation APIs.

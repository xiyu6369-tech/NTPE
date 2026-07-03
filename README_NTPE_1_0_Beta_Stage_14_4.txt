NTPE 1.0 Beta — Stage-14.4 Distribution Package

Scope
-----
Stage-14.4 adds the distribution package planning layer for NTPE release artifacts.
It is additive only and does not modify frozen Runtime, REST API, Web UI, Workflow,
Integration, CLI, SDK, Platform Services, or Foundation APIs.

Added
-----
- packaging/distribution_package.py
- packaging/distribution_builder.py
- tests/beta_stage_14_4/launcher_distribution_package_test.py
- Distribution_Package_Stage_14_4.json
- Release validation report
- Translation validation report

Distribution Kinds
------------------
- full
- increment
- portable
- wheel
- source
- release_bundle

Validation
----------
Stage-14.4 Distribution Package: PASS
Translation Validation Stage-14.4: PASS
Release Validation Stage-14.4: PASS
Stage-14.3 Build Profiles: PASS

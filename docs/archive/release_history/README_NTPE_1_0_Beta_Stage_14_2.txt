NTPE 1.0 Beta — Stage-14.2 Release Manifest
============================================

Stage-14.2 adds the Release Manifest layer for NTPE Beta packaging.

Purpose
-------
- Define a release manifest schema.
- List frozen and active components.
- List runtime, internal, and release dependencies.
- Register release artifacts.
- Preserve compatibility with Foundation, CLI, SDK, Integration, Workflow,
  Platform Services, Runtime API, External API, and Web UI.

New Modules
-----------
packaging/manifest_schema.py
packaging/component_manifest.py
packaging/dependency_manifest.py
packaging/release_manifest.py

Generated Manifest
------------------
release/manifests/Release_Manifest_Stage_14_2.json

Compatibility
-------------
Additive-only update. No frozen API is modified.

Tests
-----
python tests/beta_stage_14_2/launcher_release_manifest_test.py
python tests/beta_stage_14_2/compatibility_test.py

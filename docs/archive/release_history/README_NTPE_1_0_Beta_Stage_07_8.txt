NTPE 1.0 Beta — Stage-07.8 SDK Documentation & Packaging

Status: PASS

Stage-07.8 completes the SDK track by adding package metadata, typed package marker, documentation, examples, and packaging validation.

Added:
- sdk/version.py
- sdk/metadata.py
- sdk/__about__.py
- sdk/py.typed
- docs/sdk/*.md
- examples/sdk_*.py
- packaging/pyproject.toml
- packaging/MANIFEST.in
- packaging/wheel_build.py
- tests/beta_stage_07_8/launcher_sdk_packaging_test.py

Compatibility:
- Foundation v1.0 Frozen: preserved
- CLI Freeze: preserved
- Stage-07.0 through Stage-07.7 SDK APIs: preserved

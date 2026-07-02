NTPE 1.0 Beta — Stage-07.0 SDK Core
====================================

Status: Completed
Compatibility: Foundation v1.0 Frozen compatible; Stage-06.9 CLI Freeze compatible
Update type: Additive / incremental

Added:
- sdk/__init__.py
- sdk/contracts.py
- sdk/client.py
- sdk/manifest.py
- tests/beta_stage_07_0/launcher_sdk_core_test.py

Purpose:
Stage-07.0 introduces the public Python SDK core surface for external application integration.
It exposes stable request/result objects, a client facade, manifest export, translation engine bridging,
and provider manager injection while preserving existing Foundation, runtime, provider, quality, benchmark,
and CLI contracts.

Public API:
- NTPEClient
- SDKRequest
- SDKResult
- build_sdk_manifest
- attach_sdk_manifest

Validation:
python tests\beta_stage_07_0\launcher_sdk_core_test.py

Expected result:
PASS

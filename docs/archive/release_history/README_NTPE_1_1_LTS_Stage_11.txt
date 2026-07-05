NTPE 1.1 LTS Stage-11：LTS Runtime Freeze / Validation

Purpose:
  Freeze and validate the NTPE 1.1 LTS runtime layer after Stage-01 through Stage-10.

Command:
  python ntpe_lts_runtime_freeze.py

Outputs:
  lts_runtime_freeze/LTS_Runtime_Freeze_Manifest_1_1.json
  lts_runtime_freeze/LTS_Runtime_Freeze_Hash_1_1.json
  lts_runtime_freeze/LTS_Runtime_Freeze_Report_1_1.md

Compatibility:
  This stage is additive and does not modify Foundation, CLI, SDK, Runtime API, External REST API, Web UI, or Packaging frozen layers.

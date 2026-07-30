# NTPE 1.1 LTS RC-01 Regression Validation Report

- Version: 1.1-lts-rc-01
- Status: pass
- Validation: pass
- Recommended Tag: `v1.1.0-lts-rc-01-regression`
- Regression Checks: 6
- Failure Count: 0

## Regression Gate

| Check | Status |
|---|---|
| `stable_release_complete_marker` | PASS |
| `lts_runtime_freeze_validation` | PASS |
| `lts_release_candidate_validation` | PASS |
| `frozen_runtime_files_present` | PASS |
| `stage_report_chain_present` | PASS |
| `rc_artifact_chain_present` | PASS |

## Validation Scope

- Confirms NTPE 1.0 Stable completion artifacts are present.
- Revalidates Stage-11 frozen LTS runtime inputs.
- Revalidates Stage-12 release-candidate artifacts.
- Records runtime, stage report, and RC artifact hashes for repeatable RC validation.
- Does not modify Foundation v1.0, CLI, SDK, Runtime API, REST API, Web UI, or frozen LTS runtime behavior.

## Compatibility Policy

- ntpe_1_0_stable: preserved
- foundation_v1_0: frozen
- cli: frozen
- sdk: frozen
- runtime_api: frozen
- external_rest_api: frozen
- web_ui: frozen
- lts_runtime: frozen_by_stage_11
- rc_01_change_type: regression_validation_metadata_only

Manifest SHA256: `5ad5746bc24aef47d1607cec515a627df173a63997c0ac5de31e46cf4576e6d3`

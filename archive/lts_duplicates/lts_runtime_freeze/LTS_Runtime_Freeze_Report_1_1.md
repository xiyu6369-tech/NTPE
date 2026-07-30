# NTPE 1.1 LTS Stage-11 Runtime Freeze / Validation Report

- Version: 1.1-lts-stage-11
- Status: frozen
- Validation: pass
- Runtime Files: 8
- Stage Reports: 11
- Missing Count: 0

## Frozen Runtime Files

| Path | SHA256 | Size |
|---|---|---:|
| `ntpe_translate_txt.py` | `6f55d88afbd6687211e2aff977e623dd838d2b7776b0b30dc263f063dcd4b2f9` | 386 |
| `ntpe_translate_batch.py` | `725033d3e89b66d634b0b6114fd233799aff65136f5ced55e7aab35ffdee6c2b` | 363 |
| `ntpe_batch_monitor.py` | `d3967e04ba782562692dbe02588781cd56049cdd6454625f633b14457b09f6cf` | 341 |
| `ntpe_long_run_recovery.py` | `24626ed096a7862913f886b65f9f890f6570e78a68974ac0f776e88365ddadcf` | 335 |
| `lts/txt_translation_runtime.py` | `90538c610e9504f6e116e3a59ec30c3c7ea8aac584cb1e9a9a38b0a31d93954e` | 32707 |
| `lts/batch_translation_runtime.py` | `762af137db1d5f2ab28d40f6834727ad062caee4888ed381e5c00435d830895d` | 27591 |
| `lts/batch_runtime_monitor.py` | `4a5e5b9749a03edb39b3823f78ede7cfd3dd0a88e57d934d4f50d5b262bd46eb` | 11023 |
| `lts/long_run_recovery.py` | `3344463809f41249ea91fcc08d228c648cb00a981e93a82584d12ed3cf10d75b` | 11565 |

## Compatibility

- foundation_v1_0: frozen
- cli: frozen
- sdk: frozen
- integration: frozen
- workflow: frozen
- platform_services: frozen
- runtime_api: frozen
- external_rest_api: frozen
- web_ui: frozen
- packaging_release: frozen
- stable_1_0: preserved
- lts_1_1: incremental_additive

## Validation Scope

- Stable release regression preserved
- LTS Stage-01 through Stage-10 preserved
- Clean Project Tool preserved
- Runtime freeze manifest and hashes generated

Manifest SHA256: `5b1f352496692b764012b442efb018e786bea3c80f4f4f601103025529fe2b59`

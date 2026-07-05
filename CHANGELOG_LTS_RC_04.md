# NTPE 1.1 LTS RC-04 — Translation Quality / QA Validation

新增 LTS RC-04 Translation Quality / QA Validation 驗證層。

## Added

- `ntpe_lts_rc_quality.py`
- `lts/quality_validation.py`
- `tests/lts_rc_04/`
- `lts_rc_quality/` release candidate QA manifest/hash/report generation

## Validation

- Korean residue detector gate
- Length ratio gate
- Repeated line detector gate
- Taiwan Traditional output formatter gate
- RC-03 artifact chain validation
- Stable + LTS + RC regression compatibility preserved

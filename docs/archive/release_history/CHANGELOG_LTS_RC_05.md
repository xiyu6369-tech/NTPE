# NTPE 1.1 LTS RC-05 - Release Candidate Final Validation

## Added
- Added `ntpe_lts_rc_final_validation.py` final release candidate gate.
- Added `lts/final_validation.py` to aggregate RC-01 regression, RC-02 compatibility, RC-03 performance, and RC-04 quality validation.
- Added final manifest, hash, and markdown report generation.
- Added RC-05 regression tests and launcher smoke test.

## Compatibility
- NTPE 1.0 Stable compatibility preserved.
- Foundation, CLI, SDK, Runtime API, External REST API, and Web UI remain frozen.
- No external API calls are performed by RC-05 validation.

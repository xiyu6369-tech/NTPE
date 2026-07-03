# NTPE 1.1 LTS Stage-04 — Translation QA / Korean Residue Check

## Added
- Added TXT translation QA checks for Korean residue, empty/short output, and repeated lines.
- Added CLI QA controls: `--no-qa`, `--qa-fail-policy`, `--min-length-ratio`, `--max-korean-chars`, and `--max-repeated-lines`.
- Added QA metadata to chunk resume state and translation manifest.
- Added QA retry/warn/fail behavior without breaking Stage-01/02/03 parameters.

## Compatibility
- Foundation v1.0, CLI freeze, SDK, Integration, Workflow, Platform Services, Runtime API, REST API, Web UI, Packaging, RC, and Stable layers remain unchanged.
- Existing Stage-01/02/03 TXT commands remain compatible.

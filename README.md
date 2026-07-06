# NTPE — Novel Translation Professional Engine

NTPE is a professional Korean novel translation engine focused on stable long-form translation, terminology consistency, workflow automation, quality validation, and enterprise deployment.

## Current Release Line

- NTPE 1.0 Stable: Frozen
- NTPE 1.1 LTS Stable: Frozen
- NTPE 1.2 Professional: Active development

## Quick Start

```bat
python launcher.py
python ntpe_validate.py
```

## Documentation

All long-form documentation is organized under `docs/`.

- Architecture: `docs/architecture/`
- Developer Guide: `docs/developer/`
- API Notes: `docs/api/`
- Enterprise Deployment: `docs/enterprise/`
- Release Notes: `docs/release/`
- Roadmap: `docs/roadmap/`
- Freeze Records: `docs/freeze/`
- Stage Documents: `docs/stages/`

## Validation

```bat
python ntpe_stage18_6_documentation_center_test.py
python tests\integration\launcher_stage18_6_documentation_center_test.py
python tests\smoke\launcher_stage18_6_documentation_center_smoke_test.py
python ntpe_validate.py
```

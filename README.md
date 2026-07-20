# NTPE — Novel Translation Professional Engine

NTPE is a professional Korean novel translation engine focused on stable long-form translation, terminology consistency, workflow automation, quality validation, and enterprise deployment.

## Current Release Line

- NTPE 1.0 Stable: Frozen
- NTPE 1.1 LTS Stable: Frozen
- NTPE 1.2 Professional: Active development

## Quick Start

- 一般翻譯：`launcher_translate.py`
- 正式驗證：`ntpe_validate.py`
- 歷史 Root Wrappers：本階段保留於根目錄

```bat
python launcher_translate.py --help
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
- Project Layout: `docs/PROJECT_LAYOUT.md`

## Validation

```bat
python ntpe_stage18_6_documentation_center_test.py
python tests\integration\launcher_stage18_6_documentation_center_test.py
python tests\smoke\launcher_stage18_6_documentation_center_smoke_test.py
python ntpe_validate.py
```

## Production Translation Entry

```bat
set NVIDIA_API_KEY=your_key
python launcher_translate.py batch input output
```

For one TXT file:

```bat
python launcher_translate.py txt input\novel.txt output
```

Check environment:

```bat
python launcher_translate.py doctor
```


## PS-04.1 Regression Timeout & Encoding Hotfix

- Added regression CLI timeout options.
- Added `golden` / `smoke` / `regression` aliases.
- Replaced mojibake-prone timeout guidance with ASCII-safe text.


### TER-v1.8 Character Tone + API Stability

Adds Ilay tone guard and adaptive short-chunk first-attempt timeout.

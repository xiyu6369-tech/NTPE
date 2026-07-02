# NTPE 1.0 Beta — Stage-06.8 CLI Packaging

Stage-06.8 adds the CLI packaging layer for NTPE.

## Capabilities

- CLI entrypoint metadata: `ntpe = cli.main:main`
- Version payload generation
- Distribution metadata
- Release manifest builder
- Install verification
- CLI packaging manifest

## Test

```bat
cd /d D:\Python\NTPE
python tests\beta_stage_06_8\launcher_cli_packaging_test.py
```

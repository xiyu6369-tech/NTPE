# NTPE 1.1 LTS - Clean Project Tool

## Added
- Safe release cleaner at `tools/clean_project.py`.
- Cleaner README at `tools/README_Clean_Project.txt`.
- Preserves source code, docs, tests, config, release metadata, and frozen modules.
- Cleans runtime folders while keeping folder structure via `.gitkeep`.
- Removes runtime state files such as resume/progress/checkpoint/lock/pid/tmp files.
- Removes Python cache folders such as `__pycache__` and `.pytest_cache`.

## Compatibility
- No changes to Foundation, CLI, SDK, Runtime API, External REST API, Web UI, Stable Release, or existing TXT translation CLI parameters.

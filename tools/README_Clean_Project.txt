NTPE 1.1 LTS Utility - Clean Project Tool
=========================================

Purpose:
Clean runtime artifacts before generating release ZIP files while preserving the NTPE project structure and all source code.

Command:
python tools\clean_project.py --yes

Dry run:
python tools\clean_project.py --dry-run

Cleaned folders:
- input
- output
- translated
- final_output
- translation_cache
- cache
- tmp
- logs
- sessions
- failed_chunks
- .ntpe_runtime_checkpoints

Behavior:
- Keeps folders in place.
- Adds .gitkeep when a folder becomes empty.
- Removes runtime state files such as resume*.json, translate_progress*.json, checkpoint*.json, *.lock, *.pid, and *.tmp.
- Preserves source code, tests, docs, config, README, CHANGELOG, release manifests, Git files, and frozen modules.

Also removes Python cache folders such as __pycache__ and .pytest_cache.

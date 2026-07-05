NTPE 1.1 LTS - Clean Project Tool
=================================

This utility adds a safe release-cleaning workflow for NTPE Full ZIP generation.
It removes runtime artifacts and translation outputs while preserving project compatibility and frozen modules.

Command:
python tools\clean_project.py --yes

Use before release packaging to avoid distributing local test inputs, outputs, cache, sessions, checkpoints, logs, or resume files.

Also removes Python cache folders such as __pycache__ and .pytest_cache.

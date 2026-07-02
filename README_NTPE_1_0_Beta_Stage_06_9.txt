NTPE 1.0 Beta — Stage-06.9 CLI Freeze
======================================

This stage freezes NTPE CLI v1 as a stable public interface.
It adds compatibility checks, a CLI v1 baseline, regression tests,
acceptance checks, and CLI documentation.

Test:
  python tests\beta_stage_06_9\launcher_cli_freeze_test.py

Commit:
  git add .
  git commit -m "freeze(cli): cli v1 stable"
  git push origin main

Tag:
  git tag beta-1.0-cli
  git push origin beta-1.0-cli

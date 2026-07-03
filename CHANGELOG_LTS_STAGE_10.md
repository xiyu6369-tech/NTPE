# NTPE 1.1 LTS Stage-10 Changelog

## Long-Run Stability / Auto Recovery

- Added long-run heartbeat metadata support for batch translation runs.
- Added stale resume-state detection for interrupted long-running translation jobs.
- Added recovery plan generator for failed manifests, stale resumes, and stale heartbeat states.
- Added `ntpe_long_run_recovery.py` monitor entry.
- Added optional batch flags: `--heartbeat`, `--heartbeat-seconds`, `--stale-after-seconds`, and `--auto-recovery`.
- Preserved Stage-01 through Stage-09 backward compatibility; heartbeat is opt-in for batch runs.

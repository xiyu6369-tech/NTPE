# NTPE 1.1 LTS RC-03 Performance / Long-Run Validation Report

- Version: 1.1-lts-rc-03
- Status: pass
- Validation: pass
- Recommended Tag: `v1.1.0-lts-rc-03-performance`
- Performance Checks: 8
- Failure Count: 0
- External API Calls: 0

## Performance Gate

| Check | Status |
|---|---|
| `rc02_compatibility_validation_passes` | PASS |
| `rc02_artifact_chain_present` | PASS |
| `long_run_recovery_validation_passes` | PASS |
| `performance_files_present` | PASS |
| `batch_runtime_supports_resume` | PASS |
| `batch_runtime_supports_failure_recovery` | PASS |
| `batch_runtime_supports_heartbeat` | PASS |
| `monitor_runtime_present` | PASS |

## Static Timing Probe

- Sample Files: 120
- Sample Chunks: 9320
- Elapsed ms: 0.36
- Status: pass

## Long-Run Validation Scope

- Confirms RC-02 compatibility validation remains passable.
- Confirms Stage-10 long-run recovery validation remains passable.
- Confirms batch resume, failure recovery, heartbeat, and runtime monitor entry points remain available.
- Performs no external API calls and does not modify frozen NTPE 1.0 or LTS runtime behavior.

Manifest SHA256: `57f7ec5743396b893c1ac97730c9b74e7d9b728eb79fa5d5b19e8b2c2d8eda7e`

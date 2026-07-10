# TE v5.2.3 Provider Backpressure and Regression Resume

## Scope

- Enforce a process-wide NVIDIA request ceiling of at most 40 RPM.
- Smooth request starts instead of allowing independent client bursts.
- Apply dedicated 503/capacity backpressure delays: 60, 120, 180 seconds.
- Enable literary regression chunk resume by default.
- Preserve `--overwrite` as the explicit fresh-run operation.
- Add `--no-resume` for diagnostic runs.

## Configuration

```bat
set NTPE_NVIDIA_RPM_LIMIT=40
set NTPE_CAPACITY_RETRY_DELAYS=60,120,180
```

The RPM value is hard-capped at 40. Lower values are accepted.

## Resume workflow

First clean run:

```bat
python launcher_translate.py regression --set golden --stage TE-v5.2.3-ProviderBackpressureResume --profile literary --chunk-size 600 --api-timeout 180 --provider-attempts 4 --overwrite
```

After a provider failure, run the same command without `--overwrite`. Completed chunks and resume state are retained.

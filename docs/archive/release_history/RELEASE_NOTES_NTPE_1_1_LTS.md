# NTPE 1.1 LTS Release Notes

NTPE 1.1 LTS is the long-term support release line built on top of NTPE 1.0 Stable.

## Release Status

- Version: 1.1-lts-stable-finalization
- Status: pass
- Recommended Tag: `v1.1.0-lts-stable-finalization`
- Release Target: NTPE 1.1 LTS Stable
- Backward Compatibility: preserved
- Feature Changes After RC Freeze: False

## LTS Runtime Highlights

- TXT novel translation entry.
- Resume and retry handling for long translation runs.
- Glossary and character memory reinforcement.
- Translation QA with Korean residue checks.
- Taiwan Traditional Chinese normalization and output formatter.
- Batch folder translation, progress summary, failure recovery, runtime monitor, and auto recovery.
- RC regression, compatibility, performance, and quality validation gates.

## Packaging Policy

- Full ZIP is produced after Clean Project Tool removes runtime data.
- Increment ZIP contains only finalization-stage additions.
- No external API calls are required for release validation.

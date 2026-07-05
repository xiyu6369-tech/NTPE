# NTPE 1.1 LTS Stable Release Complete

NTPE 1.1 LTS is complete and ready to be tagged as the long-term support stable release.

## Release Summary

- Version: 1.1-lts-stable-complete
- Status: pass
- Recommended Tag: `v1.1.0-lts-stable`
- Release Line: NTPE 1.1 LTS
- Backward Compatibility: preserved
- Feature Changes After Finalization: False

## Included LTS Capabilities

- TXT novel translation entry.
- Batch folder translation.
- Resume, retry, failure recovery, and continue mode.
- Glossary, character memory, QA, Korean residue checks, and Taiwan Traditional Chinese normalization.
- Batch progress, summary reports, runtime monitor, heartbeat, and auto recovery.
- LTS runtime freeze, RC validation, stable preparation, and stable finalization gates.

## Packaging

- Full ZIP must be generated after Clean Project Tool removes runtime artifacts.
- Increment ZIP contains only Stable Complete additions.
- No external API calls are performed during release validation.

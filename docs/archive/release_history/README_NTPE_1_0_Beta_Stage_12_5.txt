NTPE 1.0 Beta — Stage-12.5 REST Event API

Status: PASS

This stage adds an additive REST Event API adapter over the frozen Runtime Event
API. The external API layer remains decoupled from lower runtime internals.

Added:
- external_api/rest_event.py
- tests/beta_stage_12_5/
- CHANGELOG_Stage_12_5.md
- Translation_Validation_Report_Stage_12_5.md

Compatibility:
- Foundation v1.0 Frozen: PASS
- CLI Frozen: PASS
- Integration Frozen: PASS
- Workflow Frozen: PASS
- Platform Services Frozen: PASS
- Runtime API Frozen: PASS
- REST Core: PASS

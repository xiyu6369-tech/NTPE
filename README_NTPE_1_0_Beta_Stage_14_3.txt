NTPE 1.0 Beta — Stage-14.3 Build Profiles

Status: PASS

Stage-14.3 adds the Build Profiles layer for NTPE release packaging.

Added:
- packaging/build_profile.py
- packaging/build_profiles.py
- tests/beta_stage_14_3/
- release/manifests/Build_Profiles_Stage_14_3.json
- CHANGELOG_Stage_14_3.md
- Translation_Validation_Report_Stage_14_3.md
- Release_Validation_Report_Stage_14_3.md

Profiles:
- development
- beta
- rc
- production

Compatibility:
- Foundation v1.0: Frozen compatible
- CLI: Frozen compatible
- Integration: Frozen compatible
- Workflow: Frozen compatible
- Platform Services: Frozen compatible
- Runtime API: Frozen compatible
- External API: Frozen compatible
- Web UI: Frozen compatible

This stage is additive only and does not modify translation runtime, REST API, Web UI, or frozen interfaces.

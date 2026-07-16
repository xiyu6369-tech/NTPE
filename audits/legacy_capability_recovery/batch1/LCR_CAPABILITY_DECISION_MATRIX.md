# LCR Capability Decision Matrix

Batch 1 is audit/design only. No legacy code is integrated.

| Capability | Decision | Reason |
|---|---|---|
| character_memory | REIMPLEMENT_FROM_CONCEPT | no evidence/confidence/version/expiry governance |
| dynamic_character_extraction | REIMPLEMENT_FROM_CONCEPT | no evidence-bound approved inference pipeline |
| character_voice_memory | MERGE_WITH_CURRENT | needs evidence and prompt eligibility gates |
| previous_translation_context | MERGE_WITH_CURRENT | fixed tail lacks ranking, evidence and semantic boundaries |
| scene_memory | MERGE_WITH_CURRENT | no explicit scene evidence or expiry |
| narrative_memory | MERGE_WITH_CURRENT | not structured or evidence-ranked |
| chunk_splitting | KEEP_CURRENT | Current NTPE already provides the safer tested equivalent; do not restore legacy implementation. |
| chunk_cache | REIMPLEMENT_FROM_CONCEPT | no content-addressed V2 cache metadata |
| resume_recovery | KEEP_CURRENT | Current NTPE already provides the safer tested equivalent; do not restore legacy implementation. |
| realtime_output_assembly | KEEP_CURRENT | Current NTPE already provides the safer tested equivalent; do not restore legacy implementation. |
| glossary_enforcement | KEEP_CURRENT | Current NTPE already provides the safer tested equivalent; do not restore legacy implementation. |
| unknown_name_handling | DROP_UNSAFE | requires language profile and human/evidence governance |
| provider_fallback | EXPERIMENT_ONLY | must remain controlled and observable |
| multi_provider_routing | EXPERIMENT_ONLY | legacy routing bypasses current policy/security |
| dual_model_workflow | REIMPLEMENT_FROM_CONCEPT | no separately observable draft/polish artifacts |
| draft_translation | REIMPLEMENT_FROM_CONCEPT | no draft artifact or draft verification |
| polish_workflow | REIMPLEMENT_FROM_CONCEPT | needs selective gate and post-polish semantic verification |
| semantic_verification | KEEP_CURRENT | Current NTPE already provides the safer tested equivalent; do not restore legacy implementation. |
| quality_retry | KEEP_CURRENT | Current NTPE already provides the safer tested equivalent; do not restore legacy implementation. |
| basic_output_validation | DROP_UNSAFE | length-only QA has no semantic coverage |
| encoding_detection | KEEP_CURRENT | Current NTPE already provides the safer tested equivalent; do not restore legacy implementation. |
| gui_workflow | EXPERIMENT_ONLY | legacy GUI cannot bypass frozen runtime/security |
| batch_processing | KEEP_CURRENT | Current NTPE already provides the safer tested equivalent; do not restore legacy implementation. |
| pause_resume | MERGE_WITH_CURRENT | UI pause should merge only through current runtime contracts |
| configuration_persistence | MERGE_WITH_CURRENT | must explicitly exclude credentials |
| academic_degraded_fallback | DROP_UNSAFE | conflicts with literary quality contract |
| embedded_provider_credentials | LICENSE_OR_SECURITY_BLOCKED | legacy credential pattern is forbidden |

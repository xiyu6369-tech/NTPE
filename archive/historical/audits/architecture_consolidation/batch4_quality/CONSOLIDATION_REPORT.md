# Batch 4 Quality API Consolidation

Batch 4 adds three thin, read-only public domains: quality assessment, quality review, and corpus governance view. The facade delegates validation and integrity semantics to the frozen Stage 11 models and never joins production runtime, Provider, Prompt Builder, retry, timeout, resume, output assembly, or translation execution.

Legacy Stage 11 imports remain available. No frozen artifact, manifest, schema, release document, Golden Corpus file, or SHA anchor is rewritten.

## Boundaries

- Assessment exposes existing defect and metric results without recalculation.
- Review preserves `planned_not_applied`, human-only provenance, and non-applied decisions.
- An accepted review fixture is not interpreted as Golden Corpus approval.
- Corpus `manage` returns a view only and provides no mutation method.
- Provider requests, prompt tokens, disk writes, artifact creation, and runtime stage deltas are zero during facade calls.
- Batch 5 is not started.

## Boundary declaration

```text
production_code_modified = false
runtime_modified = false
provider_modified = false
prompt_modified = false
candidate_modified = false
stage11_modified = false
frozen_schema_modified = false
golden_corpus_modified = false

quality_public_api_created = true
corpus_public_api_created = true
legacy_imports_preserved = true

translation_quality_changed = false
translation_quality_regressed = false
runtime_efficiency_regressed = false

provider_requests_added = 0
prompt_tokens_added = 0
disk_writes_added = 0
runtime_stages_added = 0

provider_executed = false
new_translation_generated = false

tracked_files_deleted = 0
batch5_started = false
```

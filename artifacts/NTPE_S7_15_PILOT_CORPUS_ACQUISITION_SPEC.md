# NTPE S7-15 Pilot Corpus Acquisition Specification

**Dependency**: `PILOT_CORPUS`
**Current status**: SPECIFICATION READY (sources exist; manifest not populated)
**Extends**: `artifacts/s7_14_pilot/PILOT_CORPUS_REQUIREMENTS.md` (KEEP / EXTEND)

---

## Target

- 50 passages — `PILOT_ONLY` (never a formal calibration N).
- Scene-level, chapter-aware sampling.

## Required Coverage (stratification)

dialogue · narration · mixed scene · high terminology density · high character
interaction · different chapter positions · different tone/register.

## Prohibited Selection

Easy/short text only, obvious failures only, developer-selected examples only.
Selection-bias audit required (selected vs population on length/quality proxies).

## Manifest Fields

`sample_id`, `source_id`, `chapter_id`, `scene_id`, `character_arc_ids`, `source_hash`,
`candidate_ids`, `reference_id`, `difficulty_class`, `scene_type`, `selection_stratum`.

## Acceptance

`ACCEPTED` only when the manifest is populated, hashes valid, and stratification
coverage is satisfied. Until then: PARTIAL.

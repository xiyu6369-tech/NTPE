# NTPE S7-14 Pilot Corpus Requirements

**Dependency class**: `PILOT_CORPUS`
**Current status**: PARTIAL — Korean source material exists; selection manifest not populated.

---

## 1. Sampling Properties

- Unit: scene-level passage (multi-paragraph, 500–3000 chars).
- Chapter-aware; stratified.
- Strata: genre × dialogue density × scene type × terminology density (capped ≤24).
- Minimum stratum population ≥20 before sampling; merge adjacent if below.

## 2. Diversity Requirements

- Different chapter, different scene.
- Dialogue-heavy and narration-heavy both present.
- Terminology complexity range (low/medium/high).
- Character interaction coverage.
- Tone/register diversity (formal, casual, archaic, poetic, technical).

## 3. Prohibited Selection

- Not only easy text, short text, obvious failures, or developer-selected examples.
- Selection-bias audit: compare selected vs population on length/quality proxies.

## 4. Size

- Pilot: **50 passages** (`PILOT_ONLY`).
- Formal calibration N is `TBD` pending cluster-aware power analysis (`n_eff`), never N_raw.

## 5. Manifest Schema

Each sample record must carry: `sample_id`, `source_id`, `chapter_id`, `scene_id`,
`character_arc_ids`, `source_hash`, `candidate_ids`, `reference_id`, `difficulty_class`,
`scene_type`, `selection_stratum`.

> If the canonical repository schema uses different names, the canonical implementation
> governs. Current schema provides `author_id`, `chapter_id`, `scene_id`,
> `character_ids[]`, `terminology_group_id`; there is no `character_arc_id` (see H02).

## 6. Cluster Awareness (H02)

- `character_arc_ids` is required by schema but **not currently derivable** (see
  S7-14 H02 status: `EXTERNAL_DEPENDENCY`).
- Until annotations exist, group by chapter + author; record the arc limitation.

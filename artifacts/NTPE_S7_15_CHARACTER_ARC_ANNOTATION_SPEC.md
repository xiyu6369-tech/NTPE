# NTPE S7-15 Character-Arc Annotation Specification

**Dependency**: `CHARACTER_ARC` — `EXTERNAL_DATA_DEPENDENCY` (annotation)
**Current status**: `EXTERNAL_DEPENDENCY` (no `character_arc_id` exists)
**Extends**: S7-14 H02 status (`EXTERNAL_DEPENDENCY`)

S7-15 collects **zero** annotations. It does not auto-generate arc IDs and claim them as
annotation.

---

## Objective

Prevent cross-split leakage. NOT a character database, NOT a character-memory feature.

## Definition (must be fixed before annotation)

> A **character arc** is a bounded span of narrative in which a character's identity,
> relationships, and voice form a continuity unit relevant to translation consistency.
> `same character ≠ same arc`.

A character appearing in multiple narrative arcs may carry **multiple `character_arc_id`s**
(never forced to one).

## Required Annotation Fields

`character_arc_id`, `character_ids`, `chapter_span`, `scene_span`, `arc_start`, `arc_end`,
`confidence`, `annotator_id`, `annotation_version`.

Unreliable fields → `TBD`.

## Annotation Method

Do **not** assume automatic extraction is reliable. Design: human annotation /
double annotation / adjudication. (This task = spec only.)

## Reliability

Independent annotation, disagreement recording, adjudication, versioned output.
Agreement threshold without evidence → `TBD — pilot annotation determines feasibility`.

## Split Integration

Future split uses `character_arc_id` as a leakage-prevention signal. **No split execution
in S7-15.**

## Acceptance (per annotation record)

character IDs resolvable · source span resolvable · arc-label provenance · annotation
version. No provenance → **REJECT**.

---

## Status Semantics

Only reliable, provenance-carrying annotation sets status `ACCEPTED` and closes H02.
Until then: `EXTERNAL_DEPENDENCY`.

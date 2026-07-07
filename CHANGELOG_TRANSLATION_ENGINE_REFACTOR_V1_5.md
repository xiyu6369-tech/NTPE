# Translation Engine Refactoring v1.5 — Literary Polish v2

## Focus

TER-v1.5 keeps the TER-v1.4 speed/prompt-compression gains and improves Chinese novel readability through conservative literary cleanup.

## Changes

- Improved eyebrow/action phrasing: `抬了抬眉毛` -> `挑了挑眉`.
- Improved ambiguous reply phrasing: avoids `只留下了一句模糊的話`.
- Improved worst-case situation phrasing: avoids `事情已經變得最壞了`.
- Added compact prompt mode marker `compact_literary_v6_ter_v1_5`.
- Added TER-v1.5 unit, integration, and smoke tests.

## Compatibility

- No changes to Foundation v1.0 or NTPE 1.1 LTS frozen layers.
- Keeps TER-v1.4 prompt compression strategy.
- No new external dependencies.

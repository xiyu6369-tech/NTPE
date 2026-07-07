# NTPE 1.2 Translation Engine Refactoring v1.7

## Narrative Naturalness

TER-v1.7 focuses on the remaining Smoke_Set narrative wording issues after
TER-v1.6.

### Improvements

- Smooths `想要轉身離開` into `正要轉身離去` for imminent action.
- Smooths `轉頭看向鄭泰義` into `轉頭看了過來` when the viewpoint remains with 鄭泰義.
- Smooths `心情沉重地瞪了伊萊` into `神情沉重地瞪著他看了一會兒`.
- Smooths the fatigue line into `彷彿積壓了數十年的疲憊一口氣湧了上來`.

### Compatibility

- Does not change TER-v1.6 prompt compression, Name Lock, or QA behavior.
- Adds only conservative literary normalization rules.

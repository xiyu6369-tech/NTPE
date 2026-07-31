# RM-5.3 Canary Activation Guide

> **Stage**: RM-5.3 — Runtime Context Integration (Documentation Addendum)  
> **Status**: ✅ ACTIVE  
> **Policy**: Default-Off / Canary Rollout  

---

## 1. Purpose

### 1.1 Why Default-Off?
TQI V72 (Translation Quality Integration) introduces high-impact context layers, including Character Memory V2 and Scene Memory. To prevent unexpected prompt shifts in production and ensure absolute stability, the system is designed as **Default-Off**.

### 1.2 Why Canary Activation?
Instead of a global rollout, a Canary approach allows:
- **Controlled Testing**: Enabling TQI only for specific chunks or sessions to verify the impact on translation quality.
- **Risk Mitigation**: Isolating potential prompt budget issues or context noise to a small subset of data.
- **Baseline Comparison**: Enabling a side-by-side comparison between the Baseline Prompt and the TQI-enhanced Prompt.

### 1.3 Scope
This guide applies to the `TranslationEngine.translate_package()` runtime path and governs how quality flags in the Prompt Package metadata are interpreted.

---

## 2. Activation Conditions

The TQI V72 Adapter is driven by flags located in the `metadata` section of the Prompt Package JSON.

### 2.1 Metadata Flags

| Flag Name | Default | Activation Condition | Effect |
|-----------|----------|---------------------|--------|
| `quality_integration_v72` | `False` | `True` | Global switch for TQI V72 logic |
| `quality_character_memory_v72` | `False` | `True` | Injects Character Memory V2 facts |
| `quality_context_scene_v72` | `False` | `True` | Injects Scene Memory state |
| `quality_naturalness_v72` | `False` | `True` | Injects Naturalness Policy guardrails |
| `quality_integration_kill_switch_v72` | `False` | `True` | **Overriding OFF**: Force-disables all TQI |

### 2.2 Activation Logic
The adapter activates if `kill_switch` is `False` **AND** (`integration` is `True` **OR** any specific feature flag is `True`).

---

## 3. Activation Flow

The integration occurs at the final stage of prompt assembly within the Production Pipeline:

```text
TranslationEngine.translate_package()
        │
        ▼
apply_prompt_intelligence()   ───► [Quality Directives]
        │
        ▼
apply_context_intelligence()  ───► [Context Directives]
        │
        ▼
tqi_v72_apply_to_prompt_package() ──► [TQI V72 ADAPTER]
        │                             ├─ Character Memory V2 (Facts)
        │                             ├─ Scene Memory (State)
        │                             └─ Naturalness Policy (Anti-patterns)
        ▼
Provider Request (NVIDIA API)
```

---

## 4. Rollback Procedure

Rollback is handled via metadata configuration without requiring code changes.

### 4.1 Immediate Deactivation
To disable TQI for a specific package or session:
1. Set `quality_integration_v72: false` in metadata.
2. Set all specific feature flags (`quality_character_memory_v72`, etc.) to `false`.
3. **OR** set `quality_integration_kill_switch_v72: true`.

### 4.2 System Behavior during Rollback
- **Flow**: The pipeline bypasses the `tqi_v72_apply_to_prompt_package` logic.
- **Provider**: The Provider receives the same prompt as the original baseline.
- **Consistency**: No changes to Provider behavior or API call patterns.

---

## 5. Validation Checklist

After activating Canary flags, the following must be verified:

- [ ] **Character Memory**: Verify `【人物記憶】` (or equivalent) is present in the `user_prompt`.
- [ ] **Scene Memory**: Verify `【場景狀態】` (or equivalent) is present in the `user_prompt`.
- [ ] **Prompt Structure**: Ensure no prompt truncation or structural corruption.
- [ ] **Provider Call Count**: Confirm Provider Request count remains **exactly 1** per chunk.
- [ ] **Runtime Stability**: Confirm translation completes without `TQI V72 degd` errors in logs.
- [ ] **Core Health**: Run `python ntpe_validate.py` $\rightarrow$ **ALL PASS**.
- [ ] **Syntax**: Run `python -m compileall .` $\rightarrow$ **PASS**.

---

## 6. Future Rollout

The transition from Canary to Global rollout follows this roadmap:
1. **RM-5.3 (Current)**: Wiring and Canary Activation Guide (Default-Off).
2. **RM-5.4**: Effectiveness Validation (Measure quality improvement via Canary).
3. **RM-5.5**: Strategic Decision (Determine if TQI should become Default-On based on RM-5.4 data).

**Current Status**: Strictly **Default-Off**.

# RM-5.7.2B Scene Extraction Few-shot Examples

**Purpose**: Scene Extraction Examples  
**Prompt Version**: RM-5.7.2A  
**Schema Version**: scene_schema.json (v1.0)  
**Status**: Design Complete  
**Compatible With**: RM-5.7.3 Validation Engine, RM-5.7.2C Golden Dataset

---

## Few-shot Examples

### Example 1: Scene Start (Explicit Boundary)

**INPUT**

```
第 4 章：晨曦破曉

清晨的第一縷陽光穿過雲層，灑在艾爾迪亞王都的廣場上。鐘樓敲響了六下，標誌著新一天的開始。伊萊站在廣場中央的石台上，四周聚集了數百名等待授勛的騎士。

「各位勇士，」國王的聲音在廣場上迴盪，「今日，帝國授予你們最高榮譽——聖殿騎士團團員資格。」

人群中爆發出雷動的歡呼聲。伊萊感受到陽光溫暖地照在臉上，心中卻泛起一陣從未有過的沉重。
```

**Reasoning**

```
Evidence
Explicit boundary marker: 第 4 章：晨曦破曉 (chapter start)
Explicit time: 清晨, 鐘樓敲響了六下 (dawn/morning)
Explicit location: 艾爾迪亞王都的廣場
Explicit participants: 伊萊, 國王, 數百名騎士
Explicit tone: 莊嚴, 榮譽, 歡呼
Boundary type: chapter_transition
Scene unchanged
```

**Expected JSON**

```json
[
  {
    "entity_id": "770e8400-e29b-41d4-a716-446655440001",
    "entity_type": "scene",
    "schema_version": "1.0",
    "name": "SC-001",
    "attributes": {
      "scene_id": "SC-001",
      "title": "聖殿騎士授勛儀式",
      "volume": 1,
      "chapter_range": "4",
      "location": "艾爾迪亞王都廣場",
      "time_of_day": "morning",
      "participants": [
        {"character_id": "550e8400-e29b-41d4-a716-446655440001", "status": "present", "role": "protagonist"},
        {"character_id": "550e8400-e29b-41d4-a716-446655440003", "status": "present", "role": "monarch"}
      ],
      "plot_points": [],
      "summary": "King bestows Temple Knight honors on hundreds of knights at dawn ceremony",
      "tone": "joyful",
      "unresolved_references": [],
      "boundary_type": "chapter_transition"
    },
    "source_text": "清晨的第一縷陽光穿過雲層，灑在艾爾迪亞王都的廣場上。鐘樓敲響了六下，標誌著新一天的開始。伊萊站在廣場中央的石台上，四周聚集了數百名等待授勛的騎士。\n\n「各位勇士，」國王的聲音在廣場上迴盪，「今日，帝國授予你們最高榮譽——聖殿騎士團團員資格。」\n\n人群中爆發出雷動的歡呼聲。伊萊感受到陽光溫暖地照在臉上，心中卻泛起一陣從未有過的沉重。",
    "source_location": "vol1:ch4:1-12",
    "confidence": 0.92,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "pending"
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["scene_start", "chapter_transition", "ceremony"]
  }
]
```

**Confidence**: 0.92  
**Why**: Explicit chapter boundary, time, location, participants, and tone markers provide full direct evidence.
# RM-5.7.2B Character Extraction Few-shot Examples

**Purpose**: Character Extraction Examples  
**Prompt Version**: RM-5.7.2A  
**Schema Version**: character_schema.json (v1.0)  
**Status**: Design Complete  
**Compatible With**: RM-5.7.3 Validation Engine, RM-5.7.2C Golden Dataset

---

## Few-shot Examples

### Example 1: Character First Appearance (Explicit Introduction)

**INPUT**

```
第 1 章：風起雲湧

伊萊·沃倫站在古老城堡的最高塔樓上，望著遠方翻滾的烏雲。作為艾爾迪亞王國最年輕的大劍師，他感受到肩上的責任前所未有的沉重。他的銀色長髮在風中飛揚，雙眼如同深邃的湖水般平靜。

「少主，陛下召見。」身後傳來管家塞巴斯汀恭敬的聲音。

伊萊轉身，嘴角勾起一抹淡淡的微笑：「走吧，塞巴斯汀。我不想讓父王久等。」
```

**Reasoning**

```
Evidence
Explicit canonical name: 伊萊·沃倫
Explicit title/role: 艾爾迪亞王國最年輕的大劍師, 少主
Explicit physical traits: 銀色長髮, 雙眼如同深邃的湖水
Explicit relationship: 塞巴斯汀 (管家), 父王 (國王)
Speaker identified: 伊萊, 塞巴斯汀
```

**Expected JSON**

```json
[
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440001",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "伊萊·沃倫",
    "attributes": {
      "canonical_name": "伊萊·沃倫",
      "source_name": "伊萊·沃倫",
      "aliases": ["少主", "伊萊"],
      "role": "protagonist",
      "traits": ["冷靜", "負責感強", "銀髮", "湖水般雙眼"],
      "relationships": {
        "550e8400-e29b-41d4-a716-446655440002": "butler",
        "550e8400-e29b-41d4-a716-446655440003": "father"
      },
      "cultivation_realm": "大劍師",
      "first_appearance": "第 1 章",
      "knowledge_tags": ["royalty", "swordsman", "noble"],
      "arc_summary": null
    },
    "source_text": "伊萊·沃倫站在古老城堡的最高塔樓上，望著遠方翻滾的烏雲。作為艾爾迪亞王國最年輕的大劍師，他感受到肩上的責任前所未有的沉重。他的銀色長髮在風中飛揚，雙眼如同深邃的湖水般平靜。\n\n\u0022少主，陛下召見。\u0022身後傳來管家塞巴斯汀恭敬的聲音。\n\n伊萊轉身，嘴角勾起一抹淡淡的微笑：\u0022走吧，塞巴斯汀。我不想讓父王久等。\u0022",
    "source_location": "vol1:ch1:1-15",
    "confidence": 0.95,
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
    "tags": ["first_appearance", "explicit_introduction"]
  },
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440002",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "塞巴斯汀",
    "attributes": {
      "canonical_name": "塞巴斯汀",
      "source_name": "塞巴斯汀",
      "aliases": ["管家"],
      "role": "supporting",
      "traits": ["恭敬", "忠誠"],
      "relationships": {
        "550e8400-e29b-41d4-a716-446655440001": "master"
      },
      "cultivation_realm": null,
      "first_appearance": "第 1 章",
      "knowledge_tags": ["servant", "butler"],
      "arc_summary": null
    },
    "source_text": "\u0022少主，陛下召見。\u0022身後傳來管家塞巴斯汀恭敬的聲音。",
    "source_location": "vol1:ch1:8-10",
    "confidence": 0.85,
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
    "tags": ["first_appearance", "supporting_character"]
  },
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440003",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "國王 (父王)",
    "attributes": {
      "canonical_name": "國王",
      "source_name": "父王",
      "aliases": ["陛下", "艾爾迪亞國王"],
      "role": "supporting",
      "traits": [],
      "relationships": {
        "550e8400-e29b-41d4-a716-446655440001": "son"
      },
      "cultivation_realm": null,
      "first_appearance": "第 1 章",
      "knowledge_tags": ["royalty", "father"],
      "arc_summary": null
    },
    "source_text": "\u0022少主，陛下召見。\u0022...\u0022走吧，塞巴斯汀。我不想讓父王久等。\u0022",
    "source_location": "vol1:ch1:8-14",
    "confidence": 0.7,
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
    "tags": ["first_appearance", "referenced_only"]
  }
]
```

**Confidence**: 0.95 (primary), 0.85 (supporting), 0.7 (referenced)  
**Why**: Explicit canonical name, title, physical traits, and relationships provide full direct evidence for protagonist; supporting characters have clear role indicators.

---

### Example 2: Character Referenced by Pronoun/Descriptor Only

**INPUT**

```
第 3 章：暗流湧動

那男人站在陰影中，緊握著手中的情報報告。他沒有想到，原本完美的計劃竟然會在最後關頭出現變數。那雙深邃的眼睛閃爍著危險的光芒——這次，他必須親自出手了。

「大人，屬下已經安排妥當。」一個黑衣人單膝跪地，聲音低沉。

他微微颔首，嘴角勾起一抹冰冷的弧度：「很好。讓那些自以為是的貴族們看看，什麼叫做真正的權力。」
```

**Reasoning**

```
Evidence
Pronoun reference only: 那男人, 他, 那雙深邃的眼睛
No canonical name provided
Explicit role indicators: 大人 (honorific), 計劃者, 決策者
Explicit traits: 冷酷, 危險, 權力慾強
Speaker identified: 那男人, 黑衣人
Relationship inferred: 黑衣人 -> 那男人 (subordinate)
Scene unchanged
```

**Expected JSON**

```json
[
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440004",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "未知男性 (陰影中的策劃者)",
    "attributes": {
      "canonical_name": "未知男性",
      "source_name": "那男人",
      "aliases": ["那男人", "大人", "策劃者"],
      "role": "antagonist",
      "traits": ["冷酷", "危險", "權力慾強", "深謀遠慮"],
      "relationships": {
        "550e8400-e29b-41d4-a716-446655440005": "subordinate"
      },
      "cultivation_realm": null,
      "first_appearance": "第 3 章",
      "knowledge_tags": ["shadowy_figure", "mastermind", "unnamed"],
      "arc_summary": null
    },
    "source_text": "那男人站在陰影中，緊握著手中的情報報告。他沒有想到，原本完美的計劃竟然會在最後關頭出現變數。那雙深邃的眼睛閃爍著危險的光芒——這次，他必須親自出手了。\n\n\u0022大人，屬下已經安排妥當。\u0022一個黑衣人單膝跪地，聲音低沉。\n\n他微微颔首，嘴角勾起一抹冰冷的弧度：\u0022很好。讓那些自以為是的貴族們看看，什麼叫做真正的權力。\u0022",
    "source_location": "vol1:ch3:1-12",
    "confidence": 0.4,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "needs_review"
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["pronoun_only", "unnamed", "antagonist", "low_confidence"]
  },
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440005",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "黑衣人",
    "attributes": {
      "canonical_name": "黑衣人",
      "source_name": "黑衣人",
      "aliases": ["屬下", "黑衣人"],
      "role": "minor",
      "traits": ["忠誠", "低調"],
      "relationships": {
        "550e8400-e29b-41d4-a716-446655440004": "superior"
      },
      "cultivation_realm": null,
      "first_appearance": "第 3 章",
      "knowledge_tags": ["henchman", "unnamed"],
      "arc_summary": null
    },
    "source_text": "\u0022大人，屬下已經安排妥當。\u0022一個黑衣人單膝跪地，聲音低沉。",
    "source_location": "vol1:ch3:7-9",
    "confidence": 0.45,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "needs_review"
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["pronoun_only", "unnamed", "minor", "low_confidence"]
  }
]
```

**Confidence**: 0.4 (primary), 0.45 (minor)  
**Why**: Only pronouns/descriptors used, no canonical name. Flagged for review per confidence rules (pronoun-only reference = 0.3-0.49).

---

### Example 3: Character with Multiple Aliases (Merge Required)

**INPUT**

```
第 7 章：舊識重逢

「伊萊！」一道熟悉的聲音從人群中傳來。伊萊·沃倫轉頭，看見一個身穿旅行斗篷的青年正向他揮手。

「賽恩？」伊萊驚訝地眨了眨眼，「你怎麼會在這裡？」

青年推開帽兜，露出一頭火紅的短髮和滿臉雀斑，笑容燦爛得像陽光：「當然是來找你啊，老夥計。或者我該叫你『銀閃』？畢竟現在全王國都知道艾爾迪亞的年輕大劍師伊萊·沃倫了。」

伊萊無奈地搖搖頭，嘴角卻不自覺地上揚：「別鬧了，賽恩·克勞斯。既然叫上綽號，那我也該稱呼你為『烈焰劍豪』才對。」

「哈！還記得這個稱號啊。」賽恩·克勞斯大笑，一把摟住伊萊的肩膀，「走，找個地方好好敘敘。我有很多事想問你——關於『那個組織』，還有... 你妹妹艾琳的事。」
```

**Reasoning**

```
Evidence
Explicit canonical names: 伊萊·沃倫, 賽恩·克勞斯
Explicit aliases: 銀閃 (伊萊), 烈焰劍豪 (賽恩), 老夥計 (相互)
Explicit relationship: 老友, 舊識
Explicit referenced character: 艾琳 (妹妹, not present)
Speaker identified: 伊萊, 賽恩
Relationship inferred: 伊萊 <-> 賽恩 (friends), 伊萊 -> 艾琳 (brother)
Term repeated: 組織 (referenced)
Scene unchanged
```

**Expected JSON**

```json
[
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440001",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "伊萊·沃倫",
    "attributes": {
      "canonical_name": "伊萊·沃倫",
      "source_name": "伊萊·沃倫",
      "aliases": ["少主", "伊萊", "銀閃", "年輕大劍師"],
      "role": "protagonist",
      "traits": ["冷靜", "負責感強", "銀髮", "湖水般雙眼", "重情義"],
      "relationships": {
        "550e8400-e29b-41d4-a716-446655440002": "butler",
        "550e8400-e29b-41d4-a716-446655440003": "father",
        "550e8400-e29b-41d4-a716-446655440006": "friend",
        "550e8400-e29b-41d4-a716-446655440007": "brother"
      },
      "cultivation_realm": "大劍師",
      "first_appearance": "第 1 章",
      "knowledge_tags": ["royalty", "swordsman", "noble", "alias:銀閃"],
      "arc_summary": null
    },
    "source_text": "\u0022伊萊！\u0022一道熟悉的聲音從人群中傳來。伊萊·沃倫轉頭，看見一個身穿旅行斗篷的青年正向他揮手。\n\n\u0022賽恩？\u0022伊萊驚訝地眨了眨眼，\u0022你怎麼會在這裡？\u0022\n\n青年推開帽兜，露出一頭火紅的短髮和滿臉雀斑，笑容燦爛得像陽光：\u0022當然是來找你啊，老夥計。或者我該叫你『銀閃』？畢竟現在全王國都知道艾爾迪亞的年輕大劍師伊萊·沃倫了。\u0022\n\n伊萊無奈地搖搖頭，嘴角卻不自覺地上揚：\u0022別鬧了，賽恩·克勞斯。既然叫上綽號，那我也該稱呼你為『烈焰劍豪』才對。\u0022\n\n\u0022哈！還記得這個稱號啊。\u0022賽恩·克勞斯大笑，一把摟住伊萊的肩膀，\u0022走，找個地方好好敘敘。我有很多事想問你——關於『那個組織』，還有... 你妹妹艾琳的事。\u0022",
    "source_location": "vol1:ch7:1-20",
    "confidence": 0.95,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "approved"
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 2,
    "references": {},
    "tags": ["alias_merge", "cross_chapter_reference", "updated"]
  },
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440006",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "賽恩·克勞斯",
    "attributes": {
      "canonical_name": "賽恩·克勞斯",
      "source_name": "賽恩·克勞斯",
      "aliases": ["賽恩", "老夥計", "烈焰劍豪", "火紅短髮青年"],
      "role": "supporting",
      "traits": ["熱情", "豪爽", "火紅短髮", "滿臉雀斑", "舊友"],
      "relationships": {
        "550e8400-e29b-41d4-a716-446655440001": "friend"
      },
      "cultivation_realm": "劍豪",
      "first_appearance": "第 7 章",
      "knowledge_tags": ["swordsman", "wanderer", "alias:烈焰劍豪", "old_friend"],
      "arc_summary": null
    },
    "source_text": "\u0022伊萊！\u0022一道熟悉的聲音從人群中傳來。...\u0022哈！還記得這個稱號啊。\u0022賽恩·克勞斯大笑，一把摟住伊萊的肩膀，\u0022走，找個地方好好敘敘。我有很多事想問你——關於『那個組織』，還有... 你妹妹艾琳的事。\u0022",
    "source_location": "vol1:ch7:1-20",
    "confidence": 0.9,
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
    "tags": ["first_appearance", "alias_rich", "supporting"]
  },
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440007",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "艾琳·沃倫",
    "attributes": {
      "canonical_name": "艾琳·沃倫",
      "source_name": "艾琳",
      "aliases": ["妹妹", "伊萊妹妹"],
      "role": "minor",
      "traits": [],
      "relationships": {
        "550e8400-e29b-41d4-a716-446655440001": "brother"
      },
      "cultivation_realm": null,
      "first_appearance": "第 7 章 (referenced)",
      "knowledge_tags": ["referenced_only", "family", "noble"],
      "arc_summary": null
    },
    "source_text": "...還有... 你妹妹艾琳的事。",
    "source_location": "vol1:ch7:19-20",
    "confidence": 0.5,
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
    "tags": ["referenced_only", "minor", "family"]
  }
]
```

**Confidence**: 0.95, 0.9, 0.5  
**Why**: Multiple aliases merged per CH-DUP-03; cross-chapter reference updates existing entity version; referenced-only character extracted with lower confidence.

---

## Error Examples

### Error Example 1: Hallucinated Character (Must Not Create Non-existent Characters)

**INPUT**

```
第 5 章：迷霧森林

伊萊獨自走在迷霧瀰漫的森林中。四周寂靜無聲，只有腳下枯葉碎裂的聲音。突然，一陣陣涼風吹過，彷彿有人在耳邊低語。
```

**Incorrect Extraction (FORBIDDEN)**

```json
[
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440008",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "森林守護精靈",
    "attributes": {
      "canonical_name": "森林守護精靈",
      "source_name": "森林守護精靈",
      "aliases": ["低語者", "守護者"],
      "role": "supporting",
      "traits": ["神秘", "古老", "守護森林"],
      "relationships": {},
      "cultivation_realm": "傳說級",
      "first_appearance": "第 5 章",
      "knowledge_tags": ["spirit", "guardian", "hallucinated"],
      "arc_summary": "守護迷霧森林的古老精靈，引導迷途者"
    },
    "source_text": "伊萊獨自走在迷霧瀰漫的森林中。四周寂靜無聲，只有腳下枯葉碎裂的聲音。突然，一陣陣涼風吹過，彷彿有人在耳邊低語。",
    "source_location": "vol1:ch5:1-5",
    "confidence": 0.0,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "rejected"
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["error_hallucination", "forbidden"]
  }
]
```

**Why Forbidden**: No character named "森林守護精靈" exists in source text. "彷彿有人在耳邊低語" is metaphorical/sensory description, not a character reference. Extracting hallucinated entities violates CORE PRINCIPLES: "NEVER hallucinate, infer beyond evidence, or use external knowledge."

---

### Error Example 2: Over-merging Distinct Characters

**INPUT**

```
第 10 章：雙城記

「白髮劍士」在北方戰場上橫掃千軍，敵軍聞風喪膽。
幾個月後，南方港口城市傳來消息：「銀髮刺客」在夜色中無聲收割目標性命。
```

**Incorrect Extraction (FORBIDDEN - Over-merge)**

```json
[
  {
    "entity_id": "550e8400-e29b-41d4-a716-446655440009",
    "entity_type": "character",
    "schema_version": "1.0",
    "name": "白髮/銀髮角色",
    "attributes": {
      "canonical_name": "白髮/銀髮角色",
      "source_name": "白髮劍士/銀髮刺客",
      "aliases": ["白髮劍士", "銀髮刺客", "北方戰神", "南方死神"],
      "role": "protagonist",
      "traits": ["白髮", "銀髮", "強大", "神秘"],
      "relationships": {},
      "cultivation_realm": "未知",
      "first_appearance": "第 10 章",
      "knowledge_tags": ["merged", "over_merge"],
      "arc_summary": "同一個人在不同場合使用不同身份"
    },
    "source_text": "\u0022白髮劍士\u0022在北方戰場上橫掃千軍，敵軍聞風喪膽。幾個月後，南方港口城市傳來消息：\u0022銀髮刺客\u0022在夜色中無聲收割目標性命。",
    "source_location": "vol1:ch10:1-5",
    "confidence": 0.3,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "rejected"
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["error_over_merge", "forbidden"]
  }
]
```

**Why Forbidden**: "白髮劍士" and "銀髮刺客" are distinct surface forms in different locations (north battlefield vs south port) with different roles (swordsman vs assassin). Without explicit textual evidence linking them, they must be extracted as separate entities per CH-DUP-04: "Cross-chapter same character → Separate entities; link via references later." Over-merging violates evidence-only principle.

---

*End of Character Extraction Few-shot Examples*
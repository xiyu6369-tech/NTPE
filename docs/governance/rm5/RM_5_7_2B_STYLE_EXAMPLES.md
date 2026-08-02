# RM-5.7.2B Style Extraction Few-shot Examples

**Purpose**: Style Extraction Examples  
**Prompt Version**: RM-5.7.2A  
**Schema Version**: style_schema.json (v1.0)  
**Status**: Design Complete  
**Compatible With**: RM-5.7.3 Validation Engine, RM-5.7.2C Golden Dataset

---

## Few-shot Examples

### Example 1: Author's Recurrent Phrase (Author Fingerprint)

**INPUT**

```
伊萊輕輕搖了搖頭，嘴角勾起一抹淡淡的微笑。
塞巴斯汀恭敬地颔首，眼中閃過一絲贊賞。
國王冷冷地看著他，嘴角勾起一抹冰冷的弧度。
伊萊無奈地搖搖頭，嘴角卻不自覺地上揚。
```

**Reasoning**

```
Evidence
Recurrent pattern: 嘴角勾起一抹...微笑/弧度/上揚 (4 occurrences)
Recurrent pattern: 搖頭 (3 occurrences)
Authorial fingerprint: Minimalist emotional expression through micro-gestures
Category: author_fingerprint, diction, syntax
Frequency: 5+ occurrences in sample
```

**Expected JSON**

```json
[
  {
    "entity_id": "990e8400-e29b-41d4-a716-446655440001",
    "entity_type": "style",
    "schema_version": "1.0",
    "name": "Author_MicroGesture_Smile",
    "attributes": {
      "style_type": "author_fingerprint",
      "category": "diction",
      "description": "Author consistently uses 嘴角勾起一抹[X]微笑/弧度 + 搖頭 pattern to convey emotion through minimal physical gestures",
      "examples": [
        "伊萊輕輕搖了搖頭，嘴角勾起一抹淡淡的微笑。",
        "國王冷冷地看著他，嘴角勾起一抹冰冷的弧度。",
        "伊萊無奈地搖搖頭，嘴角卻不自覺地上揚。"
      ],
      "rules": {
        "pattern": "Subject + 搖頭 + 嘴角勾起一抹[adj]微笑/弧度/上揚",
        "frequency": "High (5+ per chapter)",
        "translation_note": "Preserve minimalist gesture description"
      },
      "applies_to": "narration",
      "priority": 80,
      "author_profile": {
        "author_id": "author_001",
        "fingerprint_hash": "fp_microgesture_v1",
        "stylistic_markers": {
          "avg_sentence_length": 18.5,
          "gesture_to_dialogue_ratio": 0.7
        },
        "common_patterns": ["嘴角勾起一抹", "搖搖頭", "輕輕搖頭"]
      }
    },
    "source_text": "伊萊輕輕搖了搖頭，嘴角勾起一抹淡淡的微笑... 國王冷冷地看著他，嘴角勾起一抹冰冷的弧度... 伊萊無奈地搖搖頭，嘴角卻不自覺地上揚。",
    "source_location": "vol1:ch1-7:various",
    "confidence": 0.88,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "pending",
      "learned_from_approved": false
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["author_fingerprint", "micro_gesture", "recurrent_pattern", "diction"]
  }
]
```

---

### Example 2: Colloquial Dialogue Pattern (Register Rules)

**INPUT**

```
「少主，陛下召見。」塞巴斯汀恭敬道。
「走吧，塞巴斯汀。我不想讓父王久等。」伊萊淡淡說道。
「大人，屬下已經安排妥當。」黑衣人單膝跪地，聲音低沉。
「很好。讓那些自以為是的貴族們看看，什麼叫做真正的權力。」那男人冷笑。
「老夥計，別鬧了。」賽恩大笑，一把摟住伊萊的肩膀。
```

**Reasoning**

```
Evidence
Dialogue tags: 恭敬道, 說道, 低沉, 冷笑, 大笑
Honorifics: 少主, 陛下, 大人, 屬下
Register variation: Formal (塞巴斯汀) vs Casual (賽恩) vs Threatening (那男人)
Speech markers: 句末助詞 minimal, honorific-driven register
Category: register_rules, dialogue
```

**Expected JSON**

```json
[
  {
    "entity_id": "990e8400-e29b-41d4-a716-446655440002",
    "entity_type": "style",
    "schema_version": "1.0",
    "name": "Dialogue_Register_Hierarchy",
    "attributes": {
      "style_type": "register_rules",
      "category": "register",
      "description": "Dialogue register strictly follows social hierarchy: subordinates use honorifics (少主, 大人, 屬下) + formal tags (恭敬道); equals use casual address (老夥計) + expressive tags (大笑); antagonists use threatening tone (冷笑) + power language",
      "examples": [
        "\"少主，陛下召見。\"塞巴斯汀恭敬道。",
        "\"大人，屬下已經安排妥當。\"黑衣人單膝跪地，聲音低沉。",
        "\"老夥計，別鬧了。\"賽恩大笑...",
        "\"很好。讓那些自以為是的貴族們看看...\"那男人冷笑。"
      ],
      "rules": {
        "subordinate_to_superior": "honorific + formal_tag + polite_ending",
        "peer_to_peer": "casual_address + expressive_tag + direct_speech",
        "antagonist": "threatening_tag + power_vocabulary + imperative_mood"
      },
      "applies_to": "dialogue",
      "priority": 85,
      "author_profile": null
    },
    "source_text": "\"少主，陛下召見。\"塞巴斯汀恭敬道... \"大人，屬下已經安排妥當。\"黑衣人... \"很好...\"那男人冷笑。\"老夥計，別鬧了。\"賽恩大笑...",
    "source_location": "vol1:ch1,3,7:dialogue",
    "confidence": 0.9,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
---

### Example 3: Narrative Sentence Rhythm & Rhetorical Device (Pacing & Figurative)

**INPUT**

```
夜色如墨，王宮寢殿燈火通明。
伊萊臥在床上，腦海中還在回響著白天父王的眼神。
突然，窗外傳來一陣細微的聲響——像是有人輕輕落在屋頂上。
他猛地坐起，手已握劍：「誰在那裡？」
月光下，一道黑影從屋頂滑入窗內，穩穩落在床前。
```

**Reasoning**

```
Evidence
Sentence rhythm: Short punchy sentences (4-12 chars) for tension; longer for description
Rhetorical device: 夜色如墨 (simile), 像是有人輕輕落在屋頂上 (simile)
Pacing: Accelerating from static description to sudden action
Figurative language: 夜色如墨, 一道黑影 (metaphor)
Category: pacing, figurative, narration
```

**Expected JSON**

```json
[
  {
    "entity_id": "990e8400-e29b-41d4-a716-446655440003",
    "entity_type": "style",
    "schema_version": "1.0",
    "name": "Narrative_Tension_Pacing",
    "attributes": {
      "style_type": "collocation_patterns",
      "category": "pacing",
      "description": "Narrative pacing accelerates through sentence length variation: atmospheric opening (longer) -> internal state (medium) -> sudden trigger (short) -> action (short) -> visual payoff (medium). Similes used for atmospheric setting.",
      "examples": [
        "夜色如墨，王宮寢殿燈火通明。",
        "伊萊臥在床上，腦海中還在回響著白天父王的眼神。",
        "突然，窗外傳來一陣細微的聲響——像是有人輕輕落在屋頂上。",
        "他猛地坐起，手已握劍：\"誰在那裡？\"",
        "月光下，一道黑影從屋頂滑入窗內，穩穩落在床前。"
      ],
      "rules": {
        "sentence_length_progression": "12 -> 18 -> 22 -> 8 -> 16 characters",
        "simile_usage": "Atmospheric setting only (夜色如墨, 像是...)",
        "action_pacing": "Short sentences for sudden action/reaction"
      },
      "applies_to": "narration",
      "priority": 75,
      "author_profile": null
    },
    "source_text": "夜色如墨，王宮寢殿燈火通明。伊萊臥在床上... 突然... 他猛地坐起... 月光下，一道黑影...",
    "source_location": "vol1:ch4:26-35",
    "confidence": 0.85,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "pending",
      "learned_from_approved": false
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["pacing", "figurative", "narration", "sentence_rhythm", "simile"]
  }
]
```

**Confidence**: 0.85  
**Why**: Measurable sentence length progression; identifiable rhetorical devices; clear pacing pattern.

---

## Error Examples

### Error Example 1: Treating Character Catchphrase as Author Style

**INPUT**

```
「老夥計，別鬧了。」賽恩大笑。
「老友，好久不見。」賽恩拍肩。
「老夥計，這次麻煩大了。」賽恩皺眉。
```

**Incorrect Extraction (FORBIDDEN)**

```json
[
  {"entity_id": "...", "entity_type": "style", "name": "Author_Catchphrase_LaoHuoJi", "attributes": {"style_type": "author_fingerprint", "category": "diction", "description": "Author frequently uses '老夥計' as narrative device", "examples": ["老夥計，別鬧了", "老友，好久不見", "老夥計，這次麻煩大了"]}}
]
```

**Why Forbidden**: "老夥計" is character-specific dialogue (賽恩's catchphrase), not authorial narrative pattern. Confusing character voice with author fingerprint violates style extraction scope: author_fingerprint applies to narration, not character dialogue.

---

### Error Example 2: Subjective Style Judgment

**INPUT**

```
伊萊劍法精湛，動作行雲流水，美得令人窒息。
```

**Incorrect Extraction (FORBIDDEN)**

```json
[
  {"entity_id": "...", "entity_type": "style", "name": "Author_Poetic_Prose", "attributes": {"style_type": "genre_profile", "category": "figurative", "description": "Author's prose is poetic, elegant, and breathtakingly beautiful", "examples": ["動作行雲流水，美得令人窒息"]}}
]
```

**Why Forbidden**: "詩意、優雅、美得令人窒息" are subjective aesthetic judgments. Style extraction must be objective pattern description only. Violates: "NEVER subjective style judgments (elegant, clunky, poetic)" and "NEVER inferring author psychology or intent."

---

*End of Style Extraction Few-shot Examples*
      "validator_version": "1.0",
      "review_status": "pending",
      "learned_from_approved": false
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["register_rules", "dialogue", "hierarchy", "honorifics"]
  }
]
```

**Confidence**: 0.9  
**Why**: Clear register variation by social hierarchy with consistent patterns; multiple examples across characters.
**Confidence**: 0.88  
**Why**: High-frequency recurrent pattern (5+ occurrences) with consistent syntactic structure; clear authorial fingerprint.
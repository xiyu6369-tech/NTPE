# RM-5.7.2B Glossary Extraction Few-shot Examples

**Purpose**: Glossary Extraction Examples  
**Prompt Version**: RM-5.7.2A  
**Schema Version**: glossary_schema.json (v1.0)  
**Status**: Design Complete  
**Compatible With**: RM-5.7.3 Validation Engine, RM-5.7.2C Golden Dataset

---

## Few-shot Examples

### Example 1: Terminology First Appearance with Context

**INPUT**

```
第 2 章：修煉體系

伊萊在靈氣充裕的修煉室中盤膝而坐，引導著體內的「靈力」按著《九轉玄功》的運功路線流轉。丹田處的「氣海」穴位微微發熱，隨著每一個週天的運轉，原本渾濁的靈力逐漸變得純淨。這就是所謂的「煉氣期」——將外界靈氣引入體內，淬煉成自身靈力的過程。

「少主，您的『靈根』品質極佳，屬於罕見的『風雷雙靈根』，修煉速度將遠超常人。」塞巴斯汀在一旁恭敬地稟報道。
```

**Reasoning**

```
Evidence
Term repeated: 靈力 (4 times), 靈氣 (2 times), 氣海, 煉氣期, 靈根, 風雷雙靈根, 九轉玄功
Context defines: 煉氣期 (explicit definition), 靈根 (explicit quality description)
Explicit category markers: 功法, 境界, 體質, 穴位
Domain tags: cultivation, technique, realm, physique, acupoint
Translation obvious for cultivation terms
```

**Expected JSON**

```json
[
  {
    "entity_id": "660e8400-e29b-41d4-a716-446655440001",
    "entity_type": "glossary",
    "schema_version": "1.0",
    "name": "靈力",
    "attributes": {
      "canonical_translation": "Spiritual Power",
      "source_term": "靈力",
      "domain_tags": ["cultivation", "energy"],
      "part_of_speech": "noun",
      "context_rules": {
        "cultivation": "Spiritual Power",
        "general": "spiritual energy"
      },
      "forbidden_forms": ["magic power", "mana", "chi"],
      "aliases": ["靈氣", "真氣"],
      "notes": "Core energy cultivated by practitioners; distinct from external 靈氣",
      "relationships": {}
    },
    "source_text": "引導著體內的「靈力」按著《九轉玄功》的運功路線流轉。...隨著每一個週天的運轉，原本渾濁的靈力逐漸變得純淨。",
    "source_location": "vol1:ch2:2-6",
    "confidence": 0.95,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "pending",
      "lock_status": "unlocked"
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["first_appearance", "core_term", "high_frequency"]
  }
]
```

**Confidence**: 0.95  
**Why**: Explicit term with clear cultivation context; repeated multiple times; translation obvious.
---

### Example 1 (continued): 九轉玄功

**Expected JSON**

```json
[
  {
    "entity_id": "660e8400-e29b-41d4-a716-446655440002",
    "entity_type": "glossary",
    "schema_version": "1.0",
    "name": "九轉玄功",
    "attributes": {
      "canonical_translation": "Nine Revolutions Mysterious Art",
      "source_term": "九轉玄功",
      "domain_tags": ["cultivation", "technique", "manual"],
      "part_of_speech": "proper_noun",
      "context_rules": {},
      "forbidden_forms": ["Nine Turns Technique", "Nine Revolutions Technique"],
      "aliases": ["《九轉玄功》"],
      "notes": "Named cultivation technique; title format with book marks",
      "relationships": {}
    },
    "source_text": "按著《九轉玄功》的運功路線流轉",
    "source_location": "vol1:ch2:3-4",
    "confidence": 0.9,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "pending",
      "lock_status": "unlocked"
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["first_appearance", "technique", "named_manual"]
  }
]
```

**Confidence**: 0.9  
**Why**: Named technique with book marks; clear cultivation context.
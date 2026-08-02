# RM-5.7.2B Narrative Extraction Few-shot Examples

**Purpose**: Narrative Extraction Examples  
**Prompt Version**: RM-5.7.2A  
**Schema Version**: narrative_schema.json (v1.0)  
**Status**: Design Complete  
**Compatible With**: RM-5.7.3 Validation Engine, RM-5.7.2C Golden Dataset

---

## Few-shot Examples

### Example 1: Plot Event (Explicit Event)

**INPUT**

```
第 8 章：決戰前夕

「魔族大軍已抵達邊境。」偵察騎士單膝跪地，聲音急促，「距離王都不到三日路程。數量... 至少五萬。」

大殿一片死寂。伊萊握緊劍柄，感覺到掌心的汗水。這就是父王眼神裡的含義——不是授勛，而是送別。送他去死。

「傳令下去。」國王的聲音鐵一般冰冷，「全軍備戰。伊萊，你率領聖殿騎士團殿後。」

伊萊單膝跪地：「遵命。」
```

**Reasoning**

```
Evidence
Explicit event: 魔族大軍抵達邊境 (rising)
Explicit timeline: 距離王都不到三日路程
Explicit characters: 伊萊, 國王, 聖殿騎士團, 偵察騎士
Explicit consequence: 全軍備戰, 伊萊率領殿後
Type: rising action
Plot ID: PP-001
```

**Expected JSON**

```json
[
  {
    "entity_id": "880e8400-e29b-41d4-a716-446655440001",
    "entity_type": "narrative",
    "schema_version": "1.0",
    "name": "PP-001",
    "attributes": {
      "narrative_type": "plot_point",
      "plot_point": {
        "plot_id": "PP-001",
        "title": "魔族大軍壓境",
        "type": "rising",
        "description": "Demon army 50,000+ reaches border, 3 days from capital; King orders mobilization; Protagonist assigned rear guard",
        "affected_characters": ["550e8400-e29b-41d4-a716-446655440001", "550e8400-e29b-41d4-a716-446655440003", "550e8400-e29b-41d4-a716-446655440012"],
        "prerequisite_plots": [],
        "consequence_plots": ["PP-002"],
        "timeline_position": 1
      }
    },
    "source_text": "魔族大軍已抵達邊境... 伊萊單膝跪地：遵命。",
    "source_location": "vol1:ch8:1-15",
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
    "tags": ["plot_event", "rising", "military", "explicit"]
  }
]
---

### Example 2: Time Progression (Explicit Timeline)

**INPUT**

```
三日後，決戰爆發。

第一日，雙方在平原試探性交鋒，損失慘重。伊萊親率三百聖殿騎士衝入敵陣，斬殺魔族將領三名。

第二日，魔族祭司現身，施展禁術「血祭大法」，戰場死者盡化傀儡。聖殿騎士團損失過半，伊萊右臂中毒。

第三日黎明，伊萊在毒發昏迷前，以「九轉玄功」第七式「破曉」強行突破瓶頸，踏入「凝丹期」。一劍斬殺魔族祭司，大軍潰散。
```

**Reasoning**

```
Evidence
Explicit timeline: 三日後, 第一日, 第二日, 第三日黎明
Explicit events per day: 交鋒, 禁術, 突破
Character progression: 伊萊斬將 -> 中毒 -> 突破凝丹期
Technique: 九轉玄功第七式破曉
World rule: 血祭大法, 突破瓶頸
Timeline ID: TL-001
```

**Expected JSON**

```json
[
  {
    "entity_id": "880e8400-e29b-41d4-a716-446655440002",
    "entity_type": "narrative",
    "schema_version": "1.0",
    "name": "TL-001",
    "attributes": {
      "narrative_type": "timeline",
      "timeline": {
        "timeline_id": "TL-001",
        "name": "決戰三日記",
        "events": [
          {"position": 1, "event_id": "EVT-001", "event_type": "battle", "description": "雙方平原試探性交鋒，伊萊斬殺魔族將領三名"},
          {"position": 2, "event_id": "EVT-002", "event_type": "crisis", "description": "魔族祭司施展血祭大法，死者化傀儡，聖殿騎士團損失過半，伊萊右臂中毒"},
          {"position": 3, "event_id": "EVT-003", "event_type": "breakthrough", "description": "伊萊以九轉玄功第七式破曉突破至凝丹期，斬殺祭司，大軍潰散"}
        ]
      }
    },
    "source_text": "三日後，決戰爆發。第一日... 第三日黎明... 大軍潰散。",
    "source_location": "vol1:ch9:1-20",
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
    "tags": ["timeline", "time_progression", "breakthrough", "battle"]
  }
]
```

**Confidence**: 0.92  
**Why**: Explicit day-by-day progression with events, character state changes, cultivation breakthrough.
---

### Example 3: World Rule & Character Milestone

**INPUT**

```
決戰結束後，伊萊在療傷期間參悟了「凝丹期」的真諦。

原來，所謂「凝丹」，非將靈力壓縮成丹，而是將「意念」凝聚成形。靈力隨意動，意到力到。這就是《九轉玄功》第八層「意動力隨」的核心奧義——也是整個艾爾迪亞修煉界失傳千年的秘密。

「原來如此...」伊萊睜開眼，瞳孔深處閃過一絲金光，「修煉從來不是爭奪天地靈氣，而是掌控自身意念。」

這一悟，讓他從一介大劍師，真正邁入了修煉者的行列。也讓他明白了父王、長老會、審判庭都在爭奪什麼——不只是權力，而是這失傳的「意念掌控之法」。
```

**Reasoning**

```
Evidence
World rule: 凝丹期真諦 = 意念凝聚成形, 靈力隨意動
Cultivation system: 九轉玄功第八層意動力隨
Lost knowledge: 失傳千年的秘密
Milestone: 伊萊從大劍師邁入修煉者行列 (breakthrough)
Realization: 修煉本質是掌控意念而非爭奪靈氣
Category: cultivation_system
Rule ID: WR-001
Milestone ID: CM-001
```

**Expected JSON**

```json
[
  {
    "entity_id": "880e8400-e29b-41d4-a716-446655440003",
    "entity_type": "narrative",
    "schema_version": "1.0",
    "name": "WR-001",
    "attributes": {
      "narrative_type": "world_rule",
      "world_rule": {
        "rule_id": "WR-001",
        "category": "cultivation_system",
        "name": "凝丹期意念掌控法",
        "description": "Condensing core is not compressing spiritual power but condensing intent into form; power follows intent. Lost secret of Nine Revolutions Art 8th layer.",
        "constraints": ["Requires breakthrough bottleneck", "Intent must be pure", "Spiritual power follows intent"],
        "exceptions": ["Those with impure intent cannot condense", "External spiritual power seizure ineffective"],
        "source_volume": 1
      }
    },
    "source_text": "原所謂凝丹，非將靈力壓縮成丹，而是將意念凝聚成形... 失傳千年的秘密。",
    "source_location": "vol1:ch10:2-8",
    "confidence": 0.9,
    "metadata": {
      "extraction_method": "deterministic_prompt_v1",
      "extraction_model": "gpt-4o",
      "extraction_timestamp": "2025-08-02T00:00:00Z",
      "validator_version": "1.0",
      "review_status": "approved"
    },
    "created_at": "2025-08-02T00:00:00Z",
    "updated_at": "2025-08-02T00:00:00Z",
    "version": 1,
    "references": {},
    "tags": ["world_rule", "cultivation_system", "lost_knowledge", "core_secret"]
  },
  {
    "entity_id": "880e8400-e29b-41d4-a716-446655440004",
    "entity_type": "narrative",
    "schema_version": "1.0",
    "name": "CM-001",
    "attributes": {
      "narrative_type": "character_milestone",
      "character_milestone": {
        "character_id": "550e8400-e29b-41d4-a716-446655440001",
        "milestone_type": "breakthrough",
        "description": "Protagonist comprehends true meaning of Condensing Core realm; transitions from swordsman to true cultivator; gains intent-control ability",
        "chapter": 10,
        "impact_level": 9
      }
    },
    "source_text": "原來如此... 掌控自身意念。這一悟，讓他從一介大劍師，真正邁入了修煉者的行列。",
    "source_location": "vol1:ch10:9-15",
    "confidence": 0.88,
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
    "tags": ["character_milestone", "breakthrough", "realization", "high_impact"]
  }
]
```

**Confidence**: 0.9, 0.88  
**Why**: Explicit world rule with constraints/exceptions; explicit milestone with type and impact.

---

## Error Examples

### Error Example 1: Inferring Theme/Symbolism (Literary Analysis Forbidden)

**INPUT**

```
伊萊站在戰場上，夕陽將他的影子拉得很長。風吹過，旗幟獵獵作響。
```

**Incorrect Extraction (FORBIDDEN)**

```json
[
  {"entity_id": "...", "entity_type": "narrative", "name": "PP-099", "attributes": {"narrative_type": "plot_point", "plot_point": {"type": "revelation", "description": "Protagonist long shadow symbolizes growing burden and loneliness; flag flapping represents fleeting hope"}}}
]
```

**Why Forbidden**: No explicit plot event, timeline, world rule, or milestone. Literary interpretation of symbolism violates CORE PRINCIPLES: NEVER interpret themes, motifs, or symbolism.

---

### Error Example 2: Creating Causal Links Not in Text

**INPUT**

```
伊萊突破凝丹期。隔天，魔族撤軍。
```

**Incorrect Extraction (FORBIDDEN)**

```json
[
  {"entity_id": "...", "entity_type": "narrative", "name": "PP-002", "attributes": {"narrative_type": "plot_point", "plot_point": {"prerequisite_plots": ["PP-001"], "consequence_plots": ["PP-003"], "description": "Protagonist breakthrough DIRECTLY CAUSED demon retreat"}}}
]
```

**Why Forbidden**: Text only states temporal sequence, not causation. Adding DIRECTLY CAUSED infers unstated causal connection. Violates: NEVER infer unstated causal connections.

---

*End of Narrative Extraction Few-shot Examples*
```

**Confidence**: 0.95  
**Why**: Explicit event with timeline, affected characters, consequences, clear type.
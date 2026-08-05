# RM-5.9.0 Context Budget Policy

**Version**: RM-5.9.0  
**Date**: 2026-08-06  
**Status**: 🔒 **FROZEN — Governance Policy**

---

## Purpose

Define the token allocation policy governing context budget for knowledge injection in the Translation Runtime. This policy is mandatory for all RM-5.9.x knowledge-to-prompt integration.

---

## 1. Total Context Budget

### 1.1 Default Budget

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Context Window** | 131,072 | NVIDIA Llama 4 Maverick model limit |
| **Total Prompt Budget** | 8,192 | 1/16 of context window; treated as RM-5.4 established convention (TQI V72) |
| **Budget Unit** | Tokens (estimated as `len(text) // 4`) | Conservative Chinese+English token estimator |
| **Budget Enforcement** | Hard limit | Never exceed allocation for any domain |

### 1.2 Budget Derivation

```python
def derive_budget(context_window: int) -> int:
    """Courte of RM-5.4 Token Budget Analysis"""
    result = min(context_window // 16, 8192)
    return result
```

---

## 2. Per-Domain Allocation

### 2.1 Proportional Allocation Table

| Domain | % of Budget | Token Budget | Rationale |
|--------|------------|--------------|-----------|
| **Character** | 25% | 2,048 | Highest priority: character consistency is the #1 quality issue (per RM-5.4). Characters need contextual aliases, traits, and relationships. |
| **Glossary** | 20% | 1,638 | Second priority: term translation directly impacts correctness. Glossary entries average ~80 tokens each; ~12 entries fit under this budget. |
| **Scene** | 20% | 1,638 | Scene context includes location, participants, tone, and summary — each scene entry ~800 tokens; 2 scenes fit. Scene context affects translation atmosphere and character behavior decisions. |
| **Narrative** | 20% | 1,638 | Plot state, timeline, and world rules influence dialogue meaning and narrative flow. 5 plot points average ~320 each; exact fit at 1,600. |
| **Style** | 15% | 1,228 | Style is a refinement layer; tone/rules add nuance but rarely change meaning. 3 rules × 400 tokens each comfortable fit. |
| **Reserved** | — | 0 | Not a separate category; reserved is implicit from total - Σ(domain allocations). Domain allocations consume the full budget. Reserved space for source text + system + rules is managed separately by the existing RM-4 pipeline. |

**Verification**: 2,048 + 1,638 + 1,638 + 1,638 + 1,228 = 8,192 ✓

### 2.2 Allocation Rationale — Priority Tier

The domain allocation follows a non-uniform priority ordering:

```
Character (25%) > Glossary (20%) = Scene (20%) = Narrative (20%) > Style (15%)
```

| Domain | Priority | Why This Allocation? |
|--------|----------|---------------------|
| Character | 1 (highest) | Characters create identity; wrong names/relationships cascade to all downstream entities. |
| Glossary | 2 | Terminology fixes lock 1-to-1 translations. High precision operations (4% error rate) with clear impact. |
| Scene | 2 | Location/time/participants bound the LLMs' character behavior space. Large context with moderate per-entry detail. |
| Narrative | 2 | Plot position matters for mood/tone selection but not for fine-grained word choices. |
| Style | 3 (lowest) | Subjective complement; valency gates — nothing is damaged if omitted. |

**Note**: Narrative and scene are tied in % but processed in priority: Scene before Narrative (per injection policy ordering). In crisis budget (overallocation), style is the first to be culled, then narrative, then scene, glossary, character.

### 2.3 Source Text Reservation (Implicit from RM-4 Pipeline)

The existing `PromptBudget` has a `reserved_tokens: 3,584` for source text + instructions + overhead. This is **not part of the knowledge injection budget** — it is managed by the model's existing `PromptRenderer.render()` chunk assembly.

The knowledge context injection is **additional** to the source text, not a substitution.

---

## 3. Overflow Strategy

### 3.1 Detection

Overflow is detected per domain **during retrieval**:

```python
overflow_pcnt = (retrieved_tokens - domain_budget) / domain_budget
```

| Overflow Range | Strategy |
|---------------|----------|
| ≤ 0% | No overflow — inject as-is |
| 1-5% over | Truncate last entry (minor) |
| 5-15% over | Prioritize by confidence, drop low-confidence entities |
| 15+% over | Summarize top entries → drop remainder; flag for manual review |

### 3.2 Overflow Strategies per Domain

| Strategy | Domain | Behavior |
|----------|--------|----------|
| `PRIORITIZE_CONFIDENCE` | Character, Glossary | Sort entities by `confidence` desc → take top N within budget; discard rest |
| `TRUNCATE_FROM_TAIL` | Scene | Since scene ordering is chronological (by chapter_id) → truncate later scenes first |
| `SUMMARIZE_TOP` | Narrative | Compress 5 plot points into 3 summary bullets; preserve timeline anchors |
| `DROP_DOMAIN` | Style | The most disposable domain — if overflow in budget, drop style entirely |

### 3.3 Graceful Degradation Priority

When total injection would exceed the budget, culling order:

```
Style → (if still overflow) Narrative → (if still overflow) Scene (drop to 1) → (if still overflow) Glossary (keep all) → Character (keep all)
```

Character and Glossary are **never dropped** unless both the budget is exhausted with only Character+Glossary still exceeding. This should never happen at 45% allocation.

---

## 4. Truncation Policy

### 4.1 Entity-Level Truncation (Infile)

Each entity is whole or not injected (no silent partial truncation of a single entity). A DON'T inject half a glossary entry — the truncated term would give the LLM incomplete or misleading information.

### 4.2 Character Entity Truncation

| Condition | Behavior |
|-----------|----------|
| entity.count > 0 AND entity.field ≤ domain_budget | Inject entity as-is |
| entity.fields exceed remaining budget for domain | Skip entity; add to omission report |
| entity.fails_char_budget && entity == last in domain | Note `truncated_character_records: count_N` in metadata |

### 4.3 Generalization

An incomplete record is worse than no record. The policy is: **full entity or nothing.**

---

## 5. Summarization Policy

### 5.1 When to use summarization

| Trigger | Domain | Summarization |
|---------|--------|---------------|
| Single entity but 5+ plot_points in narrative | Narrative | Reduce to 3 most relevant, skip minor plot points |
| Single Scene has 10+ participants | Scene | List "3 main participants + 7 others" |
| Glossary entries > 20 | Glossary | Keep top 12 by confidence + relevance to context |

### 5.2 Summarization Format

```
【場景知識】 (摘要)
位置: {location} | 時間: {time_of_day}
主要角色: {A, B, C} (共 {N} 人)
```

The `(摘要)` suffix means the model knows this was summarized.

---

## 6. Budget Declaration

### 6.1 Metadata for Every Injection

```json
{
  "budget_policy": "rm-5.9.0",
  "total_budget_tokens": 8192,
  "domains_budget": {
    "character": 2048,
    "glossary": 1638,
    "scene": 1638,
    "narrative": 1638,
    "style": 1228
  },
  "budget_exhausted": false,
  "budget_exhaustion_details": {
    "any_exhausted": false,
    "exhausted_domains": []
  },
  "budget_used_tokens": 5200,
  "budget_remaining_tokens": 2992
}
```

---

## 7. Configuration Override

Budget can be customized per project via package metadata:

```json
"metadata": {
  "knowledge_budget_character_tokens": 3000,
  "knowledge_budget_glossary_tokens": 2000,
  "knowledge_budget_total": 10000
}
```

Overrides are validated against context window constraints: `total budget ≤ context_window / 16`.

---

## 8. Reference Documents

| Document | Role |
|----------|------|
| `RM_5_9_0_RUNTIME_INTEGRATION_ARCHITECTURE.md` | Parent architecture |
| `RM_5_9_0_PROMPT_INJECTION_POLICY.md` | Injection order policy |
| `RM_5_9_0_RUNTIME_SEQUENCE.md` | Sequence diagrams |
| `RM_5_9_0_RUNTIME_CACHE_POLICY.md` | Caching policy |
| `RM_5_4_TOKEN_BUDGET_ANALYSIS.md` | Original TQI V72 budget analysis |
| `RM_5_2_CONTEXT_INVENTORY.md` | Current context inventory |

---

*This policy is FROZEN as of RM-5.9.0 (2026-08-06). All subsequent RM-5.9.x stages must enforce this budget.*
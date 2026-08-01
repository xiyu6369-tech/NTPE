# RM-5.5 Glossary Runtime Integration Audit Report

> **Stage**: RM-5.5 Glossary Runtime Integration Audit  
> **Status**: ✅ COMPLETE — Audit Only, Zero Production Code Modified  
> **Date**: 2026-08-01  
> **Provider Requests**: 0  
> **Network Requests**: 0

---

## Executive Summary

The **Glossary code path from storage to prompt is fully implemented and wired** in the production pipeline. However, the **structured glossary data file (`memory/glossary.json`) does not exist**, causing the pipeline to crash at `PromptBuilder` initialization if executed.

**Verdict**: Glossary system is **CODE-READY but DATA-BLOCKED**.

---

## 1. Current Glossary Flow Audit

### 1.1 Complete Data Flow Trace (Code Path)

```
Input Chunk (chunk_text)
       │
       ▼
┌─────────────────────────────────────┐
│ PromptBuilder.__init__              │
│   └─ PromptBuilderLoader.load_all() │
│       └─ load_glossary(profile)     │  ← profile["knowledge_sources"]["glossary"] = "memory/glossary.json"
└─────────────────────────────────────┘
       │
       ▼ (returns dict: source → {translation, category, locked, confidence, ...})
┌─────────────────────────────────────┐
│ GlossarySelector.select(chunk_text) │  ← substring/regex matching
└─────────────────────────────────────┘
       │
       ▼ (list[dict] with source, target, category, locked, confidence, total_count)
┌─────────────────────────────────────┐
│ PromptBuilder.build()               │
│   glossary_matches = selector.select│
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ PromptRenderer.render()             │
│   if glossary_matches:              │
│       parts.append("【本段術語】")    │
│       for item in glossary_matches: │
│           parts.append(f"- {src}→{tgt}")  ← INJECTED INTO user_prompt
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ PackageBuilder.build()              │
│   knowledge.glossary_matches = [...]│
│   locked_dictionary[src] = tgt      │  ← for QA validation
---

## 2. Structured Glossary Data Status

### 2.1 Profile Configuration

```json
// profiles/passion_profile.json:65
"knowledge_sources": {
  "glossary": "memory/glossary.json"
}
```

### 2.2 File Existence Check

| File | Path | Exists | Notes |
|------|------|--------|-------|
| **Structured Glossary (target)** | `memory/glossary.json` | ❌ **NO** | Profile points here |
| Legacy Flat Glossary | `data/glossary.txt` | ❌ NO | Used by LTS runtime only |
| Glossary Override (manual) | `glossary_override.json` | ❌ NO | Input for builder |
| Auto Candidates | `analysis/*_glossary_auto.json` | ❌ NO | Output of Document Analyzer |
| Historical Archive | `archive/historical/memory/glossary.json` | ✅ YES | Old version, not in runtime path |

### 2.3 Glossary Builder Pipeline (Data Generation)

```
Document Analyzer → analysis/*_glossary_auto.json
                            │
                            ▼
              ┌─────────────────────────┐
              │ Glossary Builder        │
              │ (core/glossary_builder) │
              │ 1. Merge auto candidates│
              │ 2. Classify terms       │
              │ 3. Apply override.json  │
              │ 4. Score confidence     │
              │ 5. Output:              │
              │    - memory/glossary.json│  ← REQUIRED by runtime
              │    - character_alias_index.json
              │    - glossary_report.txt
              │    - glossary.csv
              └─────────────────────────┘
```

**Current Blockage**: No `analysis/*_glossary_auto.json` files exist → Glossary Builder cannot run → `memory/glossary.json` never created.

---

## 3. Runtime Behavior Analysis

### 3.1 What Happens on Pipeline Execution

```python
# PromptBuilder.__init__ (prompt_builder.py:47-54)
def __init__(self, root, profile_path=None):
    self.loader = PromptBuilderLoader(self.root)
    self.data = self.loader.load_all(profile_path)  # ← CALLS load_glossary()
    self.glossary_selector = GlossarySelector(self.data["glossary"])  # ← CRASH HERE
```

```python
# PromptBuilderLoader.load_glossary (loader.py:21-23)
def load_glossary(self, profile):
    data = load_json(self.root / profile["knowledge_sources"]["glossary"])  # ← FileNotFoundError
    return data.get("terms", data)
```

```python
# utils.load_json (utils.py:18-20)
def load_json(path):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))  # ← NO ERROR HANDLING
```

**Result**: `FileNotFoundError: [Errno 2] No such file or directory: 'memory/glossary.json'`

### 3.2 Legacy Glossary Path (Unused by Production)

| Component | File | Format | Used By |
|-----------|------|--------|---------|
| `Glossary` class | `core/glossary.py` | Flat `key=value` txt | LTS runtime (`lts/txt_translation_runtime.py`) |
| `load_glossary_text` | `lts/txt_translation_runtime.py` | Flat txt | TXT Translation Runtime |
| **Production Pipeline** | `PromptBuilderLoader` | Structured JSON | **NOT using legacy path** |

---

## 4. Quality Impact Assessment

| Quality Dimension | Current State | Impact if Glossary Active | Blocking Factor |
|-------------------|---------------|---------------------------|-----------------|
| **人名一致性** (Character Names) | ✅ Active via `character_match_dictionary.json` | Already covered | None |
| **專有名詞一致性** (Proper Nouns) | ❌ **BLOCKED** — glossary data missing | **HIGH** — would enforce term consistency across chapters | `memory/glossary.json` missing |
| **長篇章節穩定性** (Long-form Stability) | ❌ **BLOCKED** — no cross-chapter term lock | **HIGH** — glossary provides canonical translations | `memory/glossary.json` missing |
| **Token 成本** | N/A | **LOW** — only matched terms injected (substring match) | Negligible |
| **Runtime 負擔** | N/A | **LOW** — O(n) string matching per chunk | Negligible |

**Key Insight**: The glossary selector uses efficient substring/regex matching (`glossary_selector.py:27-31`). Only terms appearing in the current chunk are injected. Token overhead is proportional to matches, not glossary size.

---

## 5. Migration Risk Assessment

| Factor | Assessment | Detail |
|--------|------------|--------|
| **Code Changes Required** | **NONE** | Full code path implemented and wired |
| **Data Generation Required** | **YES** | Run Document Analyzer → Glossary Builder |
| **Profile Changes Required** | **NO** | Already points to correct path |
| **Backward Compatibility** | **SAFE** | Adding data file only, no schema change |
| **Rollback Complexity** | **TRIVIAL** | Delete `memory/glossary.json` |
| **Provider Execution Risk** | **ZERO** | Audit only, no API calls |
| **Production Downtime** | **NONE** | Data generation is offline process |

### 5.1 Recommended Unblock Sequence

```bash
# 1. Run Document Analyzer (produces analysis/*_glossary_auto.json)
python -m core.document_analyzer  # or equivalent launcher

# 2. Prepare manual overrides (optional but recommended)
# Create glossary_override.json with locked terms

# 3. Run Glossary Builder
python core/glossary_builder.py

# 4. Verify output
cat memory/glossary.json | jq '. | length'  # should show term count
```

### 5.2 Glossary Builder Dependencies

| Dependency | Status | Action |
|------------|--------|--------|
| `analysis/*_glossary_auto.json` | ❌ Missing | Run Document Analyzer first |
| `glossary_override.json` | ❌ Missing | Create manually for locked terms |
| `memory/character_database.json` | ❓ Check | Required for character alias index |
| `core/character_resolver.py` | ✅ Exists | Used by builder |

---
---
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ TranslationEngine.translate_package()│
│   → ProviderRequest(user_prompt, ...)│
└─────────────────────────────────────┘
```

### 1.2 Evidence Map

| Step | Module | File | Line(s) | Status |
|------|--------|------|---------|--------|
---

## 6. Evidence Summary

### 6.1 Files Read (Zero Modifications)

| File | Purpose |
|------|---------|
| `core/prompt_builder/loader.py` | Glossary loading logic |
| `core/prompt_builder/glossary_selector.py` | Term matching logic |
| `core/prompt_builder/prompt_builder.py` | Orchestration + selector call |
| `core/prompt_builder/prompt_renderer.py` | Prompt injection (`【本段術語】`) |
| `core/prompt_builder/package_builder.py` | Package serialization + locked_dict |
| `core/prompt_builder/utils.py` | `load_json` (no error handling) |
| `profiles/passion_profile.json` | Profile config (`knowledge_sources.glossary`) |
| `core/glossary_builder.py` | Data generation pipeline |
| `core/glossary.py` | Legacy flat glossary (unused by prod) |
| `engine/pipeline/production_pipeline.py` | Production entry (uses PromptBuilder) |
| `docs/governance/rm5/RM_5_2_CONTEXT_INVENTORY.md` | Prior audit context |
| `docs/governance/rm5/RM_5_2_EXECUTION_REPORT.md` | Prior audit execution |

### 6.2 Search Operations Performed

- `glossary.*selector` → `core/prompt_builder/glossary_selector.py`
- `load_glossary` → `loader.py:21`
- `PromptBuilderLoader` → `loader.py:9`
- `memory/glossary.json` → Profile reference only, file missing
- `analysis/*_glossary_auto.json` → Zero matches in workspace
- `glossary_override.json` → Zero matches in workspace

---

## 7. Conclusions

### 7.1 Audit Findings

| Finding | Severity | Evidence |
|---------|----------|----------|
| Glossary **code path complete** | ✅ POSITIVE | All 6 stages implemented |
| Glossary **data file missing** | 🔴 CRITICAL | `memory/glossary.json` does not exist |
| Pipeline **would crash** on start | 🔴 CRITICAL | `load_json` throws `FileNotFoundError` |
| Legacy glossary **not used by prod** | ⚠️ INFO | Separate code path (LTS only) |
| Quality impact **blocked by data** | 🔴 CRITICAL | Proper nouns, long-form stability |
| Migration risk **very low** | ✅ LOW | No code changes, offline data gen |

### 7.2 RM-5.5 Verdict

> **Glossary Runtime Integration = CODE COMPLETE, DATA BLOCKED**
> 
> The production pipeline has full glossary integration wired from storage to prompt injection. The only blocker is the absence of `memory/glossary.json`, which requires running the Document Analyzer + Glossary Builder pipeline (offline, no provider calls).

### 7.3 Next Stage Readiness (RM-5.6)

RM-5.6 (Glossary Data Generation) can proceed immediately:
- No code modifications needed
- Clear dependency chain: Document Analyzer → Glossary Builder
- Zero provider/network risk
- Single output artifact: `memory/glossary.json`

---

## 8. Compliance Checklist

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Zero production code modified | ✅ | Read-only analysis |
| Zero provider requests | ✅ | No API calls |
| Zero network requests | ✅ | No outbound HTTP |
| Full data flow traced | ✅ | 6-stage trace documented |
| `memory/glossary.json` status confirmed | ✅ | File missing, profile points to it |
| Quality impact assessed | ✅ | Table in Section 4 |
| Migration risk evaluated | ✅ | Table in Section 5 |
| Report output to `docs/governance/rm5/` | ✅ | This file + evidence index |

---

*Report generated by RM-5.5 Audit — Evidence-only, no modifications.*
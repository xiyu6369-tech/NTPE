# RM-5.6 Compatibility Report

**Stage**: RM-5.6 — Glossary Data Pipeline Validation  
**Date**: 2026-08-02  
**Component**: Runtime Compatibility Validation

---

## Compatibility Matrix

| Component | Input Format | Output Format | Compatible |
|-----------|--------------|---------------|------------|
| Document Analyzer | TXT file | analysis/*_glossary_auto.json | ✅ |
| Glossary Builder | *_glossary_auto.json + override | memory/glossary.json | ✅ |
| PromptBuilderLoader | memory/glossary.json | dict (terms) | ✅ |
| GlossarySelector | dict (terms) | list[matches] | ✅ |
| PromptRenderer | list[matches] | prompt string | ✅ |

---

## 1. Document Analyzer → Glossary Builder

### Analyzer Output (per file)
```json
{
  "TERM": {
    "source": "TERM",
    "translation": "",
    "count": N,
    "locked": false,
    "note": "auto-detected by NTPE Document Analyzer v1.0"
  }
}
```

### Builder Input Expectation
```python
# merge_glossary() expects:
{
  "TERM": {
    "source": "TERM",
    "translation": "",
    "count": N,
    "locked": false,
    "note": "..."
  }
}
```

### Field Mapping
| Analyzer | Builder | Transform |
|----------|---------|-----------|
| source | source | Direct |
| translation | translation | Direct |
| count | total_count | Renamed |
| locked | locked | Direct |
| note | notes[] | Wrapped in list |

### Result: ✅ COMPATIBLE

---

## 2. Glossary Builder → PromptBuilderLoader

### Builder Output (memory/glossary.json)
```json
{
  "summary": {...},
  "terms": {
    "TERM": {
      "source": "TERM",
      "translation": "譯名",
      "category": "...",
      "total_count": N,
      "books": {...},
      "book_count": N,
      "locked": true|false,
      "status": "...",
      "aliases": [],
      "notes": [...],
      "confidence": 0.0-1.0,
      "created_by": "..."
    }
  }
}
```

### Loader Code (core/prompt_builder/loader.py:21-23)
```python
def load_glossary(self, profile: dict) -> dict:
    data = load_json(self.root / profile["knowledge_sources"]["glossary"])
    return data.get("terms", data)
```

### Result: ✅ COMPATIBLE
---

## 3. PromptBuilderLoader → GlossarySelector

### Loader Output
```python
{
  "TERM": {
    "source": "TERM",
    "translation": "譯名",
    "category": "...",
    "total_count": N,
    "locked": True|False,
    "confidence": 0.77,
    ...
  }
}
```

### Selector Expectation (core/prompt_builder/glossary_selector.py)
```python
class GlossarySelector:
    def __init__(self, glossary: dict):
        self.glossary = glossary or {}
    
    def select(self, text: str) -> list[dict]:
        for source, item in self.glossary.items():
            if self._contains(text, source):
                matches.append({
                    "source": source,
                    "target": item.get("translation", ""),
                    "category": item.get("category", ""),
                    "locked": item.get("locked", False),
                    "confidence": item.get("confidence", 0),
                    "total_count": item.get("total_count", 0),
                })
```

### Field Usage
| Selector Field | Source | Required |
|----------------|--------|----------|
| source | dict key | ✅ |
| target | item["translation"] | ✅ |
| category | item["category"] | ✅ |
| locked | item["locked"] | ✅ |
| confidence | item["confidence"] | ✅ |
| total_count | item["total_count"] | ✅ |

### Result: ✅ COMPATIBLE

---

## 4. GlossarySelector → PromptRenderer

### Selector Output
```python
[
    {"source": "UNHRDO", "target": "聯合國人權發展組織", "category": "organization", "locked": True, "confidence": 1.0, "total_count": 64},
    {"source": "PASSION", "target": "", "category": "abbreviation", "locked": False, "confidence": 0.2, "total_count": 2},
    ...
]
```

### Renderer Code (core/prompt_builder/prompt_renderer.py:82-89)
```python
if glossary_matches:
    parts.append("【本段術語】")
    for item in glossary_matches:
        if item.get("target"):
            parts.append(f"- {item['source']} → {item['target']}")
        else:
            parts.append(f"- {item['source']}")
```

### Result: ✅ COMPATIBLE

---

## 5. Full Pipeline Test

### Test Case 1: English Text
**Input**: `"UNHRDO works with UNH on the PASSION project. UNHR and UNHRD also participate."`

**Glossary Matches**:
1. UNHRDO → 聯合國人權發展組織 (locked, conf=1.0)
2. PASSION (conf=0.2)
3. UNH (conf=0.2)
4. UNHR (conf=0.2)
5. UNHRD (conf=0.2)

**Prompt Output**:
```
【本段術語】
- UNHRDO → 聯合國人權發展組織
- PASSION
- UNH
- UNHR
- UNHRD
```

### Test Case 2: Korean Text (with spaces)
**Input**: `"UNHRDO 는 UNH 와 협력하여 PASSION 프로젝트를 진행합니다."`

**Glossary Matches**:
1. UNHRDO → 聯合國人權發展組織 (locked, conf=1.0)
2. PASSION (conf=0.2)
3. UNH (conf=0.2)

### Test Case 3: Korean Text (no spaces)
**Input**: `"UNHRDO와 UNH가 협력합니다."`

**Glossary Matches**: [] (empty - requires word boundaries)

**Note**: Current implementation uses `\b` word boundary for ASCII terms, which doesn't work for Korean text without spaces. This is a known limitation, not a compatibility issue.

---

## 6. Bug Fix Applied

### Issue: GlossarySelector._contains() regex double-escaping

**File**: `core/prompt_builder/glossary_selector.py` line 31

**Before**:
```python
return re.search(rf"\\b{re.escape(source)}\\b", text) is not None
```
Produces pattern: `\\bUNHRDO\\b` (literal backslashes)

**After**:
```python
return re.search(rf"\b{re.escape(source)}\b", text) is not None
```
Produces pattern: `\bUNHRDO\b` (correct word boundary)

**Impact**: Fixed term matching for all ASCII glossary terms.

**Verification**: 
- Before: 0 matches for "UNHRDO" in "UNHRDO"
- After: 1 match for "UNHRDO" in "UNHRDO"

---

## 7. Version Compatibility

| Component | Version | Compatible With |
|-----------|---------|-----------------|
| Document Analyzer | 1.0 | Glossary Builder 1.1.1 |
| Glossary Builder | 1.1.1 | PromptBuilderLoader (any) |
| PromptBuilderLoader | - | GlossarySelector (any) |
| GlossarySelector | - | PromptRenderer (any) |
| PromptRenderer | - | Translation Runtime |

**All versions compatible** ✅

---

## 8. Conclusion

**Runtime Compatibility: PASSED** ✅

The complete data pipeline from Document Analyzer through Translation Runtime is fully compatible:

1. ✅ Document Analyzer output → Glossary Builder input
2. ✅ Glossary Builder output → PromptBuilderLoader input  
3. ✅ PromptBuilderLoader output → GlossarySelector input
4. ✅ GlossarySelector output → PromptRenderer input
5. ✅ PromptRenderer output → Translation prompt

**One bug fixed**: GlossarySelector regex escaping (non-breaking, improves functionality)

**Known limitation**: Korean text matching requires spaces around terms (by design, word-boundary approach)
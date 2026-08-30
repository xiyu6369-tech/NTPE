#!/usr/bin/env python3
"""
P0-FINAL-15-S: Gate I — Human Literary Review

Generates Human Review Bundle for manual evaluation.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def get_git_baseline() -> dict:
    import subprocess
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        origin_main = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True, check=True).stdout.strip()
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        result = subprocess.run(["git", "rev-list", "--left-right", "--count", f"{origin_main}...{head}"], capture_output=True, text=True)
        divergence = f"{result.stdout.strip().split()[0]}/{result.stdout.strip().split()[1]}" if result.returncode == 0 else "unknown"
        return {"head_commit": head, "origin_main_commit": origin_main, "divergence": divergence, "branch": branch}
    except Exception as e:
        return {"head_commit": "error", "origin_main_commit": "error", "divergence": "error", "branch": "error", "error": str(e)}


def redact_sensitive(data: dict) -> dict:
    if not isinstance(data, dict): return data
    redacted = {}
    sensitive = {"authorization", "api_key", "apikey", "secret", "token", "password", "credential", "bearer", "x-api-key"}
    for k, v in data.items():
        if k.lower() in sensitive: redacted[k] = "[REDACTED]"
        elif isinstance(v, dict): redacted[k] = redact_sensitive(v)
        elif isinstance(v, list): redacted[k] = [redact_sensitive(i) if isinstance(i, dict) else i for i in v]
        else: redacted[k] = v
    return redacted


def load_artifact(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_fixtures() -> dict[str, dict]:
    fixtures = {}
    golden_path = Path(__file__).resolve().parents[2] / "tests" / "literary" / "Golden_Set" / "original_ko.txt"
    if golden_path.exists():
        narrative = golden_path.read_text(encoding="utf-8")
    else:
        narrative = "정태의는 아차, 하고 자리에서 일어섰다. 카일은 프라이빗풀 옆의 벤치에서 정신없이 잠들어 있을 터였다. (일주일의 휴가를 위해 그가 이곳에 오기 직전까지 밤을 새며 퀭한 얼굴로 일했다는 걸 정태의는 알고 있었다. 그래서, 그가 막무가내로 여기에 오겠다고 하는 주장을 차마 거를 수 없었다.) 라군에서 바닷가는, 당연하다면 당연하지만, 엎어지면 코 닿을 거리였다. 근처만 서성이려면 바다 위로 뻗은 나무다리 위로 산책을 할 수도 있지만, 정태的は 천천히 섬을 한 바퀴 돌아보자고 생각하고 백사장 쪽을 선택했다. 대충 걸어서 두어 시간이면 한 바퀴 다 돌 수 있을 정도로 작은 섬이라고 들었다. 무릅까지 오는 반바지 위에 넉넉한 셔츠 하나만 대충 걸치고, 그가 막 로비에서 나서려던 때였다. 새로운 손님이 왔는지, 바깥에서 약간 떠들썩하게―라고 해도 이곳이 워낙 조용해서, 단순한 말소리조차 그렇게 들릴 뿐이었지만―두세 명이 들어서고 있었다. 정태的是 저도 모르게 걸음을 멈추었다. 귀에 익은 독일어가 들렸다."
    
    fixtures["narrative"] = {"name": "narrative", "type": "narrative", "source": narrative}
    
    fixtures["dialogue"] = {
        "name": "dialogue", "type": "dialogue",
        "source": (
            '"정말 괜찮아?" 민수가 조심스럽게 물었다.\n\n'
            '지현은 고개를 끄덕이며 억지로 미소를 지었다. "응, 괜찮아. 그냥... 좀 피곤할 뿐이야."\n\n'
            '"아니, 네 눈빛이 그렇지 않아. 무슨 일 있어? 말해줘."\n\n'
            '지현은 잠시 망설였다. 그리고 낮게 한숨을 내쉬었다.\n\n'
            '"사실은... 내일 발표가 있어. 준비가 안 돼서 그래."\n\n'
            '민수는 놀란 듯 눈을 크게 떴다. "내일이면 하루 남았잖아? 왜 이제 말해?"\n\n'
            '"말해봤자 도와줄 수도 없으니까. 내 문제니까 내가 해결해야지."\n\n'
            '"그런 말 하지 마. 우린 친구잖아. 같이 해결하면 되잖아."\n\n'
            '그 말 한마디에 지현의 눈시울이 뜨거워졌다.'
        )}
    
    fixtures["continuity"] = {
        "name": "continuity", "type": "continuity",
        "source": (
            '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, '
            '그는 특유的 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. '
            '논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.\n\n'
            '어느 날, 두 사람은 연쇄 실종 사건을 맡게 되었다. '
            '철수는 현장의 미세한 흔적에서 단서를 찾으려 했고, 영희는 피해자들의 공통점을 분석했다. '
            '처음엔 서로의 방식을 불신했지만, 곧 그들의 접근法이 서로 보완됨을 깨달았다. '
            '철수의 직관이 영희的 논리를 이끌었고, 영희的 증거가 철수의 추측을 뒷받침했다.'
        )}
    
    return fixtures


def load_glossary() -> dict[str, str]:
    return {
        "정태的": "鄭泰義", "카일": "凱爾", "민수": "旻秀", "지현": "智賢",
        "김철수": "金哲秀", "이영희": "李英姬", "프라이빗풀": "私人泳池",
        "라군": "潟湖", "백사장": "沙灘", "로비": "大廳", "독일어": "德語",
        "동행": "同行", "베를린": "柏林", "남국": "南國", "섬": "島嶼",
        "호텔": "飯店", "형사": "刑警", "파트너": "搭檔", "원칙주의자": "原則主義者",
        "연쇄 실종 사건": "連環失蹤案", "현장": "現場", "피해자": "受害者",
        "공통점": "共同點", "직관": "直覺", "논리": "邏輯", "증거": "證據", "推測": "推測",
    }


def load_translation_results() -> dict:
    """Load translation results from previous gates."""
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    
    results = {}
    
    # Load translation quality results
    tq_path = artifacts_dir / "P0_FINAL_15_S_GPT_OSS_120B_TRANSLATION_QUALITY_REPORT.json"
    if tq_path.exists():
        with open(tq_path, "r", encoding="utf-8") as f:
            results["translation_quality"] = json.load(f)
    
    # Load M1 baseline (if available)
    # We'll use existing M1 output from previous phases
    
    return results


def generate_human_review_bundle():
    """Generate human review bundle with source texts and translations."""
    baseline = get_git_baseline()
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    bundle_dir = artifacts_dir / "P0_FINAL_15_S_Human_Review_Bundle"
    bundle_dir.mkdir(exist_ok=True)
    
    fixtures = load_fixtures()
    glossary = load_glossary()
    tq_data = load_artifact(artifacts_dir / "P0_FINAL_15_S_GPT_OSS_120B_TRANSLATION_QUALITY_REPORT.json")
    
    # Load candidate translations
    candidate_translations = {}
    if tq_data and "translations" in tq_data:
        for t in tq_data["translations"]:
            key = f"{t['fixture_type']}_{t['mode']}"
            candidate_translations[key] = t["translation"]
    
    # Load M1 baseline (from previous phases)
    m1_translations = {}
    # We'll check if there are M1 outputs from previous phases
    # For now, we'll note that M1 has 429 issues so we may not have recent outputs
    
    # Create bundle structure
    bundle = {
        "phase": "P0-FINAL-15-S",
        "gate": "I — Human Literary Review",
        "candidate": "openai/gpt-oss-120b",
        "hosting": "NVIDIA",
        "baseline": {
            "head_commit": baseline["head_commit"],
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        },
        "source_texts": {name: f["source"] for name, f in fixtures.items()},
        "fixtures": {name: {"type": f["type"], "description": f"See source_texts"} for name, f in fixtures.items()},
        "glossary": glossary,
        "candidate_translations": candidate_translations,
        "m1_translations": m1_translations,
        "automated_scores": {},
        "review_rubric": {
            "dimensions": [
                {"name": "Semantic Accuracy", "weight": 15, "description": "Meaning preserved without distortion"},
                {"name": "Traditional Chinese Naturalness", "weight": 15, "description": "Reads like native Taiwan publication"},
                {"name": "Literary Fluency", "weight": 10, "description": "Flow, rhythm, prose quality"},
                {"name": "Narrative Voice", "weight": 10, "description": "Consistent narrator tone and perspective"},
                {"name": "Character Voice", "weight": 10, "description": "Distinct character speech patterns"},
                {"name": "Dialogue Naturalness", "weight": 10, "description": "Conversational authenticity"},
                {"name": "Terminology Consistency", "weight": 10, "description": "Glossary adherence"},
                {"name": "Continuity", "weight": 10, "description": "Cross-chunk consistency"},
                {"name": "No Major Omission", "weight": 5, "description": "No content dropped"},
                {"name": "No Major Hallucination", "weight": 5, "description": "No invented content"},
            ],
            "scoring": "Each dimension: 1-10. PASS threshold: weighted avg >= 7.0",
            "blind_evaluation": True,
        },
    }
    
    # Save bundle JSON
    bundle_path = bundle_dir / "human_review_bundle.json"
    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)
    
    # Create source files for easy reading
    for name, fixture in fixtures.items():
        src_path = bundle_dir / f"source_{name}.txt"
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(fixture["source"])
    
    # Create candidate translation files
    if candidate_translations:
        candidate_dir = bundle_dir / "candidate_translations"
        candidate_dir.mkdir(exist_ok=True)
        for key, translation in candidate_translations.items():
            trans_path = candidate_dir / f"candidate_{key}.txt"
            with open(trans_path, "w", encoding="utf-8") as f:
                f.write(translation)
    
    # Create review template
    template_path = bundle_dir / "REVIEW_TEMPLATE.md"
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-S Human Literary Review Template

## Reviewer Information
- **Reviewer**: _________________
- **Date**: _________________
- **Candidate**: openai/gpt-oss-120b (NVIDIA hosted)
- **Session ID**: _________________

## Instructions

1. Read each source text carefully
2. Read the candidate translation (blind - you don't know which model)
3. Score each dimension 1-10
4. Provide specific examples for scores < 7
5. Overall weighted score >= 7.0 = PASS

## Source Texts

""")
        
        for name, fixture in fixtures.items():
            f.write(f"### {name.capitalize()} (Source)\n")
            f.write(f"{fixture['source']}\n\n")
        
        f.write("""## Candidate Translations (Blind)

[REVIEWER: Read translations without knowing which is which]

### Narrative - Base
[Translation A]

### Narrative - Glossary
[Translation B]

### Dialogue - Base
[Translation C]

### Dialogue - Glossary
[Translation D]

### Continuity - Base
[Translation E]

### Continuity - Glossary
[Translation F]

## Scoring Sheet

| Dimension | Weight | Score (1-10) | Notes |
|-----------|--------|--------------|-------|
| Semantic Accuracy | 15% | ___ | |
| Traditional Chinese Naturalness | 15% | ___ | |
| Literary Fluency | 10% | ___ | |
| Narrative Voice | 10% | ___ | |
| Character Voice | 10% | ___ | |
| Dialogue Naturalness | 10% | ___ | |
| Terminology Consistency | 10% | ___ | |
| Continuity | 10% | ___ | |
| No Major Omission | 5% | ___ | |
| No Major Hallucination | 5% | ___ | |
| **Weighted Total** | **100%** | **___** | |

## Critical Comments

[Required for any score < 7]

______________________________________________________________________________
______________________________________________________________________________
______________________________________________________________________________

## Overall Decision

- [ ] **PASS** (Weighted Total >= 7.0)
- [ ] **FAIL** (Weighted Total < 7.0)

**Reviewer Signature**: _________________
**Date**: _________________
""")
    
    # Create glossary reference
    glossary_path = bundle_dir / "glossary_reference.txt"
    with open(glossary_path, "w", encoding="utf-8") as f:
        f.write("Glossary Reference (must be followed exactly):\n\n")
        for k, v in sorted(glossary.items()):
            f.write(f"{k} → {v}\n")
    
    return bundle


def main():
    import datetime
    import subprocess
    
    print("=" * 70)
    print("P0-FINAL-15-S: Gate I — Human Literary Review Bundle")
    print("=" * 70)
    
    bundle = generate_human_review_bundle()
    
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    bundle_dir = artifacts_dir / "P0_FINAL_15_S_Human_Review_Bundle"
    
    print(f"\n[HUMAN_REVIEW] Bundle created at: {bundle_dir}")
    
    print("\n" + "=" * 70)
    print("GATE I — HUMAN LITERARY REVIEW BUNDLE")
    print("=" * 70)
    print(f"Bundle directory: {bundle_dir}")
    print("Contents:")
    for f in bundle_dir.iterdir():
        print(f"  {f.name}")
    
    print("\nNEXT STEPS:")
    print("1. Review the source texts in bundle directory")
    print("2. Read candidate translations (blind)")
    print("3. Complete REVIEW_TEMPLATE.md")
    print("4. Return completed review for final decision")
    
    print("\n" + "=" * 70)
    print("P0-FINAL-15-S Gate I Bundle Complete")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import datetime
    import subprocess
    sys.exit(main())
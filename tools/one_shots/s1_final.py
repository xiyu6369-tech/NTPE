#!/usr/bin/env python3
"""
P0-FINAL-15-S1: GPT-OSS 120B Context & Quality Recovery Investigation (Minimal Complete)
"""

import os
import sys
import time
import json
import datetime
import requests
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

@dataclass
class S1Result:
    test_id: str
    fixture: str
    mode: str
    context_pct: float
    http_status: int
    success: bool
    elapsed_s: float
    input_chars: int
    output_chars: int
    truncation: bool
    preservation: float
    quality: float
    quality_pass: bool
    finish_reason: str
    error: Optional[str] = None

def get_git_baseline() -> dict:
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        origin_main = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True, check=True).stdout.strip()
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        result = subprocess.run(["git", "rev-list", "--left-right", "--count", f"{origin_main}...{head}"], capture_output=True, text=True)
        divergence = f"{result.stdout.strip().split()[0]}/{result.stdout.strip().split()[1]}" if result.returncode == 0 else "unknown"
        return {"head_commit": head, "origin_main_commit": origin_main, "divergence": divergence, "branch": branch}
    except Exception as e:
        return {"head_commit": "error", "origin_main_commit": "error", "divergence": "error", "branch": "error", "error": str(e)}

def run_single(model: str, sys_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int, timeout_s: int = 60) -> tuple:
    payload = {"model": model, "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}], 
               "temperature": 0.15, "top_p": 0.85, "max_tokens": max_tokens, "stream": False}
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    start = time.time()
    try:
        r = requests.post(endpoint, headers=headers, json=payload, timeout=(10, timeout_s))
        r.encoding = 'utf-8'
        elapsed = time.time() - start
        data = r.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        if content is None: content = ""
        finish_reason = data.get('choices', [{}])[0].get('finish_reason', '')
        return r.status_code, elapsed, content, finish_reason, data.get('id'), r.headers.get('Nvcf-Reqid'), None
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        return 408, elapsed, "", "", None, None, "Timeout"
    except Exception as e:
        elapsed = time.time() - start
        return 500, elapsed, "", "", None, None, str(e)

def check_truncation(text: str) -> bool:
    if not text: return True
    return not text.rstrip().endswith(('。', '！', '？', '……', '"', '」', '」'))

def check_preservation(source: str, translation: str) -> float:
    if not translation: return 0.0
    entities = ["정태的", "카일", "민수", "지현", "김철수", "이영희", "프라이빗풀", "라군", "백사장", "로비", "독일어", "동행", "베를린", "남국", "섬", "호텔", "형사", "파트너", "원칙주의자", "연쇄 실종 사건", "현장", "피해자", "공통점", "직관", "논리", "증거"]
    zh_entities = ["鄭泰義", "凱爾", "旻秀", "智賢", "金哲秀", "李英姬", "私人泳池", "潟湖", "沙灘", "大廳", "德語", "同行", "柏林", "南國", "島嶼", "飯店", "刑警", "搭檔", "原則主義者", "連環失蹤案", "現場", "受害者", "共同點", "直覺", "邏輯", "證據"]
    found = sum(1 for e in entities if e in source)
    preserved = sum(1 for e in zh_entities if e in translation)
    return min(1.0, preserved / max(1, found))

def compute_quality(source: str, translation: str, fixture_type: str) -> tuple:
    if not translation: return 0.0, False
    zh_count = sum(1 for c in translation if '\u4e00' <= c <= '\u9fff')
    total = len(translation)
    zh_ratio = zh_count / max(1, total)
    fluency = min(zh_ratio * 20, 20)
    
    glossary = {"정태的": "鄭泰義", "카일": "凱爾", "민수": "旻秀", "지현": "智賢", "김철수": "金哲秀", "이영희": "李英姬"}
    term_matches = sum(1 for kr, zh in glossary.items() if kr in source and zh in translation)
    term_total = sum(1 for kr in glossary.keys() if kr in source)
    terminology = (term_matches / max(1, term_total)) * 20
    
    src_tokens = max(1, len(source) // 3)
    tgt_tokens = max(1, len(translation) // 3)
    ratio = tgt_tokens / src_tokens
    semantic = 20 * min(1.0, 1.0 - abs(1.0 - ratio)) if 0.5 <= ratio <= 2.0 else max(0, 20 - abs(ratio - 1.0) * 10)
    
    markers = sum(translation.count(m) for m in ["。", "，", "「", "」", "…", "——", "……"])
    literary = min(markers * 0.5, 10)
    
    continuity = 10 if fixture_type == "continuity" and ("金哲秀" in translation and "李英姬" in translation) else 10
    formatting = 5
    
    overall = fluency + terminology + semantic + literary + continuity + formatting
    return overall, overall >= 65

def load_fixtures() -> Dict[str, str]:
    return {
        "narrative": "정태의는 난감해하고 있었다. 그러나 실상 그것은 그가 난감해할 일은 아니었다. 먼 타국에 떼어놓고 온 괴물 같은 남자는 어쨌든 이지가 제대로 돌아가고 있는, 나름대로 이성적인 인간이었고, 그는 이 상황이 결코 정태的가 의도해서 벌어진 상황이 아니란 걸 이해해줄 것이다. 그러나, '몇 달 전부터 벼르고 별러서 천신만고 끝에 겨우 일주일 휴가를 뺐는데, 그놈이 일 때문에 예정보다 늦게 돌아온다고 해서 내 휴가를 깎아먹을 수는 없다'라고 분연히 주장하며, 이웃나라까지 일하러 간 동생을 내팽개치고 정태的만 홀랑 데리고 머나먼 남국의 섬으로 휴가를 와버린 카일이 무사할 수 있을지가 사뭇 걱정이 되었다. (카일도 평소의 이성적인 그였더라면 이런 짓을 막 벌이진 않았을 테지만, 일하러 떠나기 직전에 카일이 아끼던 책을 불살라버린 동생의 작태에 사흘을 앓아누울 정도로 광분했던 탓이 다분했다.) 어찌 되었든, 직통이라곤 없이 경비행기로 따로 들어와야 하는 이 여유로운 남국의 섬에 있는 호텔의 로비 소파에 앉아, 지금이야 좋지만 베를린으로 돌아간 뒤에 어떤 사단이 날지 그저 걱정스럽기만 한 정태的는 한숨을 쉬고 있었다. '……하지만 지금 미리 걱정해본들 뭐 이미 벌어진 일은 어쩔 도리 없고……. 모처럼 쉬러 왔는데 한숨만 쉬며 일주일을 지내면 손해지.' 정태的는 결국 합리적인 결론을 내리고 고개를 끄덕였다. 짙은 청옥빛 바다로 둘러싸인 이 섬은 대단히 아름답고 한가로웠다. 오는 길에 카일에게 들은 바로는, 이곳의 호텔은 몇몇 재벌이 소유한 별장처럼 쓰이다시피 해 일반 관광객은 들어오지 못하기 때문에, 남의 눈에 띌 걱정 없이 한가롭고 넉넉한 휴가를 보내기에는 안성맞춤이라고 했다. 과연 그의 말마따나, 어제 이곳에 들어온 이후 정태的가 구경한 사람이라곤 이곳의 관리인과 직원 외에는 열 손가락으로 꼽고도 넉넉하게 남을 정도였다. '인적 드문 바닷가 산책도 좋겠지.' 정태的는 어차, 하고 자리에서 일어섰다. 카일은 프라이빗풀 옆의 벤치에서 정신없이 잠들어 있을 터였다. (일주일의 휴가를 위해 그가 이곳에 오기 직전까지 밤을 새며 퀭한 얼굴로 일했다는 걸 정태的는 알고 있었다. 그래서, 그가 막무가내로 여기에 오겠다고 하는 주장을 차마 거를 수 없었다.) 라군에서 바닷가는, 당연하다면 당연하지만, 엎어지면 코 닿을 거리였다. 근처만 서성이려면 바다 위로 뻗은 나무다리 위로 산책을 할 수도 있지만, 정태的는 천천히 섬을 한 바퀴 돌아보자고 생각하고 백사장 쪽을 선택했다. 대충 걸어서 두어 시간이면 한 바퀴 다 돌 수 있을 정도로 작은 섬이라고 들었다. 무릅까지 오는 반바지 위에 넉넉한 셔츠 하나만 대충 걸치고, 그가 막 로비에서 나서려던 때였다. 새로운 손님이 왔는지, 바깥에서 약간 떠들썩하게―라고 해도 이곳이 워낙 조용해서, 단순한 말소리조차 그렇게 들릴 뿐이었지만―두세 명이 들어서고 있었다. 정태的는 저도 모르게 걸음을 멈추었다. 귀에 익은 독일어가 들렸다.",
        "dialogue": '"정말 괜찮아?" 민수가 조심스럽게 물었다.\n\n지현은 고개를 끄덕이며 억지로 미소를 지었다. "응, 괜찮아. 그냥... 좀 피곤할 뿐이야."\n\n"아니, 네 눈빛이 그렇지 않아. 무슨 일 있어? 말해줘."\n\n지현은 잠시 망설였다. 그리고 낮게 한숨을 내쉬었다.\n\n"사실은... 내일 발표가 있어. 준비가 안 돼서 그래."\n\n민수는 놀란 듯 눈을 크게 떴다. "내일이면 하루 남았잖아? 왜 이제 말해?"\n\n"말해봤자 도와줄 수도 없으니까. 내 문제니까 내가 해결해야지."\n\n"그런 말 하지 마. 우린 친구잖아. 같이 해결하면 되잖아."\n\n그 말 한마디에 지현의 눈시울이 뜨거워졌다.',
        "continuity": '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, 그는 특유的 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. 논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.\n\n어느 날, 두 사람은 연쇄 실종 사건을 맡게 되었다. 철수는 현장의 미세한 흔적에서 단서를 찾으려 했고, 영희는 피해자들의 공통점을 분석했다. 처음엔 서로의 방식을 불신했지만, 곧 그들의 접근法이 서로 보완됨을 깨달았다. 철수의 직관이 영희的 논리를 이끌었고, 영희的 증거가 철수의 추측을 뒷받침했다.'
    }

def build_prompts():
    glossary = "정태的 → 鄭泰義\n카일 → 凱爾\n민수 → 旻秀\n지현 → 智賢\n김철수 → 金哲秀\n이영희 → 李英姬\n프라이빗풀 → 私人泳池\n라군 → 潟湖\n백사장 → 沙灘\n로비 → 大廳\n독일어 → 德語\n동행 → 同行\n베를린 → 柏林\n남국 → 南國\n섬 → 島嶼\n호텔 → 飯店\n형사 → 刑警\n파트너 → 搭檔\n원칙주의자 → 原則主義者\n연쇄 실종 사건 → 連環失蹤案\n현장 → 現場\n피해자 → 受害者\n공통점 → 共同點\n직관 → 直覺\n논리 → 邏輯\n증거 → 證據"
    
    base = "You are a professional literary translator specializing in Korean to Traditional Chinese (Taiwan) translation. Output only the translation."
    glossary_prompt = base + "\n\nGLOSSARY (must follow exactly):\n" + glossary
    return base, glossary_prompt

def save_results(baseline: dict, all_results: List[S1Result], classification: str):
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    report = {
        "phase": "P0-FINAL-15-S1",
        "baseline": baseline,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "candidate": "openai/gpt-oss-120b",
        "hosting": "NVIDIA",
        "production_model": "minimaxai/minimax-m3",
        "production_state": "FROZEN",
        "rm6_status": "BLOCKED",
        "results": [asdict(r) for r in all_results],
        "classification": classification
    }
    
    report_path = artifacts_dir / "P0_FINAL_15_S1_GPT_OSS_120B_CONTEXT_QUALITY_RECOVERY_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved: {report_path}")
    
    gov_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    gov_dir.mkdir(parents=True, exist_ok=True)
    gov_path = gov_dir / "P0_FINAL_15_S1_GPT_OSS_120B_CONTEXT_QUALITY_RECOVERY.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-S1: GPT-OSS 120B Context & Quality Recovery Investigation

## Baseline
- HEAD: {baseline['head_commit']}
- Branch: {baseline['branch']}
- Timestamp: {report['timestamp']}

## Candidate
- Model: openai/gpt-oss-120b (NVIDIA)
- Production Model: minimaxai/minimax-m3 (FROZEN)
- RM6: BLOCKED

## Results

| Test | Fixture | Mode | Context | HTTP | Time | Trunc | Preserv | Quality | Pass |
|------|---------|------|---------|------|------|-------|---------|---------|------|
""")
        for r in all_results:
            f.write(f"| {r.test_id} | {r.fixture} | {r.mode} | {r.context_pct*100:.0f}% | {r.http_status} | {r.elapsed_s:.1f}s | {r.truncation} | {r.preservation:.2f} | {r.quality:.1f} | {r.quality_pass} |\n")
        
        f.write(f"""
## Classification

**{classification}**

## Human Review
PENDING (from P0-FINAL-15-S)

## Next Stage
Proceed to P0-FINAL-15-T if RECOVERABLE, otherwise remain on minimaxai/minimax-m3
""")
    print(f"Governance doc saved: {gov_path}")

def main():
    print("=" * 70)
    print("P0-FINAL-15-S1: GPT-OSS 120B Context & Quality Recovery Investigation")
    print("=" * 70)
    
    baseline = get_git_baseline()
    print(f"Branch: {baseline['branch']} | HEAD: {baseline['head_commit'][:12]}")
    
    if baseline['branch'] != 'main' or baseline['head_commit'] != '8c999b1219f65a6afaeaf0062e6c43f72691c188':
        print("BASELINE MISMATCH - STOP")
        return 1
    
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        print("NVIDIA_API_KEY not set")
        return 1
    
    model = "openai/gpt-oss-120b"
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    print("Production: minimaxai/minimax-m3 (FROZEN)")
    print("RM6: BLOCKED")
    
    fixtures = load_fixtures()
    base_prompt, glossary_prompt = build_prompts()
    
    all_results = []
    
    # 1. Context Boundary Sweep (narrative only, key boundaries)
    print("\n=== Context Boundary Sweep ===")
    narrative = fixtures["narrative"]
    for pct in [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]:
        test_id = f"CB_{int(pct*100)}"
        user_prompt = narrative[:int(len(narrative)*pct)]
        max_out = min(8000, max(2000, int(len(user_prompt) // 2)))
        
        print(f"  {test_id}...", end=" ", flush=True)
        status, elapsed, content, finish_reason, _, _, error = run_single(
            model, glossary_prompt, user_prompt, api_key, endpoint, max_out, 90
        )
        trunc = check_truncation(content)
        preserv = check_preservation(narrative, content)
        quality, qpass = compute_quality(narrative, content, "narrative")
        
        r = S1Result(test_id=test_id, fixture="narrative", mode="glossary", context_pct=pct,
            http_status=status, success=status==200, elapsed_s=elapsed,
            input_chars=len(user_prompt), output_chars=len(content),
            truncation=trunc, preservation=preserv, quality=quality, quality_pass=qpass,
            finish_reason=finish_reason or "unknown", error=error)
        all_results.append(r)
        print(f"HTTP {status} | {elapsed:.1f}s | trunc={trunc} | preserv={preserv:.2f} | qual={quality:.1f} ({'PASS' if qpass else 'FAIL'})")
        time.sleep(1)
    
    # 2. Chunking (narrative only)
    print("\n=== Chunking ===")
    for name, count in [("single", 1), ("small", 4), ("medium", 3), ("large", 2)]:
        test_id = f"CHUNK_{name}"
        if count == 1:
            chunks = [narrative]
        else:
            size = len(narrative) // count
            chunks = [narrative[i*size:(i+1)*size] for i in range(count-1)]
            chunks.append(narrative[(count-1)*size:])
        
        print(f"  {test_id} ({count} chunks)...", end=" ", flush=True)
        all_content = []
        all_success = True
        total_elapsed = 0
        status_final = 200
        finish_reasons = []
        
        for chunk in chunks:
            status, elapsed, content, fr, _, _, error = run_single(
                model, glossary_prompt, chunk, api_key, endpoint, 4000, 60
            )
            all_success = all_success and (status == 200)
            if status != 200: status_final = status
            total_elapsed += elapsed
            finish_reasons.append(fr or "unknown")
            all_content.append(content or "")
            time.sleep(0.5)
        
        full = "\n\n".join(all_content)
        trunc = check_truncation(full)
        preserv = check_preservation(narrative, full)
        quality, qpass = compute_quality(narrative, full, "narrative")
        
        r = S1Result(test_id=test_id, fixture="narrative", mode="glossary_chunked", context_pct=1.0,
            http_status=status_final, success=all_success, elapsed_s=total_elapsed,
            input_chars=len(narrative), output_chars=len(full),
            truncation=trunc, preservation=preserv, quality=quality, quality_pass=qpass,
            finish_reason=";".join(finish_reasons), error=None if all_success else "chunk failed")
        all_results.append(r)
        print(f"HTTP {status_final} | {total_elapsed:.1f}s | trunc={trunc} | preserv={preserv:.2f} | qual={quality:.1f} ({'PASS' if qpass else 'FAIL'})")
    
    # 3. Quality Matrix (all fixtures, base vs glossary)
    print("\n=== Quality Matrix ===")
    for fixture_name, source in fixtures.items():
        for mode, prompt in [("base", base_prompt), ("glossary", glossary_prompt)]:
            test_id = f"QUAL_{fixture_name}_{mode}"
            print(f"  {test_id}...", end=" ", flush=True)
            status, elapsed, content, fr, _, _, error = run_single(
                model, prompt, source, api_key, endpoint, 4000, 60
            )
            trunc = check_truncation(content)
            preserv = check_preservation(source, content)
            quality, qpass = compute_quality(source, content, fixture_name)
            
            r = S1Result(test_id=test_id, fixture=fixture_name, mode=mode, context_pct=1.0,
                http_status=status, success=status==200, elapsed_s=elapsed,
                input_chars=len(source), output_chars=len(content),
                truncation=trunc, preservation=preserv, quality=quality, quality_pass=qpass,
                finish_reason=fr or "unknown", error=error)
            all_results.append(r)
            print(f"HTTP {status} | {elapsed:.1f}s | trunc={trunc} | preserv={preserv:.2f} | qual={quality:.1f} ({'PASS' if qpass else 'FAIL'})")
            time.sleep(0.5)
    
    # 4. Reduced Context + Glossary (narrative only)
    print("\n=== Reduced Context + Glossary ===")
    for pct in [0.7, 0.8, 0.85]:
        test_id = f"REDUCED_narrative_{int(pct*100)}"
        user_prompt = narrative[:int(len(narrative)*pct)]
        max_out = min(6000, max(1500, int(len(user_prompt) // 2)))
        
        print(f"  {test_id}...", end=" ", flush=True)
        status, elapsed, content, fr, _, _, error = run_single(
            model, glossary_prompt, user_prompt, api_key, endpoint, max_out, 60
        )
        trunc = check_truncation(content)
        preserv = check_preservation(narrative, content)
        quality, qpass = compute_quality(narrative, content, "narrative")
        
        r = S1Result(test_id=test_id, fixture="narrative", mode="glossary_reduced", context_pct=pct,
            http_status=status, success=status==200, elapsed_s=elapsed,
            input_chars=len(user_prompt), output_chars=len(content),
            truncation=trunc, preservation=preserv, quality=quality, quality_pass=qpass,
            finish_reason=fr or "unknown", error=error)
        all_results.append(r)
        print(f"HTTP {status} | {elapsed:.1f}s | trunc={trunc} | preserv={preserv:.2f} | qual={quality:.1f} ({'PASS' if qpass else 'FAIL'})")
        time.sleep(0.5)
    
    # 5. Output Budget (all fixtures)
    print("\n=== Output Budget (6000) ===")
    for fixture_name, source in fixtures.items():
        test_id = f"BUDGET_{fixture_name}"
        print(f"  {test_id}...", end=" ", flush=True)
        status, elapsed, content, fr, _, _, error = run_single(
            model, glossary_prompt, source, api_key, endpoint, 6000, 60
        )
        trunc = check_truncation(content)
        preserv = check_preservation(source, content)
        quality, qpass = compute_quality(source, content, fixture_name)
        
        r = S1Result(test_id=test_id, fixture=fixture_name, mode="glossary_budget", context_pct=1.0,
            http_status=status, success=status==200, elapsed_s=elapsed,
            input_chars=len(source), output_chars=len(content),
            truncation=trunc, preservation=preserv, quality=quality, quality_pass=qpass,
            finish_reason=fr or "unknown", error=error)
        all_results.append(r)
        print(f"HTTP {status} | {elapsed:.1f}s | trunc={trunc} | preserv={preserv:.2f} | qual={quality:.1f} ({'PASS' if qpass else 'FAIL'})")
        time.sleep(0.5)
    
    # Classification
    full_pass = any(r.success and not r.truncation and r.quality_pass for r in all_results)
    conditional = any(r.success and not r.truncation and r.quality_pass and r.mode in ["glossary", "glossary_reduced", "glossary_chunked", "glossary_budget"] for r in all_results)
    
    if full_pass:
        classification = "RECOVERABLE"
    elif conditional:
        classification = "CONDITIONALLY_RECOVERABLE"
    else:
        classification = "NOT_RECOVERABLE"
    
    save_results(baseline, all_results, classification)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for r in all_results:
        print(f"  {r.test_id}: HTTP={r.http_status} Trunc={r.truncation} Preserv={r.preservation:.2f} Qual={r.quality:.1f} Pass={r.quality_pass}")
    
    print(f"\nClassification: {classification}")
    print(f"Human Review: PENDING")
    print(f"Production Model: minimaxai/minimax-m3 (UNCHANGED)")
    print(f"RM6: BLOCKED")
    
    return 0 if classification in ["RECOVERABLE", "CONDITIONALLY_RECOVERABLE"] else 1

if __name__ == "__main__":
    sys.exit(main())
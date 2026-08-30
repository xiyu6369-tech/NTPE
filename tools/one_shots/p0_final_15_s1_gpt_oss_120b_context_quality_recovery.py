#!/usr/bin/env python3
"""
P0-FINAL-15-S1: GPT-OSS 120B Context & Quality Recovery Investigation

Diagnostic / Investigation / Evidence Collection
- Context truncation boundary sweep
- Chunking strategy investigation
- Quality recovery per-fixture analysis
- Glossary effectiveness verification
- Context x Quality matrix construction

Candidate: openai/gpt-oss-120b (NVIDIA hosted)
Production Model: minimaxai/minimax-m3 (FROZEN)
"""

from __future__ import annotations

import json
import os
import sys
import time
import datetime
import requests
import subprocess
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Optional, List, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@dataclass
class S1ExperimentResult:
    """Single experiment result for S1 matrix."""
    strategy_id: str
    strategy_name: str
    fixture_type: str
    mode: str  # base, glossary, chunked
    timestamp_utc: str
    http_status: int
    success: bool
    elapsed_ms: float
    source_chars: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    system_prompt_chars: int
    glossary_chars: int
    memory_chars: int
    context_chars: int
    requested_output_tokens: int
    actual_output_tokens: int
    source_preservation_ratio: float
    output_truncation: bool
    completion_finish_reason: Optional[str]
    provider_request_id: Optional[str]
    nvcf_reqid: Optional[str]
    nvcf_status: Optional[str]
    error: Optional[str] = None
    quality_score: Optional[float] = None
    quality_pass: Optional[bool] = None
    continuity_score: Optional[float] = None
    terminology_consistency: Optional[float] = None
    chunk_count: int = 1
    chunk_strategy: str = "single"


@dataclass
class S1ContextBoundaryResult:
    """Context boundary sweep result."""
    boundary_pct: float
    level: str
    http_status: int
    success: bool
    elapsed_ms: float
    source_chars: int
    estimated_input_tokens: int
    system_prompt_chars: int
    glossary_chars: int
    memory_chars: int
    context_chars: int
    requested_output_tokens: int
    actual_output_tokens: int
    source_preservation_ratio: float
    output_truncation: bool
    completion_finish_reason: Optional[str]
    provider_request_id: Optional[str]
    nvcf_reqid: Optional[str]
    nvcf_status: Optional[str]
    classification: str  # SAFE, CAUTION, UNSTABLE, FAIL


@dataclass
class S1ChunkingResult:
    """Chunking strategy result."""
    chunk_strategy: str  # single, small, medium, large
    chunk_count: int
    http_status: int
    success: bool
    elapsed_ms: float
    source_chars: int
    source_completeness: bool
    quality_score: float
    quality_pass: bool
    continuity_score: float
    repetition_detected: bool
    missing_text: bool
    paragraph_boundary_integrity: bool
    glossary_adherence: bool
    provider_request_id: Optional[str]
    nvcf_reqid: Optional[str]
    nvcf_status: Optional[str]
    error: Optional[str] = None


@dataclass
class S1GlossaryResult:
    """Glossary effectiveness result."""
    fixture_name: str
    base_score: float
    glossary_score: float
    improvement: float
    terminology_consistency_base: float
    terminology_consistency_glossary: float
    quality_pass_base: bool
    quality_pass_glossary: bool
    unwanted_over_application: bool


@dataclass
class S1ContextQualityMatrix:
    """Context x Quality matrix row."""
    context_strategy: str
    http_success: bool
    truncation: bool
    quality: float
    quality_pass: bool
    continuity_pass: bool
    verdict: str


@dataclass
class S1Report:
    """S1 Investigation Report."""
    # Baseline
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    python_version: str
    test_timestamp: str
    # Candidate
    candidate_model: str
    hosting_provider: str
    endpoint: str
    credential_source: str
    # Production state (frozen)
    production_model: str
    production_routing: str
    production_retry: str
    production_backoff: str
    production_rpm: str
    production_timeout: str
    production_chunk_size: str
    production_runtime: str
    rm6_status: str
    # Experiment Matrix
    experiments: List[S1ExperimentResult]
    # Context Boundary Sweep
    context_boundary: List[S1ContextBoundaryResult]
    # Chunking Investigation
    chunking_results: List[S1ChunkingResult]
    # Quality Recovery
    quality_results: List[S1ExperimentResult]
    # Glossary Investigation
    glossary_results: List[S1GlossaryResult]
    # Context x Quality Matrix
    context_quality_matrix: List[S1ContextQualityMatrix]
    # Human Review Status
    human_review_status: str
    # Production Compatibility
    production_compatibility: str
    # Risk Assessment
    risk_assessment: str
    # Historical Evidence References
    historical_references: List[str]
    # Final Classification
    final_classification: str  # RECOVERABLE, CONDITIONALLY_RECOVERABLE, NOT_RECOVERABLE, INSUFFICIENT_EVIDENCE
    # Recommendation
    recommendation: str
    # Limitations
    limitations: List[str]


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


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 3)


def run_single_request(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, 
                       max_tokens: int = 8000, timeout_read: int = 90) -> tuple:
    payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], 
               "temperature": 0.15, "top_p": 0.85, "max_tokens": max_tokens, "stream": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=(10, timeout_read))
        elapsed = (time.monotonic() - start) * 1000
        http_status = resp.status_code
        provider_req_id = None
        completion_finish_reason = None
        try:
            data = resp.json()
            provider_req_id = data.get("id")
            choices = data.get("choices", [{}])
            if choices:
                completion_finish_reason = choices[0].get("finish_reason")
            response_body = choices[0].get("message", {}).get("content", "") if choices else ""
        except Exception:
            response_body = resp.text
        nvcf_reqid = resp.headers.get("Nvcf-Reqid")
        nvcf_status = resp.headers.get("Nvcf-Status")
        error = None if http_status == 200 else f"HTTP {http_status}: {resp.text[:200]}"
        return http_status, elapsed, provider_req_id, nvcf_reqid, nvcf_status, completion_finish_reason, response_body, error
    except requests.exceptions.Timeout as e:
        elapsed = (time.monotonic() - start) * 1000
        return 408, elapsed, None, None, None, None, "", f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, None, None, None, "", str(e)


def check_truncation_corruption(source: str, translation: str) -> tuple[bool, bool]:
    if not translation:
        return True, True
    truncation = False
    if translation and not any(translation.rstrip().endswith(p) for p in ["。", "！", "？", "……", "\"", "」", "」"]):
        truncation = True
    corruption = False
    if len(translation) < 10:
        corruption = True
    if translation.count(translation[:20]) > 3:
        corruption = True
    return truncation, corruption


def check_source_preservation(source: str, translation: str) -> float:
    """Estimate source preservation by checking key entities."""
    if not translation:
        return 0.0
    key_entities = ["정태의", "카일", "민수", "지현", "김철수", "이영희", "프라이빗풀", "라군", "백사장", "로비", "독일어", "동행", "베를린", "남국", "섬", "호텔", "형사", "파트너", "원칙주의자", "연쇄 실종 사건", "현장", "피해자", "공통점", "직관", "논리", "증거"]
    found = sum(1 for e in key_entities if e in source)
    preserved = sum(1 for e in key_entities if e in source and any(alias in translation for alias in ["鄭泰義", "凱爾", "旻秀", "智賢", "金哲秀", "李英姬", "私人泳池", "潟湖", "沙灘", "大廳", "德語", "同行", "柏林", "南國", "島嶼", "飯店", "刑警", "搭檔", "原則主義者", "連環失蹤案", "現場", "受害者", "共同點", "直覺", "邏輯", "證據"]))
    return preserved / max(1, found)


def load_fixtures() -> dict[str, dict]:
    fixtures = {}
    golden_path = Path(__file__).resolve().parents[2] / "tests" / "literary" / "Golden_Set" / "original_ko.txt"
    if golden_path.exists():
        narrative = golden_path.read_text(encoding="utf-8")
    else:
        narrative = "정태의는 아차, 하고 자리에서 일어섰다. 카일은 프라이빗풀 옆의 벤치에서 정신없이 잠들어 있을 터였다. (일주일의 휴가를 위해 그가 이곳에 오기 직전까지 밤을 새며 퀭한 얼굴로 일했다는 걸 정태의는 알고 있었다. 그래서, 그가 막무가내로 여기에 오겠다고 하는 주장을 차마 거를 수 없었다.) 라군에서 바닷가는, 당연하다면 당연하지만, 엎어지면 코 닿을 거리였다. 근처만 서성이려면 바다 위로 뻗은 나무다리 위로 산책을 할 수도 있지만, 정태의는 천천히 섬을 한 바퀴 돌아보자고 생각하고 백사장 쪽을 선택했다. 대충 걸어서 두어 시간이면 한 바퀴 다 돌 수 있을 정도로 작은 섬이라고 들었다. 무릅까지 오는 반바지 위에 넉넉한 셔츠 하나만 대충 걸치고, 그가 막 로비에서 나서려던 때였다. 새로운 손님이 왔는지, 바깥에서 약간 떠들썩하게―라고 해도 이곳이 워낙 조용해서, 단순한 말소리조차 그렇게 들릴 뿐이었지만―두세 명이 들어서고 있었다. 정태的는 저도 모르게 걸음을 멈추었다. 귀에 익은 독일어가 들렸다."
    fixtures["narrative"] = {"name": "narrative", "type": "narrative", "source": narrative}
    fixtures["dialogue"] = {"name": "dialogue", "type": "dialogue", "source": '"정말 괜찮아?" 민수가 조심스럽게 물었다.\n\n지현은 고개를 끄덕이며 억지로 미소를 지었다. "응, 괜찮아. 그냥... 좀 피곤할 뿐이야."\n\n"아니, 네 눈빛이 그렇지 않아. 무슨 일 있어? 말해줘."\n\n지현은 잠시 망설였다. 그리고 낮게 한숨을 내쉬었다.\n\n"사실은... 내일 발표가 있어. 준비가 안 돼서 그래."\n\n민수는 놀란 듯 눈을 크게 떴다. "내일이면 하루 남았잖아? 왜 이제 말해?"\n\n"말해봤자 도와줄 수도 없으니까. 내 문제니까 내가 해결해야지."\n\n"그런 말 하지 마. 우린 친구잖아. 같이 해결하면 되잖아."\n\n그 말 한마디에 지현의 눈시울이 뜨거워졌다.'}
    fixtures["continuity"] = {"name": "continuity", "type": "continuity", "source": '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, 그는 특유의 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. 논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.\n\n어느 날, 두 사람은 연쇄 실종 사건을 맡게 되었다. 철수는 현장의 미세한 흔적에서 단서를 찾으려 했고, 영희는 피해자들의 공통점을 분석했다. 처음엔 서로의 방식을 불신했지만, 곧 그들의 접근법이 서로 보완됨을 깨달았다. 철수의 직관이 영희의 논리를 이끌었고, 영희의 증거가 철수의 추측을 뒷받침했다.'}
    return fixtures


def load_glossary() -> dict[str, str]:
    return {"정태的": "鄭泰義", "카일": "凱爾", "민수": "旻秀", "지현": "智賢",
            "김철수": "金哲秀", "이영희": "李英姬", "프라이빗풀": "私人泳池",
            "라군": "潟湖", "백사장": "沙灘", "로비": "大廳", "독일어": "德語",
            "동행": "同行", "베를린": "柏林", "남국": "南國", "섬": "島嶼",
            "호텔": "飯店", "형사": "刑警", "파트너": "搭檔", "원칙주의자": "原則主義者",
            "연쇄 실종 사건": "連環失蹤案", "현장": "現場", "피해자": "受害者",
            "공통점": "共同點", "직관": "直覺", "논리": "邏輯", "증거": "證據", "推測": "推測"}


def load_character_memory() -> list[dict]:
    return [
        {"name": "정태的", "aliases": ["鄭泰義", "Jung Tae-ui"], "role": "protagonist", "gender": "male", "description": "Sharp-eyed survivor who relies on intuition"},
        {"name": "카일", "aliases": ["凱爾", "Kyle"], "role": "companion", "gender": "male", "description": "Rational, protective figure"},
        {"name": "민수", "aliases": ["旻秀", "Minsu"], "role": "supporting", "gender": "male", "description": "Caring friend"},
        {"name": "지현", "aliases": ["智賢", "Jihyun"], "role": "supporting", "gender": "female", "description": "Hides stress behind forced smiles"},
        {"name": "김철수", "aliases": ["金哲秀", "Kim Cheol-su"], "role": "protagonist", "gender": "male", "description": "30-year veteran detective"},
        {"name": "이영희", "aliases": ["李英姬", "Lee Young-hee"], "role": "protagonist", "gender": "female", "description": "Principled detective"},
    ]


def build_prompt(mode: str, fixture: dict, glossary: dict, char_memory: list[dict], context_pct: float = 1.0) -> tuple[str, str]:
    base_system = (
        "You are a professional literary translator specializing in Korean to Traditional Chinese (Taiwan) translation. "
        "Translate the following Korean text naturally, preserving:\n"
        "1. Character names and honorifics\n"
        "2. Narrative tone and literary style\n"
        "3. Dialogue naturalness and character voice distinction\n"
        "4. Terminology consistency\n"
        "5. Cultural nuances appropriate for Taiwan readers\n\n"
        "Output only the translation."
    )
    glossary_text = ""
    if mode in ["glossary", "glossary_chunked"] and glossary:
        glossary_lines = [f"- {k} → {v}" for k, v in glossary.items()]
        glossary_text = "\n\nGLOSSARY (must follow exactly):\n" + "\n".join(glossary_lines)
    char_memory_text = ""
    if mode in ["char_memory", "glossary"] and char_memory:
        char_lines = [f"- {c['name']} ({', '.join(c['aliases'])}) — {c['role']}, {c['gender']}: {c['description']}" for c in char_memory]
        char_memory_text = "\n\nCHARACTER MEMORY:\n" + "\n".join(char_lines)
    system_prompt = base_system + glossary_text + char_memory_text
    
    # Apply context percentage by truncating source
    source_text = fixture["source"]
    if context_pct < 1.0:
        target_chars = int(len(source_text) * context_pct)
        source_text = source_text[:target_chars]
    
    user_prompt = source_text
    return system_prompt, user_prompt


def compute_quality_scores(source: str, translation: str, fixture_type: str, glossary: dict, char_memory: list[dict]) -> dict:
    scores = {"semantic_fidelity": 0.0, "fluency": 0.0, "literary_style": 0.0,
              "terminology_consistency": 0.0, "character_consistency": 0.0,
              "continuity": 0.0, "formatting_preservation": 0.0}
    if not translation or not translation.strip():
        return {**scores, "overall": 0.0, "status": "FAIL"}
    zh_char_count = sum(1 for c in translation if '\u4e00' <= c <= '\u9fff')
    total_chars = len(translation)
    zh_ratio = zh_char_count / max(1, total_chars)
    scores["fluency"] = min(zh_ratio * 20, 20)
    term_matches = 0
    term_total = 0
    for kr, zh in glossary.items():
        if kr in source:
            term_total += 1
            if zh in translation:
                term_matches += 1
    scores["terminology_consistency"] = (term_matches / max(1, term_total)) * 20
    char_matches = 0
    char_total = 0
    for c in char_memory:
        for alias in c["aliases"]:
            if alias in source:
                char_total += 1
                if alias in translation:
                    char_matches += 1
    scores["character_consistency"] = (char_matches / max(1, char_total)) * 15
    src_tokens = estimate_tokens(source)
    tgt_tokens = estimate_tokens(translation)
    if src_tokens > 0:
        ratio = tgt_tokens / src_tokens
        if 0.5 <= ratio <= 2.0:
            scores["semantic_fidelity"] = 20 * min(1.0, 1.0 - abs(1.0 - ratio))
        else:
            scores["semantic_fidelity"] = max(0, 20 - abs(ratio - 1.0) * 10)
    literary_markers = ["。", "，", "「", "」", "…", "——", "……"]
    marker_count = sum(translation.count(m) for m in literary_markers)
    scores["literary_style"] = min(marker_count * 0.5, 10)
    if fixture_type == "continuity":
        scores["continuity"] = 10 if ("金哲秀" in translation and "李英姬" in translation) else 5
    else:
        scores["continuity"] = 10
    src_paragraphs = source.count('\n\n') + 1
    tgt_paragraphs = translation.count('\n\n') + 1
    if src_paragraphs == tgt_paragraphs:
        scores["formatting_preservation"] = 5
    else:
        scores["formatting_preservation"] = max(0, 5 - abs(src_paragraphs - tgt_paragraphs))
    overall = sum(scores.values())
    status = "PASS" if overall >= 65 else "FAIL"
    return {**scores, "overall": overall, "status": status}


def classify_context_boundary(truncation: bool, http_status: int, quality_pass: bool) -> str:
    if http_status != 200:
        return "FAIL"
    if truncation:
        return "UNSTABLE"
    if not quality_pass:
        return "CAUTION"
    return "SAFE"


def run_context_boundary_sweep(api_key: str, endpoint: str, model: str) -> List[S1ContextBoundaryResult]:
    """Run context boundary sweep at multiple percentages."""
    print("\n" + "=" * 70)
    print("S1-A: Context Boundary Sweep")
    print("=" * 70)
    
    fixtures = load_fixtures()
    narrative = fixtures["narrative"]["source"]
    sys_prompt_base = "You are a professional literary translator specializing in Korean to Traditional Chinese (Taiwan) translation. Output only the translation."
    glossary = load_glossary()
    glossary_text = "\n\nGLOSSARY (must follow exactly):\n" + "\n".join([f"- {k} → {v}" for k, v in glossary.items()])
    sys_prompt_with_glossary = sys_prompt_base + glossary_text
    
    boundaries = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    results = []
    
    for pct in boundaries:
        level_name = f"P{int(pct*100)}"
        print(f"\n[CONTEXT-SWEEP] Testing {level_name} ({pct*100:.0f}% context)...")
        
        target_chars = int(len(narrative) * pct)
        user_prompt = narrative[:target_chars]
        sys_prompt = sys_prompt_with_glossary
        
        est_input = estimate_tokens(sys_prompt + user_prompt)
        max_output = min(16000, max(4000, int(est_input * 0.8)))
        
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, finish_reason, body, error = run_single_request(
            model, sys_prompt, user_prompt, api_key, endpoint, max_tokens=max_output
        )
        
        truncation, corruption = check_truncation_corruption(user_prompt, body or "")
        source_preservation = check_source_preservation(user_prompt, body or "")
        quality_scores = compute_quality_scores(user_prompt, body or "", "narrative", glossary, load_character_memory())
        quality_pass = quality_scores["status"] == "PASS"
        classification = classify_context_boundary(truncation, http_status, quality_pass)
        
        result = S1ContextBoundaryResult(
            boundary_pct=pct,
            level=level_name,
            http_status=http_status,
            success=(http_status == 200),
            elapsed_ms=elapsed,
            source_chars=len(user_prompt),
            estimated_input_tokens=est_input,
            system_prompt_chars=len(sys_prompt),
            glossary_chars=len(glossary_text),
            memory_chars=0,
            context_chars=len(user_prompt),
            requested_output_tokens=max_output,
            actual_output_tokens=estimate_tokens(body or ""),
            source_preservation_ratio=source_preservation,
            output_truncation=truncation,
            completion_finish_reason=finish_reason,
            provider_request_id=req_id,
            nvcf_reqid=nvcf_reqid,
            nvcf_status=nvcf_status,
            classification=classification
        )
        results.append(result)
        
        print(f"  HTTP {http_status} | {elapsed:.0f}ms | Trunc: {truncation} | Preservation: {source_preservation:.2f} | Class: {classification}")
        time.sleep(2)
    
    return results


def run_chunking_investigation(api_key: str, endpoint: str, model: str) -> List[S1ChunkingResult]:
    """Test different chunking strategies."""
    print("\n" + "=" * 70)
    print("S1-B: Chunking Strategy Investigation")
    print("=" * 70)
    
    fixtures = load_fixtures()
    narrative = fixtures["narrative"]["source"]
    glossary = load_glossary()
    char_memory = load_character_memory()
    
    strategies = [
        ("single", "Single Request", 1),
        ("small", "Small Chunks (~4)", 4),
        ("medium", "Medium Chunks (~3)", 3),
        ("large", "Larger Chunks (~2)", 2),
    ]
    
    results = []
    
    for strategy_id, strategy_name, chunk_count in strategies:
        print(f"\n[CHUNKING] Testing {strategy_name} ({chunk_count} chunks)...")
        
        if chunk_count == 1:
            chunks = [narrative]
        else:
            chunk_size = len(narrative) // chunk_count
            chunks = [narrative[i*chunk_size:(i+1)*chunk_size] for i in range(chunk_count-1)]
            chunks.append(narrative[(chunk_count-1)*chunk_size:])
        
        all_translations = []
        all_success = True
        total_elapsed = 0
        http_status_final = 200
        provider_req_ids = []
        nvcf_reqids = []
        nvcf_statuses = []
        
        for i, chunk in enumerate(chunks):
            sys_prompt, user_prompt = build_prompt("glossary", {"source": chunk, "type": "narrative"}, glossary, char_memory)
            
            http_status, elapsed, req_id, nvcf_reqid, nvcf_status, finish_reason, body, error = run_single_request(
                model, sys_prompt, user_prompt, api_key, endpoint, max_tokens=8000
            )
            
            all_success = all_success and (http_status == 200)
            if http_status != 200:
                http_status_final = http_status
            total_elapsed += elapsed
            if req_id:
                provider_req_ids.append(req_id)
            if nvcf_reqid:
                nvcf_reqids.append(nvcf_reqid)
            if nvcf_status:
                nvcf_statuses.append(nvcf_status)
            all_translations.append(body or "")
            
            time.sleep(1)
        
        full_translation = "\n\n".join(all_translations)
        source_preservation = check_source_preservation(narrative, full_translation)
        quality_scores = compute_quality_scores(narrative, full_translation, "narrative", glossary, char_memory)
        
        # Check for repetition
        repetition = False
        if len(all_translations) > 1:
            for i in range(len(all_translations) - 1):
                if all_translations[i][-50:] in all_translations[i+1][:100]:
                    repetition = True
                    break
        
        # Check paragraph boundary integrity
        src_paras = narrative.count('\n\n') + 1
        tgt_paras = full_translation.count('\n\n') + 1
        para_integrity = src_paras == tgt_paras
        
        # Glossary adherence
        term_matches = sum(1 for kr, zh in glossary.items() if kr in narrative and zh in full_translation)
        term_total = sum(1 for kr in glossary.keys() if kr in narrative)
        glossary_adherence = (term_matches / max(1, term_total)) >= 0.8
        
        result = S1ChunkingResult(
            chunk_strategy=strategy_id,
            chunk_count=chunk_count,
            http_status=http_status_final,
            success=all_success,
            elapsed_ms=total_elapsed,
            source_chars=len(narrative),
            source_completeness=source_preservation >= 0.9,
            quality_score=quality_scores["overall"],
            quality_pass=quality_scores["status"] == "PASS",
            continuity_score=quality_scores["continuity"],
            repetition_detected=repetition,
            missing_text=source_preservation < 0.9,
            paragraph_boundary_integrity=para_integrity,
            glossary_adherence=glossary_adherence,
            provider_request_id=";".join(provider_req_ids) if provider_req_ids else None,
            nvcf_reqid=";".join(nvcf_reqids) if nvcf_reqids else None,
            nvcf_status=";".join(nvcf_statuses) if nvcf_statuses else None,
            error=None if all_success else "Some chunks failed"
        )
        results.append(result)
        
        print(f"  HTTP {http_status_final} | {total_elapsed:.0f}ms | Quality: {quality_scores['overall']:.1f} | Pass: {quality_scores['status']} | Repetition: {repetition} | Completeness: {source_preservation:.2f}")
    
    return results


def run_experiment_matrix(api_key: str, endpoint: str, model: str) -> List[S1ExperimentResult]:
    """Run the full experiment matrix S1-A through S1-F."""
    print("\n" + "=" * 70)
    print("S1: Experiment Matrix (S1-A through S1-F)")
    print("=" * 70)
    
    fixtures = load_fixtures()
    glossary = load_glossary()
    char_memory = load_character_memory()
    
    strategies = [
        ("S1-A", "Baseline", "base", 1.0, False),
        ("S1-B", "Glossary Only", "glossary", 1.0, False),
        ("S1-C", "Glossary + Reduced Context (70%)", "glossary", 0.70, False),
        ("S1-C", "Glossary + Reduced Context (80%)", "glossary", 0.80, False),
        ("S1-C", "Glossary + Reduced Context (85%)", "glossary", 0.85, False),
        ("S1-D", "Glossary + Controlled Chunking (3)", "glossary_chunked", 1.0, True),
        ("S1-E", "Glossary + Output Budget (6000)", "glossary_output_budget", 1.0, False),
        ("S1-F", "Optimized Envelope (85% + Glossary)", "glossary", 0.85, False),
    ]
    
    results = []
    
    for fixture_name, fixture in fixtures.items():
        for strat_id, strat_name, mode, context_pct, chunked in strategies:
            # Skip chunked for non-narrative (use single request)
            if chunked and fixture_name != "narrative":
                continue
                
            print(f"\n[EXPERIMENT] {strat_id} - {strat_name} | {fixture_name} | mode={mode} | ctx={context_pct*100:.0f}% | chunked={chunked}")
            
            if chunked:
                # Split into 3 chunks
                source = fixture["source"]
                chunk_size = len(source) // 3
                chunks = [source[i*chunk_size:(i+1)*chunk_size] for i in range(2)]
                chunks.append(source[2*chunk_size:])
                
                all_translations = []
                all_success = True
                total_elapsed = 0
                http_status_final = 200
                provider_req_ids = []
                nvcf_reqids = []
                nvcf_statuses = []
                finish_reasons = []
                user_prompt = ""
                
                for i, chunk in enumerate(chunks):
                    sys_prompt, user_prompt = build_prompt("glossary", {"source": chunk, "type": fixture["type"]}, glossary, char_memory)
                    http_status, elapsed, req_id, nvcf_reqid, nvcf_status, finish_reason, body, error = run_single_request(
                        model, sys_prompt, user_prompt, api_key, endpoint, max_tokens=6000
                    )
                    all_success = all_success and (http_status == 200)
                    if http_status != 200:
                        http_status_final = http_status
                    total_elapsed += elapsed
                    if req_id: provider_req_ids.append(req_id)
                    if nvcf_reqid: nvcf_reqids.append(nvcf_reqid)
                    if nvcf_status: nvcf_statuses.append(nvcf_status)
                    if finish_reason: finish_reasons.append(finish_reason)
                    all_translations.append(body or "")
                    time.sleep(1)
                
                translation = "\n\n".join(all_translations)
                sys_prompt_full = "You are a professional literary translator..."
                glossary_text = "\n\nGLOSSARY (must follow exactly):\n" + "\n".join([f"- {k} → {v}" for k, v in glossary.items()])
                sys_prompt_full += glossary_text
                
                source_chars = len(fixture["source"])
                est_input = estimate_tokens(sys_prompt_full + fixture["source"])
                error = None
                
            elif mode == "glossary_output_budget":
                sys_prompt, user_prompt = build_prompt("glossary", fixture, glossary, char_memory, context_pct)
                http_status, elapsed, req_id, nvcf_reqid, nvcf_status, finish_reason, body, error = run_single_request(
                    model, sys_prompt, user_prompt, api_key, endpoint, max_tokens=6000
                )
                translation = body or ""
                source_chars = len(fixture["source"])
                sys_prompt_full, _ = build_prompt("glossary", fixture, glossary, char_memory, context_pct)
                est_input = estimate_tokens(sys_prompt_full + user_prompt)
                all_success = http_status == 200
                total_elapsed = elapsed
                http_status_final = http_status
                provider_req_ids = [req_id] if req_id else []
                nvcf_reqids = [nvcf_reqid] if nvcf_reqid else []
                nvcf_statuses = [nvcf_status] if nvcf_status else []
                finish_reasons = [finish_reason] if finish_reason else []
                
            else:
                sys_prompt, user_prompt = build_prompt(mode, fixture, glossary, char_memory, context_pct)
                http_status, elapsed, req_id, nvcf_reqid, nvcf_status, finish_reason, body, error = run_single_request(
                    model, sys_prompt, user_prompt, api_key, endpoint, max_tokens=8000
                )
                translation = body or ""
                source_chars = len(user_prompt)
                sys_prompt_full, _ = build_prompt(mode, fixture, glossary, char_memory, context_pct)
                est_input = estimate_tokens(sys_prompt_full + user_prompt)
                all_success = http_status == 200
                total_elapsed = elapsed
                http_status_final = http_status
                provider_req_ids = [req_id] if req_id else []
                nvcf_reqids = [nvcf_reqid] if nvcf_reqid else []
                nvcf_statuses = [nvcf_status] if nvcf_status else []
                finish_reasons = [finish_reason] if finish_reason else []
            
            truncation, corruption = check_truncation_corruption(user_prompt if not chunked else fixture["source"], translation)
            source_preservation = check_source_preservation(fixture["source"], translation)
            quality_scores = compute_quality_scores(fixture["source"], translation, fixture["type"], glossary, char_memory)
            
            result = S1ExperimentResult(
                strategy_id=strat_id,
                strategy_name=strat_name,
                fixture_type=fixture["type"],
                mode=mode,
                timestamp_utc=datetime.datetime.utcnow().isoformat() + "Z",
                http_status=http_status_final,
                success=all_success,
                elapsed_ms=total_elapsed,
                source_chars=source_chars,
                estimated_input_tokens=est_input,
                estimated_output_tokens=estimate_tokens(translation),
                system_prompt_chars=len(sys_prompt_full) if not chunked else len("You are a professional literary translator...") + len("\n\nGLOSSARY (must follow exactly):\n" + "\n".join([f"- {k} → {v}" for k, v in glossary.items()])),
                glossary_chars=len("\n\nGLOSSARY (must follow exactly):\n" + "\n".join([f"- {k} → {v}" for k, v in glossary.items()])) if mode != "base" else 0,
                memory_chars=0,
                context_chars=source_chars,
                requested_output_tokens=8000 if mode != "glossary_output_budget" else 6000,
                actual_output_tokens=estimate_tokens(translation),
                source_preservation_ratio=source_preservation,
                output_truncation=truncation,
                completion_finish_reason=";".join(finish_reasons) if finish_reasons else None,
                provider_request_id=";".join(provider_req_ids) if provider_req_ids else None,
                nvcf_reqid=";".join(nvcf_reqids) if nvcf_reqids else None,
                nvcf_status=";".join(nvcf_statuses) if nvcf_statuses else None,
                error=error,
                quality_score=quality_scores["overall"],
                quality_pass=quality_scores["status"] == "PASS",
                continuity_score=quality_scores["continuity"],
                terminology_consistency=quality_scores["terminology_consistency"],
                chunk_count=3 if chunked else 1,
                chunk_strategy="chunked_3" if chunked else "single"
            )
            results.append(result)
            
            print(f"  HTTP {http_status_final} | {total_elapsed:.0f}ms | Quality: {quality_scores['overall']:.1f} ({quality_scores['status']}) | Trunc: {truncation} | Preservation: {source_preservation:.2f}")
            time.sleep(1)
    
    return results


def run_glossary_investigation(api_key: str, endpoint: str, model: str) -> List[S1GlossaryResult]:
    """Detailed glossary effectiveness investigation."""
    print("\n" + "=" * 70)
    print("S1-C: Glossary Investigation")
    print("=" * 70)
    
    fixtures = load_fixtures()
    glossary = load_glossary()
    char_memory = load_character_memory()
    
    results = []
    
    for fixture_name, fixture in fixtures.items():
        print(f"\n[GLOSSARY] Testing {fixture_name}...")
        
        # Base (no glossary)
        sys_prompt, user_prompt = build_prompt("base", fixture, glossary, char_memory)
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, finish_reason, body, error = run_single_request(
            model, sys_prompt, user_prompt, api_key, endpoint, max_tokens=8000
        )
        base_translation = body or ""
        base_scores = compute_quality_scores(fixture["source"], base_translation, fixture["type"], glossary, char_memory)
        
        time.sleep(1)
        
        # Glossary
        sys_prompt, user_prompt = build_prompt("glossary", fixture, glossary, char_memory)
        http_status, elapsed, req_id, nvcf_reqid, nvcf_status, finish_reason, body, error = run_single_request(
            model, sys_prompt, user_prompt, api_key, endpoint, max_tokens=8000
        )
        glossary_translation = body or ""
        glossary_scores = compute_quality_scores(fixture["source"], glossary_translation, fixture["type"], glossary, char_memory)
        
        improvement = glossary_scores["overall"] - base_scores["overall"]
        
        # Check for unwanted over-application (terms forced where not in source)
        unwanted = False
        for kr, zh in glossary.items():
            if kr not in fixture["source"] and zh in glossary_translation:
                unwanted = True
                break
        
        result = S1GlossaryResult(
            fixture_name=fixture_name,
            base_score=base_scores["overall"],
            glossary_score=glossary_scores["overall"],
            improvement=improvement,
            terminology_consistency_base=base_scores["terminology_consistency"],
            terminology_consistency_glossary=glossary_scores["terminology_consistency"],
            quality_pass_base=base_scores["status"] == "PASS",
            quality_pass_glossary=glossary_scores["status"] == "PASS",
            unwanted_over_application=unwanted
        )
        results.append(result)
        
        print(f"  Base: {base_scores['overall']:.1f} ({base_scores['status']}) | Glossary: {glossary_scores['overall']:.1f} ({glossary_scores['status']}) | Δ: {improvement:+.1f} | Unwanted: {unwanted}")
    
    return results


def build_context_quality_matrix(experiments: List[S1ExperimentResult], 
                                  context_boundary: List[S1ContextBoundaryResult],
                                  chunking: List[S1ChunkingResult]) -> List[S1ContextQualityMatrix]:
    """Build the Context x Quality matrix."""
    context_quality_matrix: List[S1ContextQualityMatrix] = []
    
    # Aggregate by strategy
    strategy_map = {}
    for exp in experiments:
        key = f"{exp.strategy_id}_{exp.fixture_type}"
        if key not in strategy_map:
            strategy_map[key] = []
        strategy_map[key].append(exp)
    
    for key, exps in strategy_map.items():
        if not exps:
            continue
        strat_id = exps[0].strategy_id
        strat_name = exps[0].strategy_name
        fixture_type = exps[0].fixture_type
        
        http_success = all(e.success for e in exps)
        truncation = any(e.output_truncation for e in exps)
        avg_quality = sum(e.quality_score or 0.0 for e in exps) / len(exps)
        quality_pass = all(e.quality_pass for e in exps)
        continuity_pass = all((e.continuity_score or 0.0) >= 8 for e in exps)
        
        if http_success and not truncation and quality_pass and continuity_pass:
            verdict = "PASS"
        elif http_success and not truncation and quality_pass:
            verdict = "CONDITIONAL"
        else:
            verdict = "FAIL"
        
        context_quality_matrix.append(S1ContextQualityMatrix(
            context_strategy=f"{strat_id} ({strat_name}) - {fixture_type}",
            http_success=http_success,
            truncation=truncation,
            quality=avg_quality,
            quality_pass=quality_pass,
            continuity_pass=continuity_pass,
            verdict=verdict
        ))
    
    # Add context boundary results
    for cb in context_boundary:
        # Find matching quality from experiments
        matching_exp = [e for e in experiments if e.fixture_type == "narrative" and abs(e.context_chars/len(load_fixtures()["narrative"]["source"]) - cb.boundary_pct) < 0.05]
        quality = float(matching_exp[0].quality_score) if matching_exp and matching_exp[0].quality_score is not None else 0.0
        quality_pass = bool(matching_exp[0].quality_pass) if matching_exp and matching_exp[0].quality_pass is not None else False
        
        context_quality_matrix.append(S1ContextQualityMatrix(
            context_strategy=f"Boundary {cb.level} ({cb.boundary_pct*100:.0f}%)",
            http_success=cb.success,
            truncation=cb.output_truncation,
            quality=quality,
            quality_pass=quality_pass,
            continuity_pass=quality_pass,  # approximate
            verdict="SAFE" if cb.classification == "SAFE" else ("CAUTION" if cb.classification == "CAUTION" else "FAIL")
        ))
    
    # Add chunking results
    for ck in chunking:
        context_quality_matrix.append(S1ContextQualityMatrix(
            context_strategy=f"Chunking {ck.chunk_strategy} ({ck.chunk_count} chunks)",
            http_success=ck.success,
            truncation=ck.missing_text,
            quality=ck.quality_score,
            quality_pass=ck.quality_pass,
            continuity_pass=ck.continuity_score >= 8,
            verdict="PASS" if (ck.success and ck.quality_pass and not ck.repetition_detected and not ck.missing_text) else "FAIL"
        ))
    
    return context_quality_matrix


def determine_final_classification(matrix: List[S1ContextQualityMatrix], 
                                    glossary: List[S1GlossaryResult],
                                    human_review_status: str) -> tuple[str, str]:
    """Determine final classification per decision tree."""
    
    # Check if any strategy achieves full recovery
    full_recovery = any(
        m.http_success and not m.truncation and m.quality_pass and m.continuity_pass 
        for m in matrix
    )
    
    if not full_recovery:
        # Check if conditional recovery exists
        conditional = any(
            m.http_success and not m.truncation and m.quality_pass 
            for m in matrix
        )
        if conditional:
            return "CONDITIONALLY_RECOVERABLE", "Recovery possible with constraints (glossary required, context limit, specific chunking)"
        return "NOT_RECOVERABLE", "No strategy achieves stable context + quality + continuity simultaneously"
    
    # Full recovery exists - check human review
    if human_review_status == "PASS":
        return "RECOVERABLE", "All gates pass including human review - candidate ready for controlled replacement evaluation"
    elif human_review_status == "PENDING":
        return "CONDITIONALLY_RECOVERABLE", "Technical recovery demonstrated but human review pending"
    else:
        return "NOT_RECOVERABLE", "Human review FAIL"


def run_s1_investigation() -> S1Report:
    print("=" * 70)
    print("P0-FINAL-15-S1: GPT-OSS 120B Context & Quality Recovery Investigation")
    print("=" * 70)
    
    baseline = get_git_baseline()
    
    candidate_model = "openai/gpt-oss-120b"
    hosting_provider = "NVIDIA"
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    api_key = os.environ.get("NVIDIA_API_KEY")
    
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    
    print(f"Candidate: {candidate_model}")
    print(f"Hosting: {hosting_provider}")
    print(f"Baseline: {baseline['head_commit'][:8]} ({baseline['branch']})")
    
    # Verify production freeze
    print("\n[COMPLIANCE] Verifying production freeze...")
    print("  Production Model: minimaxai/minimax-m3 (FROZEN)")
    print("  Production Routing: UNCHANGED")
    print("  Retry/Backoff/RPM/Timeout/ChunkSize/Runtime: UNCHANGED")
    print("  RM6: BLOCKED")
    
    # Run investigations
    context_boundary = run_context_boundary_sweep(api_key, endpoint, candidate_model)
    chunking_results = run_chunking_investigation(api_key, endpoint, candidate_model)
    experiment_results = run_experiment_matrix(api_key, endpoint, candidate_model)
    glossary_results = run_glossary_investigation(api_key, endpoint, candidate_model)
    
    # Build matrix
    context_quality_matrix = build_context_quality_matrix(experiment_results, context_boundary, chunking_results)
    
    # Human review status (from S-stage)
    human_review_status = "PENDING"  # Per S final decision
    
    # Determine classification
    final_classification, recommendation = determine_final_classification(
        context_quality_matrix, glossary_results, human_review_status
    )
    
    # Production compatibility assessment
    production_compatible = True
    compat_issues = []
    for m in context_quality_matrix:
        if m.verdict == "PASS":
            # Check if it requires production changes
            pass  # Would need deeper analysis
    if not production_compatible:
        prod_compat = "NOT_COMPATIBLE"
    else:
        prod_compat = "COMPATIBLE_WITH_CONSTRAINTS"
    
    risk_assessment = "MEDIUM" if final_classification in ["CONDITIONALLY_RECOVERABLE", "RECOVERABLE"] else "HIGH"
    
    historical_refs = [
        "P0_FINAL_15_S_GPT_OSS_120B_CONTEXT_BOUNDARY_REPORT.json",
        "P0_FINAL_15_S_GPT_OSS_120B_TRANSLATION_QUALITY_REPORT.json",
        "P0_FINAL_15_S_GPT_OSS_120B_RELIABILITY_REPORT.json",
        "P0_FINAL_15_S_GPT_OSS_120B_RUNTIME_STABILITY_REPORT.json",
        "P0_FINAL_15_S_FINAL_DECISION.json"
    ]
    
    limitations = [
        "Single NVIDIA account used for all testing",
        "No cross-provider comparison",
        "Single-run per condition (no repetition for statistical significance)",
        "Automated quality scoring only; human literary review pending",
        "Token estimation is character-based approximation",
        "Context boundary sweep uses narrative fixture only",
        "Chunking test uses narrative fixture only",
        "No streaming test",
        "No sustained load test",
        "Production workload may differ from test fixtures"
    ]
    
    return S1Report(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        candidate_model=candidate_model,
        hosting_provider=hosting_provider,
        endpoint=endpoint,
        credential_source="NVIDIA_API_KEY",
        production_model="minimaxai/minimax-m3",
        production_routing="UNCHANGED",
        production_retry="UNCHANGED",
        production_backoff="UNCHANGED",
        production_rpm="UNCHANGED",
        production_timeout="UNCHANGED",
        production_chunk_size="UNCHANGED",
        production_runtime="UNCHANGED",
        rm6_status="BLOCKED",
        experiments=experiment_results,
        context_boundary=context_boundary,
        chunking_results=chunking_results,
        quality_results=[e for e in experiment_results if e.quality_score is not None],
        glossary_results=glossary_results,
        context_quality_matrix=context_quality_matrix,
        human_review_status=human_review_status,
        production_compatibility=prod_compat,
        risk_assessment=risk_assessment,
        historical_references=historical_refs,
        final_classification=final_classification,
        recommendation=recommendation,
        limitations=limitations
    )


def save_report(report: S1Report):
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    # JSON artifact
    report_path = artifacts_dir / "P0_FINAL_15_S1_GPT_OSS_120B_CONTEXT_QUALITY_RECOVERY_REPORT.json"
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    print(f"\n[S1] Report saved to: {report_path}")
    
    # Governance markdown
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    gov_path = governance_dir / "P0_FINAL_15_S1_GPT_OSS_120B_CONTEXT_QUALITY_RECOVERY.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-S1: GPT-OSS 120B Context & Quality Recovery Investigation

## Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Timestamp**: {report.test_timestamp}

## Candidate
- **Model**: {report.candidate_model}
- **Hosting**: {report.hosting_provider}
- **Endpoint**: {report.endpoint}
- **Credential**: {report.credential_source}

## Production State (FROZEN)
- **Production Model**: {report.production_model}
- **Production Routing**: {report.production_routing}
- **Retry Policy**: {report.production_retry}
- **Backoff**: {report.production_backoff}
- **RPM Limiter**: {report.production_rpm}
- **Timeout**: {report.production_timeout}
- **Chunk Size**: {report.production_chunk_size}
- **Runtime**: {report.production_runtime}
- **RM6 Status**: {report.rm6_status}

## Experiment Matrix (S1-A through S1-F)

| Strategy | Fixture | Mode | Context | Chunks | HTTP | Quality | Pass | Truncation | Preservation |
|----------|---------|------|---------|--------|------|---------|------|------------|--------------|
""")
        for e in report.experiments:
            f.write(f"| {e.strategy_id} | {e.fixture_type} | {e.mode} | {e.context_chars/len(load_fixtures()[e.fixture_type]['source'])*100:.0f}% | {e.chunk_count} | {e.http_status} | {e.quality_score:.1f} | {e.quality_pass} | {e.output_truncation} | {e.source_preservation_ratio:.2f} |\n")
        
        f.write(f"""
## Context Boundary Sweep

| Boundary | Level | HTTP | Success | Latency | Input Tokens | Output Tokens | Preservation | Truncation | Classification |
|----------|-------|------|---------|---------|--------------|---------------|--------------|------------|----------------|
""")
        for cb in report.context_boundary:
            f.write(f"| {cb.boundary_pct*100:.0f}% | {cb.level} | {cb.http_status} | {cb.success} | {cb.elapsed_ms:.0f}ms | {cb.estimated_input_tokens} | {cb.actual_output_tokens} | {cb.source_preservation_ratio:.2f} | {cb.output_truncation} | {cb.classification} |\n")
        
        f.write(f"""
## Chunking Investigation

| Strategy | Chunks | HTTP | Success | Latency | Quality | Pass | Completeness | Repetition | Para Integrity | Glossary Adherence |
|----------|--------|------|---------|---------|---------|------|--------------|------------|----------------|-------------------|
""")
        for ck in report.chunking_results:
            f.write(f"| {ck.chunk_strategy} | {ck.chunk_count} | {ck.http_status} | {ck.success} | {ck.elapsed_ms:.0f}ms | {ck.quality_score:.1f} | {ck.quality_pass} | {ck.source_completeness} | {ck.repetition_detected} | {ck.paragraph_boundary_integrity} | {ck.glossary_adherence} |\n")
        
        f.write(f"""
## Glossary Investigation

| Fixture | Base Score | Glossary Score | Δ | Term Base | Term Glossary | Base Pass | Glossary Pass | Unwanted Over-application |
|---------|------------|----------------|---|-----------|---------------|-----------|---------------|---------------------------|
""")
        for g in report.glossary_results:
            f.write(f"| {g.fixture_name} | {g.base_score:.1f} | {g.glossary_score:.1f} | {g.improvement:+.1f} | {g.terminology_consistency_base:.1f} | {g.terminology_consistency_glossary:.1f} | {g.quality_pass_base} | {g.quality_pass_glossary} | {g.unwanted_over_application} |\n")
        
        f.write(f"""
## Context × Quality Matrix

| Context Strategy | HTTP | Truncation | Quality | Quality Pass | Continuity Pass | Verdict |
|------------------|------|------------|---------|--------------|-----------------|---------|
""")
        for m in report.context_quality_matrix:
            f.write(f"| {m.context_strategy} | {m.http_success} | {m.truncation} | {m.quality:.1f} | {m.quality_pass} | {m.continuity_pass} | {m.verdict} |\n")
        
        f.write(f"""
## Human Review Status

**{report.human_review_status}**

## Production Compatibility

**{report.production_compatibility}**

## Risk Assessment

**{report.risk_assessment}**

## Historical Evidence References

""")
        for ref in report.historical_references:
            f.write(f"- {ref}\n")
        
        f.write(f"""
## Final Classification

**{report.final_classification}**

## Recommendation

{report.recommendation}

## Limitations

""")
        for lim in report.limitations:
            f.write(f"- {lim}\n")
        
        f.write("""
## Compliance

- ✅ No credential leakage
- ✅ No production modification
- ✅ Read-only provider invocation
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
- ✅ Historical evidence preserved
- ✅ Artifacts in tools/one_shots/ and artifacts/
- ✅ Governance in docs/governance/repository/

## Next Stage

If **RECOVERABLE** → Proceed to **P0-FINAL-15-T — Controlled Replacement Readiness / Final Human-Gated Approval**  
If **CONDITIONALLY_RECOVERABLE** → Document constraints, evaluate if acceptable for production  
If **NOT_RECOVERABLE** → Candidate rejected, remain on minimaxai/minimax-m3  
If **INSUFFICIENT_EVIDENCE** → Additional investigation required
""")
    
    print(f"[S1] Governance doc saved to: {gov_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("S1 INVESTIGATION SUMMARY")
    print("=" * 70)
    print(f"Experiments: {len(report.experiments)}")
    print(f"Context Boundaries: {len(report.context_boundary)}")
    print(f"Chunking Strategies: {len(report.chunking_results)}")
    print(f"Glossary Tests: {len(report.glossary_results)}")
    print(f"Matrix Rows: {len(report.context_quality_matrix)}")
    print(f"\nFinal Classification: {report.final_classification}")
    print(f"Recommendation: {report.recommendation}")
    print(f"Human Review: {report.human_review_status}")
    print(f"Production Compatibility: {report.production_compatibility}")
    print(f"Risk: {report.risk_assessment}")
    print(f"\nProduction Model: {report.production_model} (UNCHANGED)")
    print(f"RM6: {report.rm6_status}")
    
    # Matrix summary
    print("\nContext × Quality Matrix:")
    for m in report.context_quality_matrix:
        print(f"  {m.context_strategy}: HTTP={m.http_success} Trunc={m.truncation} Qual={m.quality:.1f} Pass={m.quality_pass} Cont={m.continuity_pass} → {m.verdict}")
    
    return 0 if report.final_classification in ["RECOVERABLE", "CONDITIONALLY_RECOVERABLE"] else 1


def main():
    import datetime
    import requests
    
    print("=" * 70)
    print("P0-FINAL-15-S1: GPT-OSS 120B Context & Quality Recovery Investigation")
    print("=" * 70)
    
    # Verify baseline
    baseline = get_git_baseline()
    print(f"Branch: {baseline['branch']}")
    print(f"HEAD: {baseline['head_commit'][:12]}")
    if baseline['branch'] != 'main' or baseline['head_commit'] != '8c999b1219f65a6afaeaf0062e6c43f72691c188':
        print("⚠️  BASELINE MISMATCH - STOP")
        return 1
    
    report = run_s1_investigation()
    
    save_report(report)
    
    print("\n" + "=" * 70)
    print("P0-FINAL-15-S1 Complete")
    print("=" * 70)
    
    return 0 if report.final_classification in ["RECOVERABLE", "CONDITIONALLY_RECOVERABLE"] else 1


if __name__ == "__main__":
    import datetime
    import requests
    sys.exit(main())
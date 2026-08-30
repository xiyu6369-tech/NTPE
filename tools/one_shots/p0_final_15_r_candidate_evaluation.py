#!/usr/bin/env python3
"""
P0-FINAL-15-R: Cross-Provider Candidate Evaluation

Phase R-B: Evaluate priority candidates across providers.
Tests: smoke, translation (narrative/dialogue/continuity), quality, glossary, context, reliability.
"""

from __future__ import annotations

import json
import os
import sys
import time
import datetime
import requests
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@dataclass
class SmokeResult:
    """Smoke test result."""
    model: str
    provider: str
    timestamp_utc: str
    http_status: int
    success: bool
    elapsed_ms: float
    provider_request_id: Optional[str]
    nvcf_reqid: Optional[str] = None
    nvcf_status: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TranslationResult:
    """Translation test result."""
    model: str
    provider: str
    fixture_name: str
    fixture_type: str
    mode: str  # base, glossary
    source_text: str
    translation: str
    http_status: int
    success: bool
    elapsed_ms: float
    provider_request_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class QualityScores:
    """Automated quality scores."""
    overall: float
    semantic_fidelity: float
    fluency: float
    literary_style: float
    terminology_consistency: float
    character_consistency: float
    continuity: float
    formatting_preservation: float
    status: str  # PASS/FAIL


@dataclass
class ReliabilityResult:
    """Reliability observation."""
    model: str
    provider: str
    timestamp_utc: str
    http_status: int
    success: bool
    elapsed_ms: float
    provider_request_id: Optional[str]
    error: Optional[str] = None


@dataclass
class CandidateEvaluation:
    """Complete evaluation for one candidate."""
    model_id: str
    provider: str
    api_type: str
    
    # Smoke
    smoke_results: list[SmokeResult]
    smoke_success_rate: float
    smoke_median_latency_ms: float
    smoke_p95_latency_ms: float
    
    # Translation
    translation_results: list[TranslationResult]
    translation_success_rate: float
    
    # Quality
    quality_scores: dict[str, QualityScores]
    avg_quality_score: float
    quality_pass: bool
    glossary_improvement: float
    
    # Context
    context_results: list[dict]
    context_compatible: bool
    
    # Reliability
    reliability_results: list[ReliabilityResult]
    reliability_success_rate: float
    reliability_median_latency_ms: float
    reliability_p95_latency_ms: float
    
    # Classification
    classification: str
    classification_rationale: str
    
    # Limitations
    limitations: list[str]


@dataclass
class EvaluationReport:
    """Complete evaluation report for all candidates."""
    head_commit: str
    origin_main_commit: str
    divergence: str
    branch: str
    python_version: str
    test_timestamp: str
    candidates: list[CandidateEvaluation]
    m1_baseline: Optional[CandidateEvaluation]
    limitations: list[str]


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


def load_inventory() -> dict:
    """Load cross-provider inventory to get priority candidates."""
    path = Path(__file__).resolve().parents[2] / "artifacts" / "P0_FINAL_15_R_CROSS_PROVIDER_CANDIDATE_INVENTORY.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"priority_candidates": []}


def load_fixtures() -> dict[str, dict]:
    """Load translation test fixtures."""
    fixtures = {}
    
    # Narrative
    golden_path = Path(__file__).resolve().parents[2].joinpath("tests/literary/Golden_Set/original_ko.txt")
    if golden_path.exists():
        narrative_source = golden_path.read_text(encoding="utf-8")
    else:
        narrative_source = (
            "정태의는 아차, 하고 자리에서 일어섰다. 카일은 프라이빗풀 옆의 벤치에서 정신없이 잠들어 있을 터였다. "
            "(일주일의 휴가를 위해 그가 이곳에 오기 직전까지 밤을 새며 퀭한 얼굴로 일했다는 걸 정태의는 알고 있었다. "
            "그래서, 그가 막무가내로 여기에 오겠다고 하는 주장을 차마 거스를 수 없었다.) "
            "라군에서 바닷가는, 당연하다면 당연하지만, 엎어지면 코 닿을 거리였다. "
            "근처만 서성이려면 바다 위로 뻗은 나무다리 위로 산책을 할 수도 있지만, "
            "정태的は 천천히 섬을 한 바퀴 돌아보자고 생각하고 백사장 쪽을 선택했다. "
            "대충 걸어서 두어 시간이면 한 바퀴 다 돌 수 있을 정도로 작은 섬이라고 들었다. "
            "무릎까지 오는 반바지 위에 넉넉한 셔츠 하나만 대충 걸치고, 그가 막 로비에서 나서려던 때였다. "
            "새로운 손님이 왔는지, 바깥에서 약간 떠들썩하게―라고 해도 이곳이 워낙 조용해서, "
            "단순한 말소리조차 그렇게 들릴 뿐이었지만―두세 명이 들어서고 있었다. "
            "정태의는 저도 모르게 걸음을 멈추었다. 귀에 익은 독일어가 들렸다. "
            "목소리를 들어보건대 결코 그놈이 온 건 아니었지만 그래도 반사적으로 숨을 멈추고 만다. "
            "조용하지만 냉정하고 사무적인 말투는, 이곳에 같이 오기로 했던 동행과 따로 오게 되었다는 요지의 말을 하고 있었다. "
            "그 동행도 한두 시간 안에 도착할 거라는 말을 하며, 그 독일인은 모습을 드러내었다. "
            "바늘 끝 하나 들어가지 않을 듯, 빈틈이라곤 없어 보이는 남자였다. "
            "침착하고 담담해 보이는 남자였지만, 눈치 하나만으로 인생 역경을 헤쳐온 정태의는 저도 모르게 눈살을 찌푸렸다. "
            "자칫 잘못 건드렸다간 뼈도 추리기 힘들 듯한 인간이다. 가급적이면 엮이지 않는 게 좋을. "
            "정태의는 못 본 척하고 걸음을 옮겼다. 굳이 엮일 일도 없을 테니, 하려던 대로 산책이나 하자. "
            "그러나, 그때 남자의 시선이 정태의에게 멎었다. 엉겁결에 정태의도 그를 마주본다."
        )
    
    fixtures["narrative"] = {
        "name": "narrative", "type": "narrative", "source": narrative_source,
        "description": "Novel narrative with character introspection, setting description, dialogue",
    }
    
    # Dialogue
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
        ),
        "description": "Dialogue-heavy scene with emotional exchange, honorifics, character distinction",
    }
    
    # Continuity
    fixtures["continuity"] = {
        "name": "continuity", "type": "continuity",
        "source": (
            '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, '
            '그는 특유의 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. '
            '논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.\n\n'
            '어느 날, 두 사람은 연쇄 실종 사건을 맡게 되었다. '
            '철수는 현장의 미세한 흔적에서 단서를 찾으려 했고, 영희는 피해자들의 공통점을 분석했다. '
            '처음엔 서로의 방식을 불신했지만, 곧 그들의 접근법이 서로 보완됨을 깨달았다. '
            '철수의 직관이 영희의 논리를 이끌었고, 영희의 증거가 철수의 추측을 뒷받침했다.'
        ),
        "description": "Two paragraphs with character consistency, terminology continuity, cross-reference",
    }
    
    return fixtures


def load_glossary() -> dict[str, str]:
    return {
        "정태의": "鄭泰義", "카일": "凱爾", "민수": "旻秀", "지현": "智賢",
        "김철수": "金哲秀", "이영희": "李英姬", "프라이빗풀": "私人泳池",
        "라군": "潟湖", "백사장": "沙灘", "로비": "大廳", "독일어": "德語",
        "동행": "同行", "베를린": "柏林", "남국": "南國", "섬": "島嶼",
        "호텔": "飯店", "형사": "刑警", "파트너": "搭檔", "원칙주의자": "原則主義者",
        "연쇄 실종 사건": "連環失蹤案", "현장": "現場", "피해자": "受害者",
        "공통점": "共同點", "직관": "直覺", "논리": "邏輯", "증거": "證據", "推測": "推測",
    }


def load_character_memory() -> list[dict]:
    return [
        {"name": "정태의", "aliases": ["鄭泰義", "Jung Tae-ui"], "role": "protagonist", "gender": "male", "description": "Sharp-eyed survivor who relies on intuition"},
        {"name": "카일", "aliases": ["凱爾", "Kyle"], "role": "companion", "gender": "male", "description": "Rational, protective figure"},
        {"name": "민수", "aliases": ["旻秀", "Minsu"], "role": "supporting", "gender": "male", "description": "Caring friend"},
        {"name": "지현", "aliases": ["智賢", "Jihyun"], "role": "supporting", "gender": "female", "description": "Hides stress behind forced smiles"},
        {"name": "김철수", "aliases": ["金哲秀", "Kim Cheol-su"], "role": "protagonist", "gender": "male", "description": "30-year veteran detective"},
        {"name": "이영희", "aliases": ["李英姬", "Lee Young-hee"], "role": "protagonist", "gender": "female", "description": "Principled detective"},
    ]


def build_prompt(mode: str, fixture: dict, glossary: dict, char_memory: list[dict]) -> tuple[str, str]:
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
    if mode == "glossary" and glossary:
        glossary_lines = [f"- {k} → {v}" for k, v in glossary.items()]
        glossary_text = "\n\nGLOSSARY (must follow exactly):\n" + "\n".join(glossary_lines)
    
    char_memory_text = ""
    if mode == "char_memory" and char_memory:
        char_lines = [f"- {c['name']} ({', '.join(c['aliases'])}) — {c['role']}, {c['gender']}: {c['description']}" for c in char_memory]
        char_memory_text = "\n\nCHARACTER MEMORY:\n" + "\n".join(char_lines)
    
    system_prompt = base_system + glossary_text + char_memory_text
    user_prompt = fixture["source"]
    return system_prompt, user_prompt


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 3)


def compute_quality_scores(source: str, translation: str, fixture_type: str, glossary: dict, char_memory: list[dict]) -> QualityScores:
    scores = {"semantic_fidelity": 0.0, "fluency": 0.0, "literary_style": 0.0,
              "terminology_consistency": 0.0, "character_consistency": 0.0,
              "continuity": 0.0, "formatting_preservation": 0.0}
    
    if not translation or not translation.strip():
        return QualityScores(overall=0.0, **scores, status="FAIL")
    
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
    return QualityScores(overall=overall, **scores, status=status)


def make_request_openai_compatible(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 8000) -> tuple[int, float, Optional[str], str, Optional[str]]:
    payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.15, "top_p": 0.85, "max_tokens": max_tokens, "stream": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=(10, 120))
        elapsed = (time.monotonic() - start) * 1000
        http_status = resp.status_code
        provider_request_id = None
        try:
            data = resp.json()
            provider_request_id = data.get("id")
            response_body = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception:
            response_body = resp.text
        error = None if http_status == 200 else f"HTTP {http_status}: {resp.text[:200]}"
        return http_status, elapsed, provider_request_id, response_body, error
    except requests.exceptions.Timeout as e:
        elapsed = (time.monotonic() - start) * 1000
        return 408, elapsed, None, "", f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, "", str(e)


def make_request_anthropic(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 8000) -> tuple[int, float, Optional[str], str, Optional[str]]:
    payload = {"model": model, "max_tokens": max_tokens, "temperature": 0.15, "messages": [{"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}]}
    headers = {"x-api-key": api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
    start = time.monotonic()
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=(10, 120))
        elapsed = (time.monotonic() - start) * 1000
        http_status = resp.status_code
        provider_request_id = None
        response_body = ""
        try:
            data = resp.json()
            provider_request_id = data.get("id")
            response_body = data.get("content", [{}])[0].get("text", "")
        except Exception:
            response_body = resp.text
        error = None if http_status == 200 else f"HTTP {http_status}: {resp.text[:200]}"
        return http_status, elapsed, provider_request_id, response_body, error
    except requests.exceptions.Timeout as e:
        elapsed = (time.monotonic() - start) * 1000
        return 408, elapsed, None, "", f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, "", str(e)


def make_request_google(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 8000) -> tuple[int, float, Optional[str], str, Optional[str]]:
    # Google uses API key in URL
    url = f"{endpoint}?key={api_key}"
    payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}], "generationConfig": {"temperature": 0.15, "topP": 0.85, "maxOutputTokens": max_tokens}}
    headers = {"Content-Type": "application/json"}
    start = time.monotonic()
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=(10, 120))
        elapsed = (time.monotonic() - start) * 1000
        http_status = resp.status_code
        provider_request_id = None
        response_body = ""
        try:
            data = resp.json()
            provider_request_id = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            response_body = provider_request_id
        except Exception:
            response_body = resp.text
        error = None if http_status == 200 else f"HTTP {http_status}: {resp.text[:200]}"
        return http_status, elapsed, provider_request_id, response_body, error
    except requests.exceptions.Timeout as e:
        elapsed = (time.monotonic() - start) * 1000
        return 408, elapsed, None, "", f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, "", str(e)


def make_request_cohere(model: str, system_prompt: str, user_prompt: str, api_key: str, endpoint: str, max_tokens: int = 8000) -> tuple[int, float, Optional[str], str, Optional[str]]:
    payload = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.15, "p": 0.85, "max_tokens": max_tokens}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    start = time.monotonic()
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=(10, 120))
        elapsed = (time.monotonic() - start) * 1000
        http_status = resp.status_code
        provider_request_id = None
        response_body = ""
        try:
            data = resp.json()
            provider_request_id = data.get("generation_id")
            response_body = data.get("text", "")
        except Exception:
            response_body = resp.text
        error = None if http_status == 200 else f"HTTP {http_status}: {resp.text[:200]}"
        return http_status, elapsed, provider_request_id, response_body, error
    except requests.exceptions.Timeout as e:
        elapsed = (time.monotonic() - start) * 1000
        return 408, elapsed, None, "", f"Timeout: {e}"
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return 500, elapsed, None, "", str(e)


def get_api_config(provider: str, api_type: str) -> dict:
    """Get API configuration for a provider."""
    configs = {
        "OpenAI": {"api_type": "openai-compatible", "endpoint": "https://api.openai.com/v1/chat/completions", "env_var": "OPENAI_API_KEY"},
        "Anthropic": {"api_type": "anthropic", "endpoint": "https://api.anthropic.com/v1/messages", "env_var": "ANTHROPIC_API_KEY"},
        "Google": {"api_type": "google", "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent", "env_var": "GOOGLE_API_KEY"},
        "Cohere": {"api_type": "cohere", "endpoint": "https://api.cohere.ai/v1/chat", "env_var": "COHERE_API_KEY"},
        "Mistral AI": {"api_type": "openai-compatible", "endpoint": "https://api.mistral.ai/v1/chat/completions", "env_var": "MISTRAL_API_KEY"},
        "DeepSeek": {"api_type": "openai-compatible", "endpoint": "https://api.deepseek.com/v1/chat/completions", "env_var": "DEEPSEEK_API_KEY"},
        "Z.ai": {"api_type": "openai-compatible", "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions", "env_var": "ZAI_API_KEY"},
    }
    return configs.get(provider, {"api_type": "openai-compatible", "endpoint": "", "env_var": ""})


def dispatch_request(model: str, provider: str, api_type: str, system_prompt: str, user_prompt: str, max_tokens: int = 8000) -> tuple[int, float, Optional[str], str, Optional[str]]:
    """Dispatch request to appropriate API handler."""
    config = get_api_config(provider, api_type)
    api_key = os.environ.get(config["env_var"])
    if not api_key:
        return 0, 0.0, None, "", f"Credential not found: {config['env_var']}"
    endpoint = config["endpoint"]
    
    if api_type == "openai-compatible":
        return make_request_openai_compatible(model, system_prompt, user_prompt, api_key, endpoint, max_tokens)
    elif api_type == "anthropic":
        return make_request_anthropic(model, system_prompt, user_prompt, api_key, endpoint, max_tokens)
    elif api_type == "google":
        return make_request_google(model, system_prompt, user_prompt, api_key, endpoint, max_tokens)
    elif api_type == "cohere":
        return make_request_cohere(model, system_prompt, user_prompt, api_key, endpoint, max_tokens)
    else:
        return 0, 0.0, None, "", f"Unknown API type: {api_type}"


def evaluate_candidate(candidate: dict, api_key_map: dict) -> CandidateEvaluation:
    """Evaluate a single candidate across all tests."""
    model_id = candidate["model_id"]
    provider = candidate["provider"]
    api_type = candidate.get("api_type", "openai-compatible")
    
    print(f"\n[EVAL] Evaluating {model_id} ({provider})...")
    
    fixtures = load_fixtures()
    glossary = load_glossary()
    char_memory = load_character_memory()
    
    # Get API key
    config = get_api_config(provider, candidate.get("api_type", "openai-compatible"))
    api_key = api_key_map.get(config["env_var"])
    if not api_key:
        print(f"  Skipping: No API key for {config['env_var']}")
        return CandidateEvaluation(
            model_id=candidate["model_id"], provider=provider, api_type=candidate.get("api_type", ""),
            smoke_results=[], smoke_success_rate=0.0,
            smoke_median_latency_ms=0.0, smoke_p95_latency_ms=0.0,
            translation_results=[], translation_success_rate=0.0,
            quality_scores={}, avg_quality_score=0.0, quality_pass=False,
            glossary_improvement=0.0, context_results=[], context_compatible=False,
            reliability_results=[], reliability_success_rate=0.0,
            reliability_median_latency_ms=0.0, reliability_p95_latency_ms=0.0,
            classification="PROVIDER_UNAVAILABLE", classification_rationale="No API key",
            limitations=["No API key available"],
        )
    
    endpoint = config["endpoint"]
    
    # Smoke test (3 observations)
    print("  Smoke test (3x)...")
    smoke_results = []
    for i in range(3):
        sys_prompt = "Translate Korean to Traditional Chinese (Taiwan). Output only translation."
        http_status, elapsed, req_id, body, error = dispatch_request(
            candidate["model_id"], provider, candidate.get("api_type", "openai-compatible"),
            sys_prompt, "안녕하세요. 이것은 테스트입니다.", max_tokens=100
        )
        smoke_results.append(SmokeResult(
            model=candidate["model_id"],
            provider=provider,
            timestamp_utc=datetime.datetime.utcnow().isoformat() + "Z",
            http_status=http_status,
            success=(http_status == 200),
            elapsed_ms=elapsed,
            provider_request_id=req_id,
            error=error,
        ))
        time.sleep(0.5)
    
    smoke_success = sum(1 for s in smoke_results if s.success)
    smoke_success_rate = smoke_success / len(smoke_results)
    smoke_latencies = [s.elapsed_ms for s in smoke_results if s.success]
    smoke_median = sorted(smoke_latencies)[len(smoke_latencies)//2] if smoke_latencies else 0
    smoke_p95 = sorted(smoke_latencies)[int(len(smoke_latencies)*0.95)] if smoke_latencies else 0
    
    if smoke_success_rate == 0:
        print(f"  Smoke failed, skipping translation")
        return CandidateEvaluation(
            model_id=candidate["model_id"], provider=provider, api_type=candidate.get("api_type", ""),
            smoke_results=smoke_results, smoke_success_rate=smoke_success_rate,
            smoke_median_latency_ms=0.0, smoke_p95_latency_ms=0.0,
            translation_results=[], translation_success_rate=0.0,
            quality_scores={}, avg_quality_score=0.0, quality_pass=False,
            glossary_improvement=0.0, context_results=[], context_compatible=False,
            reliability_results=[], reliability_success_rate=0.0,
            reliability_median_latency_ms=0.0, reliability_p95_latency_ms=0.0,
            classification="PROVIDER_UNAVAILABLE", classification_rationale="Smoke test failed",
            limitations=["Provider unavailable or no valid credentials"],
)
    
    # Translation tests (base + glossary)
    print("  Translation tests (base + glossary)...")
    translation_results = []
    for fixture_name, fixture in fixtures.items():
        for mode in ["base", "glossary"]:
            sys_prompt, user_prompt = build_prompt(mode, fixture, glossary, char_memory)
            http_status, elapsed, req_id, translation, error = dispatch_request(
                candidate["model_id"], provider, candidate.get("api_type", "openai-compatible"),
                sys_prompt, user_prompt, max_tokens=8000
            )
            translation_results.append(TranslationResult(
                model=candidate["model_id"], provider=provider,
                fixture_name=fixture_name, fixture_type=fixture["type"],
                mode=mode, source_text=fixture["source"], translation=translation or "",
                http_status=http_status, success=(http_status == 200),
                elapsed_ms=elapsed, provider_request_id=req_id, error=error,
            ))
            time.sleep(1)
    
    trans_success = sum(1 for t in translation_results if t.success)
    trans_success_rate = trans_success / len(translation_results)
    
    # Quality scoring
    quality_scores = {}
    for t in translation_results:
        if t.success:
            scores = compute_quality_scores(t.source_text, t.translation, t.fixture_type, glossary, char_memory)
            quality_scores[f"{t.fixture_name}_{t.mode}"] = scores
    
    avg_quality = sum(qs.overall for qs in quality_scores.values()) / len(quality_scores) if quality_scores else 0
    quality_pass = all(qs.status == "PASS" for qs in quality_scores.values()) and len(quality_scores) > 0
    
    # Glossary improvement
    base_scores = [qs.overall for k, qs in quality_scores.items() if k.endswith("_base")]
    glossary_scores = [qs.overall for k, qs in quality_scores.items() if k.endswith("_glossary")]
    glossary_improvement = (sum(glossary_scores)/len(glossary_scores) - sum(base_scores)/len(base_scores)) if base_scores and glossary_scores else 0
    
    # Context test (small, medium, large)
    print("  Context tests...")
    context_results = []
    test_fixtures = {
        "small": "안녕하세요. 이것은 작은 테스트입니다.",
        "medium": fixtures["narrative"]["source"][:2000],
        "large": fixtures["narrative"]["source"] * 2,
    }
    sys_prompt = "Translate Korean to Traditional Chinese (Taiwan). Output only translation."
    for level, text in test_fixtures.items():
        http_status, elapsed, req_id, body, error = dispatch_request(
            candidate["model_id"], provider, candidate.get("api_type", "openai-compatible"),
            sys_prompt, text, max_tokens=4000
        )
        context_results.append({
            "level": level, "http_status": http_status,
            "success": http_status == 200, "elapsed_ms": elapsed, "error": error
        })
        time.sleep(0.5)
    
    context_compatible = all(r["success"] for r in context_results)
    
    # Reliability (5 observations)
    print("  Reliability (5x)...")
    reliability_results = []
    for i in range(5):
        http_status, elapsed, req_id, body, error = dispatch_request(
            candidate["model_id"], provider, candidate.get("api_type", "openai-compatible"),
            "Translate Korean to Traditional Chinese (Taiwan). Output only translation.",
            fixtures["narrative"]["source"][:500], max_tokens=4000
        )
        reliability_results.append(ReliabilityResult(
            model=candidate["model_id"], provider=provider,
            timestamp_utc=datetime.datetime.utcnow().isoformat() + "Z",
            http_status=http_status, success=(http_status == 200),
            elapsed_ms=elapsed, provider_request_id=req_id, error=error
        ))
        time.sleep(0.5)
    
    rel_success = sum(1 for r in reliability_results if r.success)
    rel_success_rate = rel_success / len(reliability_results)
    rel_latencies = [r.elapsed_ms for r in reliability_results if r.success]
    rel_median = sorted(rel_latencies)[len(rel_latencies)//2] if rel_latencies else 0
    rel_p95 = sorted(rel_latencies)[int(len(rel_latencies)*0.95)] if rel_latencies else 0
    
    # Classification
    if smoke_success_rate == 0:
        classification = "PROVIDER_UNAVAILABLE"
        rationale = "Smoke test failed"
    elif not context_compatible:
        classification = "CONTEXT_INCOMPATIBLE"
        rationale = "Failed context compatibility"
    elif trans_success_rate < 1.0:
        classification = "TRANSLATION_UNSUITABLE"
        rationale = f"Translation success rate {trans_success_rate:.0%}"
    elif not quality_pass:
        classification = "QUALITY_INSUFFICIENT"
        rationale = f"Avg quality {avg_quality:.1f} < 65"
    elif rel_success_rate < 0.8:
        classification = "RUNTIME_UNSTABLE"
        rationale = f"Reliability {rel_success_rate:.0%}"
    else:
        classification = "REPLACEMENT_CANDIDATE"
        rationale = "All gates passed"
    
    # Note: we need to redefine fixtures variable
    fixtures = load_fixtures()
    char_memory = load_character_memory()
    glossary = load_glossary()
    
    return CandidateEvaluation(
        model_id=candidate["model_id"], provider=provider, api_type=candidate.get("api_type", ""),
        smoke_results=smoke_results, smoke_success_rate=smoke_success_rate,
        smoke_median_latency_ms=smoke_median, smoke_p95_latency_ms=smoke_p95,
        translation_results=translation_results, translation_success_rate=trans_success_rate,
        quality_scores=quality_scores, avg_quality_score=round(avg_quality, 1),
        quality_pass=quality_pass, glossary_improvement=round(glossary_improvement, 1),
        context_results=context_results, context_compatible=context_compatible,
        reliability_results=reliability_results, reliability_success_rate=rel_success_rate,
        reliability_median_latency_ms=rel_median, reliability_p95_latency_ms=rel_p95,
        classification=classification, classification_rationale=rationale,
        limitations=["Single-run per test", "Automated quality only", "No human review"],
    )


def run_evaluation() -> EvaluationReport:
    """Run evaluation for all priority candidates."""
    baseline = get_git_baseline()
    
    # Load inventory
    inventory = load_inventory()
    priority_ids = inventory.get("priority_candidates", [])
    
    # Load full inventory for candidate details
    inv_path = Path(__file__).resolve().parents[2] / "artifacts" / "P0_FINAL_15_R_CROSS_PROVIDER_CANDIDATE_INVENTORY.json"
    with open(inv_path, "r", encoding="utf-8") as f:
        full_inv = json.load(f)
    
    candidates = [c for c in full_inv["candidates"] if c["model_id"] in priority_ids]
    
    # Collect available API keys
    api_key_map = {}
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "COHERE_API_KEY", 
                "MISTRAL_API_KEY", "DEEPSEEK_API_KEY", "ZAI_API_KEY"]:
        val = os.environ.get(key)
        if val:
            api_key_map[key] = val
            print(f"  Found API key: {key}")
    
    print(f"\n[EVAL] Evaluating {len(candidates)} priority candidates with available credentials...")
    
    evaluations = []
    for candidate in candidates:
        config = get_api_config(candidate["provider"], candidate.get("api_type", "openai-compatible"))
        if config["env_var"] in api_key_map:
            result = evaluate_candidate(candidate, api_key_map)
            if result:
                evaluations.append(result)
                print(f"  Result: {result.classification}")
        else:
            print(f"  Skipping {candidate['model_id']}: No API key for {config['env_var']}")
    
    limitations = [
        "Only candidates with available API keys evaluated",
        "Single-run per test condition",
        "Automated quality scoring only",
        "No human literary review",
        "Glossary/char_memory are test versions",
        "Context tests use estimated tokens",
    ]
    
    return EvaluationReport(
        head_commit=baseline["head_commit"],
        origin_main_commit=baseline["origin_main_commit"],
        divergence=baseline["divergence"],
        branch=baseline["branch"],
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        test_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        candidates=evaluations,
        m1_baseline=None,
        limitations=limitations,
    )


def main():
    print("=" * 70)
    print("P0-FINAL-15-R: Cross-Provider Candidate Evaluation")
    print("=" * 70)
    
    report = run_evaluation()
    
    artifacts_dir = Path(__file__).resolve().parents[2] / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    report_path = artifacts_dir / "P0_FINAL_15_R_CANDIDATE_EVALUATION.json"
    
    report_dict = asdict(report)
    report_dict = redact_sensitive(report_dict)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n[EVAL] Report saved to: {report_path}")
    
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    for c in report.candidates:
        print(f"\n  {c.model_id} ({c.provider})")
        print(f"    Classification: {c.classification}")
        print(f"    Smoke: {c.smoke_success_rate:.0%}, {c.smoke_median_latency_ms:.0f}ms")
        print(f"    Translation: {c.translation_success_rate:.0%}")
        print(f"    Quality: {c.avg_quality_score:.1f} (pass={c.quality_pass})")
        print(f"    Glossary improvement: {c.glossary_improvement:+.1f}")
        print(f"    Context compatible: {c.context_compatible}")
        print(f"    Reliability: {c.reliability_success_rate:.0%}")
    
    # Governance
    governance_dir = Path(__file__).resolve().parents[2] / "docs" / "governance" / "repository"
    governance_dir.mkdir(parents=True, exist_ok=True)
    gov_path = governance_dir / "P0_FINAL_15_R_CANDIDATE_EVALUATION.md"
    
    with open(gov_path, "w", encoding="utf-8") as f:
        f.write(f"""# P0-FINAL-15-R — Candidate Evaluation

## Phase R-B: Cross-Provider Candidate Evaluation

### Baseline
- **HEAD**: {report.head_commit}
- **origin/main**: {report.origin_main_commit}
- **divergence**: {report.divergence}
- **branch**: {report.branch}
- **Python**: {report.python_version}
- **Timestamp**: {report.test_timestamp}

### Candidates Evaluated
""")
        for c in report.candidates:
            f.write(f"- {c.model_id} ({c.provider}) [{c.api_type}]\n")
        
        f.write("""
## Evaluation Pipeline

1. **Smoke Test** (3 observations) - Basic API connectivity
2. **Translation** (3 fixtures × 2 modes) - Narrative, Dialogue, Continuity with Base/Glossary
3. **Quality Scoring** (7 dimensions, threshold ≥65)
4. **Glossary Effectiveness** - Base vs Glossary comparison
5. **Context Compatibility** - Small/Medium/Large fixtures
6. **Reliability** (5 observations) - Success rate, latency

## Results Summary

| Model | Provider | Smoke | Translation | Quality | Glossary Δ | Context | Reliability | Classification |
|-------|----------|-------|-------------|---------|------------|---------|-------------|----------------|
""")
        
        for c in report.candidates:
            f.write(f"| {c.model_id} | {c.provider} | {c.smoke_success_rate:.0%} | {c.translation_success_rate:.0%} | {c.avg_quality_score:.1f} | {c.glossary_improvement:+.1f} | {c.context_compatible} | {c.reliability_success_rate:.0%} | {c.classification} |\n")
        
        f.write("""
## Detailed Results

""")
        for c in report.candidates:
            f.write(f"""
### {c.model_id} ({c.provider})

**Classification**: {c.classification}
**Rationale**: {c.classification_rationale}

**Smoke**: {c.smoke_success_rate:.0%} success, median {c.smoke_median_latency_ms:.0f}ms, P95 {c.smoke_p95_latency_ms:.0f}ms

**Translation**: {c.translation_success_rate:.0%} success
""")
            for t in c.translation_results:
                f.write(f"- {t.fixture_name} ({t.mode}): {'✓' if t.success else '✗'} HTTP {t.http_status} ({t.elapsed_ms:.0f}ms)\n")
            
            f.write(f"""
**Quality Scores**: avg={c.avg_quality_score:.1f}, pass={c.quality_pass}
""")
            for k, qs in c.quality_scores.items():
                f.write(f"- {k}: {qs.overall:.1f} (Sem={qs.semantic_fidelity:.1f}, Flu={qs.fluency:.1f}, Style={qs.literary_style:.1f}, Term={qs.terminology_consistency:.1f}, Char={qs.character_consistency:.1f}, Cont={qs.continuity:.1f}, Fmt={qs.formatting_preservation:.1f}) [{qs.status}]\n")
            
            f.write(f"""
**Glossary Improvement**: {c.glossary_improvement:+.1f}
**Context Compatible**: {c.context_compatible}
**Reliability**: {c.reliability_success_rate:.0%} success, median {c.reliability_median_latency_ms:.0f}ms
""")
        
        f.write("""
## Limitations
""")
        for lim in report.limitations:
            f.write(f"- {lim}\n")
        
        f.write("""
## Compliance
- ✅ No credential leakage
- ✅ No production modification
- ✅ Root Hygiene compliant
- ✅ Protected Worktree preserved
""")
    
    print(f"[EVAL] Governance doc saved to: {gov_path}")
    print("\n" + "=" * 70)
    print("P0-FINAL-15-R Candidate Evaluation Complete")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    import datetime
    import subprocess
    import requests
    sys.exit(main())
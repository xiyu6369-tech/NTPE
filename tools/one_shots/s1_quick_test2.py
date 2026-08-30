#!/usr/bin/env python3
"""Quick S1 test with proper encoding."""

import os
import time
import requests
import json

api_key = os.environ.get('NVIDIA_API_KEY')
endpoint = 'https://integrate.api.nvidia.com/v1/chat/completions'

def test_call(sys_prompt, user_prompt, max_tokens=100):
    payload = {
        'model': 'openai/gpt-oss-120b',
        'messages': [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'temperature': 0.15,
        'top_p': 0.85,
        'max_tokens': max_tokens,
        'stream': False
    }
    headers = {'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'}
    start = time.time()
    r = requests.post(endpoint, headers=headers, json=payload, timeout=(10, 60))
    elapsed = time.time() - start
    r.encoding = 'utf-8'
    try:
        data = r.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        return r.status_code, elapsed, content, data.get('id'), r.headers.get('Nvcf-Reqid')
    except:
        return r.status_code, elapsed, r.text, None, None

# Test 1: Simple translation
print("Test 1: Simple translation")
sys_prompt = "Translate Korean to Traditional Chinese (Taiwan). Output only translation."
result = test_call(sys_prompt, "안녕하세요. 이것은 테스트입니다.", 50)
print(f"  HTTP {result[0]} | {result[1]:.1f}s | {result[2][:60] if result[2] else 'EMPTY'}")

# Test 2: Narrative with glossary
print("\nTest 2: Narrative with glossary")
glossary = "정태의 → 鄭泰義, 카일 → 凱爾, 민수 → 旻秀, 지현 → 智賢, 김철수 → 金哲秀, 이영희 → 李英姬, 프라이빗풀 → 私人泳池, 라군 → 潟湖, 백사장 → 沙灘, 로비 → 大廳, 독일어 → 德語, 동행 → 同行, 베를린 → 柏林, 남국 → 南國, 섬 → 島嶼, 호텔 → 飯店, 형사 → 刑警, 파트너 → 搭檔, 원칙주의자 → 原則主義者, 연쇄 실종 사건 → 連環失蹤案, 현장 → 現場, 피해자 → 受害者, 공통점 → 共同點, 직관 → 直覺, 논리 → 邏輯, 증거 → 證據"

sys_prompt2 = f"""You are a professional literary translator specializing in Korean to Traditional Chinese (Taiwan) translation.
Output only the translation.

GLOSSARY (must follow exactly):
{glossary}"""

narrative = "정태의는 난감해하고 있었다. 그러나 실상 그것은 그가 난감해할 일은 아니었다. 먼 타국에 떼어놓고 온 괴물 같은 남자는 어쨌든 이지가 제대로 돌아가고 있는, 나름대로 이성적인 인간이었고, 그는 이 상황이 결코 정태의가 의도해서 벌어진 상황이 아니란 걸 이해해줄 것이다."

# Test at different context percentages
for pct in [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]:
    user_prompt = narrative[:int(len(narrative)*pct)]
    result = test_call(sys_prompt2, user_prompt, 2000)
    truncation = not (result[2] and result[2].rstrip().endswith(('。', '！', '？', '……', '"', '」')))
    print(f"  {int(pct*100)}%: HTTP {result[0]} | {result[1]:.1f}s | trunc={truncation} | len={len(result[2])}")

# Test 3: Dialogue with glossary
print("\nTest 3: Dialogue with glossary")
dialogue = '"정말 괜찮아?" 민수가 조심스럽게 물었다.\n\n지현은 고개를 끄덕이며 억지로 미소를 지었다. "응, 괜찮아. 그냥... 좀 피곤할 뿐이야."\n\n"아니, 네 눈빛이 그렇지 않아. 무슨 일 있어? 말해줘."'
result = test_call(sys_prompt2, dialogue, 1000)
print(f"  HTTP {result[0]} | {result[1]:.1f}s | len={len(result[2])}")

# Test 4: Continuity with glossary
print("\nTest 4: Continuity with glossary")
continuity = '김철수는 30년 경력의 형사였다. 그가 맡은 사건은 언제나 복잡했지만, 그는 특유的 직관으로 진실을 파헤쳐왔다. 그의 파트너 이영희는 그와 정반대였다. 논리와 증거만으로 사건을 풀어나가는 원칙주의자였다.'
result = test_call(sys_prompt2, continuity, 1000)
print(f"  HTTP {result[0]} | {result[1]:.1f}s | len={len(result[2])}")

print("\nAll quick tests complete!")
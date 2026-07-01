from translation.runtime import create_translation_runtime

job = {
    "job_id": "demo-066",
    "source_language": "ko",
    "target_language": "zh-TW",
    "segments": [
        {"segment_id": "demo-1", "index": 0, "source_text": "안녕하세요"},
        {"segment_id": "demo-2", "index": 1, "source_text": "테스트입니다"},
    ],
}

runtime = create_translation_runtime()
result = runtime.execute(job)
print(result["status"])
print(result["session"]["progress"])
for item in result["results"]:
    print(item["segment_id"], item.get("output_text", ""))

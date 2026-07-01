from translation.context_runtime import create_translation_context_runtime_adapter

job = {"job_id": "demo", "target_language": "zh-TW", "glossary": {"정태의": "鄭泰義"}}
segments = [
    {"segment_id": "s1", "index": 1, "source_text": "정태의는 웃었다."},
    {"segment_id": "s2", "index": 2, "source_text": "그는 걸었다."},
]
adapter = create_translation_context_runtime_adapter(job=job, window=1)
print(adapter.build_context(segments[0], segments))

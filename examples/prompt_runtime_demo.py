from translation.context_runtime import create_context_bundle
from translation.prompt_runtime import create_prompt_package

job = {"job_id": "demo", "source_language": "ko", "target_language": "zh-TW", "glossary": {"정태의": "鄭泰義"}}
segment = {"segment_id": "s1", "index": 1, "source_text": "정태의는 웃었다."}
context = create_context_bundle(segment=segment, job=job)
prompt = create_prompt_package(context)
print(prompt["messages"][-1]["content"])

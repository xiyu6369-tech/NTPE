import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from translation.segment_manager import TranslationSegmentManager
from translation.context_runtime import create_translation_context_runtime_adapter


def check(name, condition):
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)

print("NTPE Foundation-06.3 Translation Runtime E2E Test")
print("=================================================")
job = {"job_id": "e2e", "target_language": "zh-TW", "glossary": {"안녕": "你好"}}
segments = [
    {"segment_id": "s1", "index": 1, "source_text": "안녕"},
    {"segment_id": "s2", "index": 2, "source_text": "세계", "dependencies": ["s1"]},
]
manager = TranslationSegmentManager(segments)
adapter = create_translation_context_runtime_adapter(job=job, window=1)
first = manager.next()
ctx1 = adapter.build_context(first, manager.queue["segments"])
check("Job Created", job["job_id"] == "e2e")
check("Segment Ready", first["segment_id"] == "s1")
check("Context Built", ctx1["segment"]["segment_id"] == "s1")
manager.start("s1")
manager.complete("s1", "你好")
second = manager.next()
ctx2 = adapter.build_context(second, manager.queue["segments"])
check("Dependency Released", second["segment_id"] == "s2")
check("Previous Output", ctx2["previous_context"][0]["target_text"] == "你好")
manager.start("s2")
manager.complete("s2", "世界")
check("Runtime Completed", manager.metrics()["percent"] == 100.0)
print("PASS")

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.context_runtime import TranslationContextBuilder, validate_context_bundle
from translation.prompt_runtime import PromptRuntimeBuilder, validate_prompt_package
from translation.segment_manager import TranslationSegmentManager, create_segment_queue


def check(name, condition):
    print(f"{name:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)

print("NTPE Foundation-06.4 Prompt Runtime E2E Test")
print("============================================")

job = {"job_id": "job-e2e-064", "source_language": "ko", "target_language": "zh-TW", "glossary": {"일라이": "伊萊"}}
segments = [
    {"segment_id": "s1", "index": 1, "source_text": "A", "target_text": "甲", "status": "completed"},
    {"segment_id": "s2", "index": 2, "source_text": "일라이가 말했다.", "depends_on": ["s1"]},
]
manager = TranslationSegmentManager(segments)
seg = manager.next()
check("Segment Ready", seg["segment_id"] == "s2")
ctx_builder = TranslationContextBuilder(job=job, window=1)
ctx = ctx_builder.build(seg, segments)
check("Context Built", validate_context_bundle(ctx))
prompt_builder = PromptRuntimeBuilder()
pkg = prompt_builder.build(ctx)
check("Prompt Built", validate_prompt_package(pkg))
check("Glossary Injected", "일라이" in pkg["prompt_text"] and "伊萊" in pkg["prompt_text"])
check("Messages Ready", len(pkg["messages"]) == 2)
manager.complete("s2", "伊萊說道。")
check("Segment Completed", manager.metrics()["completed"] == 2)
print("PASS")

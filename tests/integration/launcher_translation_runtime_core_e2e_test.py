import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.runtime import create_translation_runtime, validate_runtime_result  # noqa: E402


def check(label, condition):
    print(f"{label:<30} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


print("NTPE Foundation-06.6 Translation Runtime Core E2E Test")
print("=" * 58)

runtime = create_translation_runtime()
job = {
    "job_id": "e2e-066",
    "source_language": "ko",
    "target_language": "zh-TW",
    "glossary": {"정태의": "鄭泰義"},
    "character_context": {"정태의": "主角固定譯名為鄭泰義"},
    "segments": [
        {"segment_id": "s1", "index": 0, "source_text": "정태의는 말했다."},
        {"segment_id": "s2", "index": 1, "source_text": "그는 고개를 끄덕였다."},
    ],
}

result = runtime.execute(job)
check("Runtime Valid", validate_runtime_result(result))
check("Session Complete", result["session"]["status"] == "completed")
check("All Segments", result["session"]["progress"]["completed"] == 2)
check("Context Component", "context_runtime" in result["manifest"]["components"])
check("Prompt Component", "prompt_runtime" in result["manifest"]["components"])
check("Executor Component", "executor" in result["manifest"]["components"])
check("Output Attached", bool(result["job"]["segments"][0].get("output_text")))
check("Runtime Events", len(result["manifest"]["events"]) >= 1)
print("PASS")

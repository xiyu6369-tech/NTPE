import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.runtime import create_translation_runtime, validate_runtime_result  # noqa: E402


def check(label, condition):
    print(f"{label:<24} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


print("NTPE Foundation-06.6 Translation Runtime Core Smoke Test")
print("=" * 57)
runtime = create_translation_runtime()
result = runtime.execute({"job_id": "smoke-066", "segments": [{"segment_id": "smoke-seg", "source_text": "안녕"}]})
check("Runtime Created", runtime.runtime_id == "translation-runtime-core")
check("Runtime Valid", validate_runtime_result(result))
check("Smoke Completed", result["status"] == "completed")
print("PASS")

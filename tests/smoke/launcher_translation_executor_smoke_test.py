import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.executor import create_translation_runtime_executor  # noqa: E402


def check(label, condition):
    print(f"{label:<26} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(label)


print("NTPE Foundation-06.5 Translation Executor Smoke Test")
print("=" * 54)
executor = create_translation_runtime_executor()
job = {"job_id": "smoke-job"}
segment = {"segment_id": "smoke-seg", "source_text": "테스트"}
result = executor.execute_segment(job, segment)
check("Executor Created", executor is not None)
check("Result Created", result["status"] == "completed")
check("Manifest Valid", executor.manifest()["version"] == "06.5")
print("PASS")

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translation.context_runtime import create_context_bundle
from translation.prompt_runtime import create_prompt_package, validate_prompt_package


def check(name, condition):
    print(f"{name:<26} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise AssertionError(name)

print("NTPE Foundation-06.4 Prompt Runtime Smoke Test")
print("==============================================")
ctx = create_context_bundle({"segment_id": "s", "source_text": "안녕"}, {"job_id": "j", "target_language": "zh-TW"})
pkg = create_prompt_package(ctx)
check("Prompt Created", bool(pkg["prompt_text"]))
check("Prompt Valid", validate_prompt_package(pkg))
print("PASS")

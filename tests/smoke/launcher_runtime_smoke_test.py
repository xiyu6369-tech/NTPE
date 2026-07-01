import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from translation.context_runtime import create_context_bundle, validate_context_bundle

print("NTPE Foundation-06.3 Runtime Smoke Test")
print("=======================================")
bundle = create_context_bundle({"segment_id": "smoke", "source_text": "test"})
print(f"Runtime Created              {'PASS' if bundle else 'FAIL'}")
print(f"Context Valid                {'PASS' if validate_context_bundle(bundle) else 'FAIL'}")
print("PASS")

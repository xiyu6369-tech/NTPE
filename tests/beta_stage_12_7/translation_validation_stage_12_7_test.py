"""Translation validation for Stage-12.7.

The validation checks that the new REST middleware/auth hooks are additive and do
not disturb the existing REST resource + Runtime API translation path contract.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import create_rest_api


def test_translation_validation_stage_12_7():
    api = create_rest_api()
    api.middleware.add_after(lambda context, response: response)
    health = api.handle("GET", "/health")
    assert health.status_code == 200
    assert health.body["ok"] is True
    manifest = api.handle("GET", "/v1/runtime/manifest")
    assert manifest.status_code == 200
    assert manifest.body["ok"] is True
    assert api.manifest()["middleware_api"]["additive_only"] is True
    assert api.manifest()["auth_hooks"]["default_policy"] == "allow_when_no_hooks"


if __name__ == "__main__":
    test_translation_validation_stage_12_7()
    print("PASS")

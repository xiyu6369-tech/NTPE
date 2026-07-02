"""Translation validation smoke test for Stage-12.1.

The REST layer must reach the translation runtime only through Runtime API routes.
This deterministic check verifies the external layer is additive and preserves the
frozen Runtime API ping/manifest path used by translation workflows.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from external_api import create_rest_api


def test_translation_validation_stage_12_1():
    api = create_rest_api()
    health = api.handle("GET", "/health")
    assert health.status_code == 200
    assert health.body["data"]["pong"] is True
    manifest = api.handle("GET", "/v1/runtime/manifest")
    assert manifest.status_code == 200
    assert "runtime.ping" in manifest.body["data"]["operations"]


if __name__ == "__main__":
    test_translation_validation_stage_12_1()
    print("PASS")

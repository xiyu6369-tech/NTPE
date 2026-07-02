"""Translation validation smoke test for Stage-11.8.

This validation remains intentionally offline and deterministic. It verifies that
the Runtime API freeze layer is additive and does not remove the previously
available runtime facade operation used by translation workflows.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime_api import RuntimeApi, RuntimeApiFreezeValidator


def test_translation_validation_stage_11_8():
    api = RuntimeApi(metadata={"validation": "translation"})
    response = api.execute("runtime.ping")
    assert response.ok is True
    assert response.data["pong"] is True
    report = RuntimeApiFreezeValidator().validate_runtime_api(api)
    assert report.frozen is True


if __name__ == "__main__":
    test_translation_validation_stage_11_8()
    print("PASS")

"""Compatibility guard for Stage-11.7 additive Middleware API."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime_api import RuntimeApi, RuntimeMiddlewareApi


def main():
    api = RuntimeApi()
    before = set(api.operations())
    RuntimeMiddlewareApi(runtime_api=api)
    after = set(api.operations())
    assert "runtime.ping" in after
    assert "runtime.manifest" in after
    assert before.issubset(after)
    assert "middleware.execute" in after
    assert api.execute("runtime.ping").ok is True
    print("PASS")


if __name__ == "__main__":
    main()

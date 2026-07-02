"""Compatibility guard for Stage-11.6 additive Resource API."""
from runtime_api import RuntimeApi, RuntimeResourceApi


def main():
    api = RuntimeApi()
    before = set(api.operations())
    RuntimeResourceApi(runtime_api=api)
    after = set(api.operations())
    assert "runtime.ping" in after
    assert "runtime.manifest" in after
    assert before.issubset(after)
    assert "resource.create" in after
    print("PASS")


if __name__ == "__main__":
    main()

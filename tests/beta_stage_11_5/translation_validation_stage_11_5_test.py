"""Translation validation guard for Stage-11.5.

This smoke test verifies the Runtime Event API remains additive and does not
remove existing Runtime API surfaces used by translation validation flows.
"""
from runtime_api import RuntimeApi, RuntimeEventApi


def main():
    api = RuntimeApi()
    RuntimeEventApi(runtime_api=api)
    required = {
        "runtime.ping",
        "runtime.manifest",
        "event.publish",
        "event.summary",
    }
    missing = required.difference(api.operations())
    if missing:
        raise AssertionError(f"missing operations: {sorted(missing)}")
    print("Translation Validation Stage-11.5: PASS")


if __name__ == "__main__":
    main()

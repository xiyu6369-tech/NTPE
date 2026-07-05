from core.ai_provider import MockProvider, ProviderObservabilityRuntime, ProviderRequest


def main() -> int:
    runtime = ProviderObservabilityRuntime()
    response = runtime.execute_provider(MockProvider(name="custom", response_text="ok"), ProviderRequest(prompt="stage 14.5"))
    snapshot = runtime.snapshot()
    checks = {
        "Response": response.text == "ok",
        "Stage": snapshot["stage"] == "NTPE 1.2 Professional Stage-14.5",
        "Metrics": snapshot["provider_metrics"]["custom"]["success_count"] == 1,
        "Events": len(snapshot["events"]) >= 2,
        "Traces": len(snapshot["traces"]) == 1,
        "Diagnostics": snapshot["diagnostics"]["healthy"] is True,
        "Prometheus": "ntpe_provider_requests_total" in runtime.export_prometheus(),
    }
    print("NTPE 1.2 Professional Stage-14.5 Provider Observability Test")
    print("=" * 64)
    for name, ok in checks.items():
        print(f"{name:24} {'PASS' if ok else 'FAIL'}")
    if all(checks.values()):
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

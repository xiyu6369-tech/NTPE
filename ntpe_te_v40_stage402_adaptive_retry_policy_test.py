
from core.translation_reliability import AdaptiveRetryPolicy


def check(name, condition):
    print(f"{name:<42} {'PASS' if condition else 'FAIL'}")
    if not condition:
        raise SystemExit(1)


def main():
    print("NTPE TE-v4.0 Stage-4.0.2 Adaptive Retry Policy Test")
    print("=" * 74)

    policy = AdaptiveRetryPolicy()

    retry_503 = policy.decide({
        "outcome": "http_503",
        "attempt": 1,
        "max_attempts": 5,
        "timeout_seconds": 180,
        "chunk_size": 600,
    })
    check("503 Retry Enabled", retry_503["retry"] is True)
    check("503 Backoff", retry_503["delay_seconds"] == 10)
    check("503 Chunk Unchanged", retry_503["next_chunk_size"] == 600)

    timeout = policy.decide({
        "outcome": "read_timeout",
        "attempt": 1,
        "max_attempts": 5,
        "timeout_seconds": 180,
        "chunk_size": 600,
    })
    check("Timeout Retry Enabled", timeout["retry"] is True)
    check("Timeout Increased", timeout["next_timeout_seconds"] > 180)
    check("Timeout Chunk Reduced", timeout["next_chunk_size"] == 300)

    not_attempted = policy.decide({
        "outcome": "provider_not_attempted",
        "attempt": 0,
        "max_attempts": 5,
        "chunk_size": 600,
    })
    check("Provider Rebuild Requested", not_attempted["rebuild_provider_session"] is True)
    check("Provider Retry Enabled", not_attempted["retry"] is True)

    too_short = policy.decide({
        "outcome": "too_short",
        "attempt": 0,
        "max_attempts": 5,
        "chunk_size": 600,
    })
    check("Too Short Immediate Retry", too_short["delay_seconds"] == 0)
    check("Too Short Chunk Reduced", too_short["next_chunk_size"] == 300)

    exhausted = policy.decide({
        "outcome": "http_503",
        "attempt": 5,
        "max_attempts": 5,
        "chunk_size": 600,
    })
    check("Attempt Limit Stops", exhausted["stop"] is True)
    check("Attempt Limit No Retry", exhausted["retry"] is False)

    auth_error = policy.decide({
        "outcome": "authentication_error",
        "attempt": 0,
        "max_attempts": 5,
    })
    check("Authentication Not Retried", auth_error["retry"] is False)
    check("Authentication Stops", auth_error["stop"] is True)

    success = policy.decide({"outcome": "success"})
    check("Success No Retry", success["retry"] is False)
    check("Success Stops", success["stop"] is True)

    switch = policy.decide(
        {
            "outcome": "http_503",
            "attempt": 2,
            "max_attempts": 5,
        },
        {
            "allow_provider_switch": True,
            "provider_switch_after_attempt": 3,
        },
    )
    check("Provider Switch Suggested", switch["switch_provider"] is True)

    for decision in [
        retry_503,
        timeout,
        not_attempted,
        too_short,
        exhausted,
        auth_error,
        success,
        switch,
    ]:
        check("Decision Valid", policy.validate_decision(decision))

    check("No Provider Call", retry_503["metadata"]["provider_called"] is False)
    check("No HTTP Call", retry_503["metadata"]["http_called"] is False)
    check("No API Key Access", retry_503["metadata"]["api_key_accessed"] is False)
    check("No Sleep Executed", retry_503["metadata"]["sleep_executed"] is False)

    print("NTPE TE-v4.0 Stage-4.0.2 Adaptive Retry Policy PASS")


if __name__ == "__main__":
    main()

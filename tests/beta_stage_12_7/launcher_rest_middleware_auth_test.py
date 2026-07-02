"""Launcher for Stage-12.7 REST Middleware / Auth Hooks."""
from rest_middleware_auth_test import (
    test_after_middleware_can_annotate_response,
    test_before_middleware_can_short_circuit,
    test_default_auth_is_backward_compatible,
    test_required_header_auth_hook,
    test_rest_middleware_auth_created,
)


def main():
    checks = [
        ("REST Middleware Auth Created", test_rest_middleware_auth_created),
        ("Default Auth Compatible", test_default_auth_is_backward_compatible),
        ("Required Header Auth", test_required_header_auth_hook),
        ("Before Middleware", test_before_middleware_can_short_circuit),
        ("After Middleware", test_after_middleware_can_annotate_response),
    ]
    print("NTPE Stage-12.7 REST Middleware / Auth Hooks Test")
    print("=" * 55)
    for name, fn in checks:
        fn()
        print(f"{name:<34} PASS")
    print("PASS")


if __name__ == "__main__":
    main()

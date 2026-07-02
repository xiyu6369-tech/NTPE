"""Launcher for Stage-12.2 REST Session API."""
from rest_session_api_test import (
    test_create_get_list_session,
    test_method_validation,
    test_rest_session_api_created,
    test_session_not_found,
    test_session_transitions_and_resume_state,
)


def main():
    checks = [
        ("REST Session API Created", test_rest_session_api_created),
        ("Create Get List Session", test_create_get_list_session),
        ("Session Transitions", test_session_transitions_and_resume_state),
        ("Session Not Found", test_session_not_found),
        ("Method Validation", test_method_validation),
    ]
    print("NTPE Stage-12.2 REST Session API Test")
    print("=" * 48)
    for name, fn in checks:
        fn()
        print(f"{name:<32} PASS")
    print("PASS")


if __name__ == "__main__":
    main()

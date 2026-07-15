from batch5a1_parity_support import characterize_context, fixture_cases


def test_context_characterization_is_deterministic_and_exposes_non_parity() -> None:
    for case in fixture_cases("context"):
        first = characterize_context(case)
        second = characterize_context(case)
        assert first == second
        assert first["status"] == "PARITY_FAILED"
        assert not first["value_equal"] and not first["input_mutated"]

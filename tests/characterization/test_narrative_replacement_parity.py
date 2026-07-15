from batch5a1_parity_support import characterize_narrative, fixture_cases


def test_narrative_characterization_is_deterministic_and_partial() -> None:
    for case in fixture_cases("narrative"):
        first = characterize_narrative(case)
        second = characterize_narrative(case)
        assert first == second
        assert first["status"] == "PARITY_PARTIAL"
        assert not first["value_equal"] and not first["input_mutated"]

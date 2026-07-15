from batch5a1_parity_support import characterize_voice, fixture_cases


def test_voice_characterization_is_deterministic_and_partial() -> None:
    for case in fixture_cases("voice"):
        first = characterize_voice(case)
        second = characterize_voice(case)
        assert first == second
        assert first["status"] == "PARITY_PARTIAL"
        assert not first["value_equal"] and not first["input_mutated"]

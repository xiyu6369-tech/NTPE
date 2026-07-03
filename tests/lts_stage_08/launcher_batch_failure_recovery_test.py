from lts.batch_translation_runtime import parse_args


def test_stage08_launcher_parse_continue_mode():
    options = parse_args(['input', 'output', '--continue-on-failure', '--quiet-progress'])
    assert options.continue_on_failure is True
    assert options.progress is False

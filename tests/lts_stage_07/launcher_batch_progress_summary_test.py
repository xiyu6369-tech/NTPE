from lts.batch_translation_runtime import parse_args


def test_stage07_parse_quiet_progress_flag():
    options = parse_args(['input', 'output', '--quiet-progress'])
    assert options.progress is False

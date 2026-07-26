from dataclasses import fields

import pytest

from core.controlled_multi_chunk_translation_canary.models import (
    MultiChunkCanaryRequest,
)
from core.controlled_multi_chunk_translation_canary.policy import (
    AUTHORIZED_ARTIFACT_ROOT_OVERRIDES,
    OUTPUT_ROOT,
    STAGE744_OUTPUT_ROOT,
)
from verification.controlled_runtime.controlled_multi_chunk_translation_stage74_real_canary import (
    main,
)


def test_default_and_authorized_override_are_exact_contract_values():
    assert OUTPUT_ROOT == "artifacts/controlled_multi_chunk_translation_stage743"
    assert STAGE744_OUTPUT_ROOT == (
        "artifacts/controlled_multi_chunk_translation_stage744"
    )
    assert AUTHORIZED_ARTIFACT_ROOT_OVERRIDES == (STAGE744_OUTPUT_ROOT,)


def test_request_identity_contract_contains_artifact_root():
    assert "artifact_root" in {
        item.name for item in fields(MultiChunkCanaryRequest) if item.init
    }


def test_real_canary_cli_exposes_explicit_artifact_root_option(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert "--artifact-root ARTIFACT_ROOT" in help_text
    assert "--authorize-real-provider" in help_text

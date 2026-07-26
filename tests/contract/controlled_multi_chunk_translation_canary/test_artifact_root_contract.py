from dataclasses import fields

import pytest

from core.controlled_multi_chunk_translation_canary.models import (
    MultiChunkCanaryRequest,
)
from core.controlled_multi_chunk_translation_canary.policy import (
    AUTHORIZED_ARTIFACT_ROOT_OVERRIDES,
    OUTPUT_ROOT,
    PRIOR_CANARY_ROOTS,
    STAGE744_OUTPUT_ROOT,
    STAGE746_OUTPUT_ROOT,
)
from verification.controlled_runtime.controlled_multi_chunk_translation_stage74_real_canary import (
    main,
)


def test_default_and_authorized_override_are_exact_contract_values():
    assert OUTPUT_ROOT == "artifacts/controlled_multi_chunk_translation_stage743"
    assert STAGE744_OUTPUT_ROOT == (
        "artifacts/controlled_multi_chunk_translation_stage744"
    )
    assert STAGE746_OUTPUT_ROOT == (
        "artifacts/controlled_multi_chunk_translation_stage746"
    )
    assert AUTHORIZED_ARTIFACT_ROOT_OVERRIDES == (
        STAGE744_OUTPUT_ROOT,
        STAGE746_OUTPUT_ROOT,
    )


def test_prior_canary_roots_contract():
    assert OUTPUT_ROOT in PRIOR_CANARY_ROOTS
    assert STAGE744_OUTPUT_ROOT in PRIOR_CANARY_ROOTS
    assert STAGE746_OUTPUT_ROOT not in PRIOR_CANARY_ROOTS
    assert len(PRIOR_CANARY_ROOTS) == 2


def test_stage746_not_in_prior_canary_roots():
    assert STAGE746_OUTPUT_ROOT not in PRIOR_CANARY_ROOTS


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
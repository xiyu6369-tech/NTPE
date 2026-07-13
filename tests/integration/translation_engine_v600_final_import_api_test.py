from dataclasses import FrozenInstanceError

import core.translation_release as release
from core.translation_discipline import build_translation_discipline_freeze
from core.translation_evidence import build_translation_evidence_freeze
from core.translation_naturalness import build_translation_naturalness_freeze


def test_final_release_import_api_surface() -> None:
    expected = {"TEV6ReleaseContract", "build_te_v6_release_contract", "validate_te_v6_release"}
    assert expected.issubset(set(release.__all__))
    contract = release.build_te_v6_release_contract()
    try:
        contract.frozen = False  # type: ignore[misc]
        raise AssertionError("contract is mutable")
    except FrozenInstanceError:
        pass
    assert build_translation_discipline_freeze().frozen
    assert build_translation_evidence_freeze().frozen
    assert build_translation_naturalness_freeze().to_metadata()["frozen"]

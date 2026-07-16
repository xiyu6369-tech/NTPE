from __future__ import annotations

from dataclasses import asdict, replace
import json

import pytest
import core.multilingual_profiles as mp


@pytest.mark.parametrize("source,profile_id", [("ko", "literary-ko-zh-hant"), ("ja", "literary-ja-zh-hant"), ("en", "literary-en-zh-hant")])
def test_exact_profile_selection(source, profile_id):
    result = mp.select_language_profile(source, "zh-Hant")
    assert result.status == "selected" and result.profile.profile_id == profile_id
    assert result == mp.select_language_profile(source, "zh-Hant")


@pytest.mark.parametrize("source,target,status", [("fr", "zh-Hant", "unsupported_pair"), ("ko", "zh-TW", "unsupported_pair"), ("ja", "zh-CN", "unsupported_pair"), (None, "zh-Hant", "invalid")])
def test_unsupported_pair_fails_closed(source, target, status):
    result = mp.select_language_profile(source, target)
    assert result.status == status and result.profile is None


def test_unknown_profile_and_version_never_fallback():
    assert mp.select_language_profile("ko", "zh-Hant", requested_profile_id="literary-ja-zh-hant").status == "not_found"
    assert mp.select_language_profile("ko", "zh-Hant", requested_version="9.9").status == "version_mismatch"


def test_common_target_contract_is_shared_and_safe():
    profiles = mp.list_language_profiles()
    assert all(p.target_rules is mp.COMMON_TARGET_POLICY for p in profiles)
    assert all(p.target_language == "zh-Hant" and p.target_rules.dialogue_quotes == "「」" for p in profiles)
    assert all(not p.target_rules.force_taiwan_terms and p.target_rules.preserve_era_context for p in profiles)
    required = {"no_omission", "no_addition", "no_summary", "no_full_name_completion", "preserve_deliberate_ambiguity"}
    assert all(required <= set(p.target_rules.requirements) for p in profiles)


@pytest.mark.parametrize("source", ["ko", "ja", "en"])
def test_name_policy_forbids_completion_and_automatic_transliteration(source):
    p = mp.select_language_profile(source, "zh-Hant").profile
    assert p.name_policy.full_name_completion_policy == "forbidden_without_evidence"
    assert p.name_policy.transliteration_strategy != "automatic_transliteration"
    assert "human-approved" in p.name_policy.approved_variant_policy


def test_korean_language_specific_contract():
    p = mp.get_language_profile("literary-ko-zh-hant")
    assert p.pronoun_policy.subject_omission_expected and p.pronoun_policy.unresolved_reference_policy == "preserve_unresolved"
    assert {"존댓말", "반말", "하십시오체", "해요체", "해체", "하게체", "하오체"} <= set(p.honorific_policy.register_levels)
    assert "always_use_您" in p.honorific_policy.forbidden_simplifications
    assert "long_adnominal_literalism" in p.source_rules.structure_risks


def test_japanese_language_specific_contract():
    p = mp.get_language_profile("literary-ja-zh-hant")
    assert p.pronoun_policy.subject_omission_expected
    assert "change_agent_for_humble_or_respectful" in p.honorific_policy.forbidden_simplifications
    assert "topic_subject_confusion" in p.source_rules.structure_risks
    assert "giving_receiving_agent" in p.source_rules.structure_risks
    assert any("not_gender_proof" in x for x in p.pronoun_policy.pronoun_surface_to_identity_rules)


def test_english_language_specific_contract():
    p = mp.get_language_profile("literary-en-zh-hant")
    assert not p.pronoun_policy.subject_omission_expected
    assert "singular_they_no_gender_assignment" in p.pronoun_policy.pronoun_surface_to_identity_rules
    assert {"conditional", "perfect", "subjunctive"} <= set(p.source_rules.temporal_aspect_rules)
    assert "passive_literalism" in p.source_rules.structure_risks and "idiom_literalism" in p.source_rules.structure_risks


@pytest.mark.parametrize("source,text,script", [("ko", "그는 돌아왔다。", "Hangul"), ("ja", "彼はかえった。", "Hiragana"), ("ja", "彼はカエッタ。", "Katakana")])
def test_ko_ja_residue_detected(source, text, script):
    p = mp.select_language_profile(source, "zh-Hant").profile
    findings = mp.detect_source_residue(text, p)
    assert findings and any(x["script"] == script and x["blocking"] for x in findings)


def test_english_residue_does_not_block_legal_names_or_abbreviations():
    p = mp.get_language_profile("literary-en-zh-hant")
    assert not mp.detect_source_residue("Alice 與 NASA。", p)
    findings = mp.detect_source_residue("He should leave now because it is late。", p)
    assert findings and findings[0]["blocking"]


def test_residue_finding_schema():
    item = mp.detect_source_residue("아직。", mp.get_language_profile("literary-ko-zh-hant"))[0]
    assert {"text", "scope", "script", "confidence", "allowed_by_policy", "blocking", "reason"} == set(item)


def test_quality_rule_catalog_is_explicit_not_a_score():
    for profile in mp.list_language_profiles():
        assert len(profile.quality_rules) == 14
        assert all(r.evidence_required and r.applicability == f"{profile.source_language}->zh-Hant" for r in profile.quality_rules)
        assert all(not hasattr(r, "naturalness_score") for r in profile.quality_rules)


def test_fingerprint_deterministic_and_timestamp_display_excluded():
    p = mp.get_language_profile("literary-ko-zh-hant")
    assert p.fingerprint == mp.build_language_profile_fingerprint(p)
    changed = replace(p, display_name="Display only", updated_at="2099-01-01T00:00:00Z", status="frozen")
    assert mp.build_language_profile_fingerprint(changed) == p.fingerprint
    assert set(mp.IDENTITY_EXCLUDED_FIELDS) == {"display_name", "status", "created_at", "updated_at", "fingerprint"}


def test_version_rule_and_language_change_fingerprint():
    p = mp.get_language_profile("literary-en-zh-hant")
    assert mp.build_language_profile_fingerprint(replace(p, profile_version="1.1")) != p.fingerprint
    rule = replace(p.quality_rules[0], description="changed rule")
    assert mp.build_language_profile_fingerprint(replace(p, quality_rules=(rule,) + p.quality_rules[1:])) != p.fingerprint
    assert mp.build_language_profile_fingerprint(replace(p, source_language="ko")) != p.fingerprint


def test_profile_identities_are_distinct_and_cache_complete():
    identities = [mp.build_cache_profile_identity(p) for p in mp.list_language_profiles()]
    assert len({x["language_profile_fingerprint"] for x in identities}) == 3
    assert all(set(x) == {"language_profile_id", "language_profile_version", "language_profile_fingerprint", "source_language", "target_language"} for x in identities)


def test_memory_hints_never_upgrade_inference():
    for p in mp.list_language_profiles():
        hints = mp.build_character_memory_hints(p)
        assert not hints["creates_approved_memory"] and hints["human_approved_priority"] and not hints["gender_inference_confirmed"]
        context = mp.build_context_scene_hints(p)
        assert context["origin"] == "rule_derived" and not context["forces_reference_resolution"] and context["scene_memory_remains_authority"]


def test_polish_triggers_are_language_specific_not_approval():
    views = [mp.build_polish_profile_view(p) for p in mp.list_language_profiles()]
    assert len({view["trigger_types"][0] for view in views}) == 3
    assert all(not view["trigger_is_semantic_approval"] and not view["provider_state_controlled"] for view in views)


def test_semantic_hints_do_not_decide_batch6_pass():
    for p in mp.list_language_profiles():
        hints = mp.build_semantic_verification_hints(p)
        assert hints["verification_authority"] == "LCR Batch 6" and not hints["can_decide_pass"]
        identity = mp.build_verification_profile_identity(p)
        assert not identity["profile_can_accept_polish"] and not identity["fail_closed_threshold_lowered"]


@pytest.mark.parametrize("profile_id", ["literary-ko-zh-hant", "literary-ja-zh-hant", "literary-en-zh-hant"])
def test_serialization_roundtrip_deterministic(profile_id):
    p = mp.get_language_profile(profile_id)
    encoded = mp.serialize_language_profile(p)
    assert mp.serialize_language_profile(mp.deserialize_language_profile(encoded)) == encoded


@pytest.mark.parametrize("mutator", [lambda x: x.update(schema_version="9.9"), lambda x: x.update(profile_version="9.9"), lambda x: x.update(target_language="zh-TW"), lambda x: x.pop("name_policy"), lambda x: x.update(output_path="../escape")])
def test_invalid_serialized_profile_fails_closed(mutator):
    value = json.loads(mp.serialize_language_profile(mp.get_language_profile("literary-ko-zh-hant")))
    mutator(value)
    with pytest.raises(ValueError): mp.deserialize_language_profile(json.dumps(value, ensure_ascii=False))


def test_duplicate_active_profile_rejected():
    p = replace(mp.get_language_profile("literary-ko-zh-hant"), status="active")
    with pytest.raises(ValueError): mp.validate_registry((p, replace(p, profile_id="duplicate")))


def test_public_api_has_no_runtime_provider_prompt_or_translation_executor():
    assert not {"translate", "execute_provider", "route_provider", "build_prompt", "run_runtime", "assemble_output"} & set(mp.__all__)

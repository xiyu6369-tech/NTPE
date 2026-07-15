from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from core.context import ContextBuilder
from core.literary import CharacterContext, NarrativeContext
from core.literary.literary_style_normalizer import normalize_literary_style
from core.narrative import NarrativeIntelligenceEngine
from core.narrative.literary_style import LiteraryStyleRulesEngine
from core.voice import VoiceProfile


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/architecture_consolidation/batch5a1"


def fixture_cases(domain: str) -> list[dict[str, Any]]:
    import json
    payload = json.loads((FIXTURES / f"{domain}_cases.json").read_text(encoding="utf-8"))
    return payload["cases"]


def _narrative_engine() -> NarrativeIntelligenceEngine:
    style = LiteraryStyleRulesEngine.__new__(LiteraryStyleRulesEngine)
    style.root = ROOT
    style.rules_path = ROOT / "unused"
    style.rules = {
        "rules": [{"triggers": ["rain", "雨"], "instruction": "preserve atmosphere"}],
        "principles": ["deterministic"], "rewrite_preferences": [], "forbidden": [],
    }
    engine = NarrativeIntelligenceEngine.__new__(NarrativeIntelligenceEngine)
    engine.root = ROOT
    engine.literary_style = style
    return engine


def _voice_profile() -> VoiceProfile:
    profile = VoiceProfile.__new__(VoiceProfile)
    profile.root = ROOT
    profile.path = ROOT / "unused"
    profile.data = {"profiles": {
        "林真": {"source_names": ["림진"], "voice": ["quiet"], "dialogue_style": "reserved", "narration_style": "close", "avoid": ["shouting"]},
        "泰義": {"source_names": ["태의"], "voice": ["measured"], "dialogue_style": "direct", "narration_style": "observant", "avoid": []},
    }}
    return profile


def legacy_context(case: dict[str, Any]) -> Any:
    return ContextBuilder(max_chars=case["max_chars"]).build(deepcopy(case["states"]), previous_tail=case["previous"])


def replacement_context(case: dict[str, Any]) -> Any:
    return {
        "character": CharacterContext.analyze(case["text"], case["locked"], case["previous"]).to_dict(),
        "narrative": NarrativeContext.analyze(case["text"], case["previous"]).to_dict(),
    }


def characterize_context(case: dict[str, Any]) -> dict[str, Any]:
    before = deepcopy(case)
    legacy = legacy_context(case)
    replacement = replacement_context(case)
    return {"case_id": case["id"], "legacy": legacy, "replacement": replacement, "return_type_equal": type(legacy) is type(replacement), "value_equal": legacy == replacement, "input_mutated": case != before, "status": "PARITY_FAILED"}


def legacy_narrative(case: dict[str, Any]) -> Any:
    return _narrative_engine().analyze(case["text"])


def replacement_narrative(case: dict[str, Any]) -> Any:
    replacement_context = NarrativeContext.analyze(case["text"], case["previous"])
    return {"context": replacement_context.to_dict(), "normalized_text": normalize_literary_style(case["text"])}


def characterize_narrative(case: dict[str, Any]) -> dict[str, Any]:
    before = deepcopy(case)
    legacy = legacy_narrative(case)
    replacement = replacement_narrative(case)
    return {"case_id": case["id"], "legacy": legacy, "replacement": replacement, "return_type_equal": type(legacy) is type(replacement), "value_equal": legacy == replacement, "input_mutated": case != before, "status": "PARITY_PARTIAL"}


def legacy_voice(case: dict[str, Any]) -> Any:
    return _voice_profile().match(case["text"])


def replacement_voice(case: dict[str, Any]) -> Any:
    return CharacterContext.analyze(case["text"], case["locked"]).to_dict()


def characterize_voice(case: dict[str, Any]) -> dict[str, Any]:
    before = deepcopy(case)
    legacy = legacy_voice(case)
    replacement = replacement_voice(case)
    legacy_names = [row["target_name"] for row in legacy]
    replacement_names = replacement["current_focus"]
    return {"case_id": case["id"], "legacy": legacy, "replacement": replacement, "return_type_equal": type(legacy) is type(replacement), "value_equal": legacy == replacement, "overlap_names": sorted(set(legacy_names) & set(replacement_names)), "input_mutated": case != before, "status": "PARITY_PARTIAL"}


def characterize_domain(domain: str) -> list[dict[str, Any]]:
    function = {"context": characterize_context, "narrative": characterize_narrative, "voice": characterize_voice}[domain]
    return [function(case) for case in fixture_cases(domain)]


def exception_observation(domain: str) -> dict[str, Any]:
    calls = {
        "context": (lambda: ContextBuilder().build(None), lambda: CharacterContext.analyze(None, {})),
        "narrative": (lambda: _narrative_engine().analyze(None), lambda: NarrativeContext.analyze(None)),
        "voice": (lambda: _voice_profile().match(None), lambda: CharacterContext.analyze(None, {})),
    }
    observations = []
    for label, call in zip(("legacy", "replacement"), calls[domain]):
        try:
            call()
            observations.append({"side": label, "exception_type": None, "message_category": "none", "failure_timing": "none"})
        except Exception as exc:
            observations.append({"side": label, "exception_type": type(exc).__name__, "message_category": "invalid_type", "failure_timing": "call"})
    return {"domain": domain, "observations": observations, "parity": observations[0]["exception_type"] == observations[1]["exception_type"]}

from __future__ import annotations

from .location import DefectLocation
from .model import TranslationDefect
from .validator import validate_defects

REVIEW_PATH = "artifacts/te_v7_stage10101/review/TE_V7_STAGE10101_TRANSLATION_REVIEW.txt"


def _location(locator: str) -> DefectLocation:
    return DefectLocation(REVIEW_PATH, locator)


def initial_human_confirmed_defects() -> tuple[TranslationDefect, ...]:
    rows = (
        TranslationDefect("TQ-DEF-A", "lexical_choice", ("chinese_fluency", "narrative_naturalness"), "high", _location("human-note-A-source"), _location("phrase:相當理性的人間"), "인간", "相當理性的人間", "Use a contextually valid expression for a rational person.", "理性的人／講得通道理的人", "人間 does not denote a person in this context.", 1.0, "human_review_stage10101", True, False, {"suggestion_only": True, "approved_translation": None}),
        TranslationDefect("TQ-DEF-B", "omission", ("context_continuity", "semantic_precision"), "critical", _location("human-note-B-source-clause"), _location("missing-clause"), "沒有直達交通，必須另搭小型飛機進入島嶼", None, "Preserve the reviewed transport and island-access clause.", "補回交通與進島方式資訊", "A reviewed scene-setting clause is absent from the translation.", 1.0, "human_review_stage10101", True, True, {"dimensions": ["completeness", "fidelity"], "suggestion_only": True, "approved_translation": None}),
        TranslationDefect("TQ-DEF-C", "semantic_mistranslation", ("action_intensity",), "high", _location("human-note-C-source"), _location("phrase:足足哀號了三天"), "氣得幾乎臥床三天", "足足哀號了三天", "Preserve anger-induced illness or bedrest rather than wailing.", "氣得幾乎臥床三天", "The action and emotional consequence are mistranslated.", 1.0, "human_review_stage10101", True, False, {"dimensions": ["fidelity"], "suggestion_only": True, "approved_translation": None}),
        TranslationDefect("TQ-DEF-D", "semantic_precision", ("under_translation",), "medium", _location("human-note-D-source"), _location("phrase:就會壞了我的假期"), "不能因延遲而縮短或犧牲假期", "就會壞了我的假期", "Retain the specific loss or shortening of the holiday.", "避免弱化假期被縮短或犧牲的語意", "The main idea remains but its concrete consequence is weakened.", 1.0, "human_review_stage10101", True, False, {"suggestion_only": True, "approved_translation": None}),
        TranslationDefect("TQ-DEF-E", "narrative_naturalness", ("chinese_fluency",), "medium", _location("human-note-E-source"), _location("phrase:被拋在遠國的怪物般的男人"), None, "被拋在遠國的怪物般的男人", "Use natural narrative Chinese without the stiff 遠國 construction.", "重整語序並避免生硬的「遠國」", "The wording is stiff and carries translated syntax.", 1.0, "human_review_stage10101", True, False, {"suggestion_only": True, "approved_translation": None}),
        TranslationDefect("TQ-DEF-F", "traditional_chinese_style", ("style_consistency",), "low", _location("human-note-F-source"), _location("phrase:一周"), None, "一周", "Use consistent Traditional Chinese typography.", "一週", "The reviewed style convention prefers 週 in this context.", 1.0, "human_review_stage10101", True, False, {"suggestion_only": True, "approved_translation": None}),
    )
    return validate_defects(rows)

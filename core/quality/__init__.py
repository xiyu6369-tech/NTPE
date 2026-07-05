try:
    from .semantic_engine import SemanticTranslationEngine
except Exception:
    SemanticTranslationEngine = None

try:
    from .structure_engine import DocumentStructureEngine
except Exception:
    DocumentStructureEngine = None

try:
    from .coverage_analyzer import CoverageAnalyzer
    from .coverage_checker import CoverageChecker
except Exception:
    CoverageAnalyzer = None
    CoverageChecker = None

try:
    from .coverage_expansion_analyzer import CoverageExpansionAnalyzer
except Exception:
    CoverageExpansionAnalyzer = None

try:
    from .semantic_qa import SemanticQA
    from .semantic_repair import SemanticRepair
except Exception:
    SemanticQA = None
    SemanticRepair = None

try:
    from .novel_style_planner import NovelStylePlanner
except Exception:
    NovelStylePlanner = None

from .novel_prompt_engine import NovelPromptEngine

__all__ = [
    "SemanticTranslationEngine",
    "DocumentStructureEngine",
    "CoverageAnalyzer",
    "CoverageChecker",
    "CoverageExpansionAnalyzer",
    "SemanticQA",
    "SemanticRepair",
    "NovelStylePlanner",
    "NovelPromptEngine",
]

# NTPE 1.2 Professional Stage-15.1 Translation Quality Engine Core
try:
    from .quality_context import QualityContext
    from .quality_engine import TranslationQualityEngine
    from .quality_events import QualityEvent, QualityEventBus
    from .quality_pipeline import QualityPipeline
    from .quality_registry import QualityRuleRegistry, build_default_quality_registry
    from .quality_report import QualityReport
    from .quality_result import QualityIssue, QualityResult, QualitySeverity, QualityStatus
    from .quality_rules import (
        BaseQualityRule,
        LengthRatioRule,
        NonEmptyTranslationRule,
        PlaceholderIntegrityRule,
        build_default_quality_rules,
    )
except Exception:
    QualityContext = None
    TranslationQualityEngine = None
    QualityEvent = None
    QualityEventBus = None
    QualityPipeline = None
    QualityRuleRegistry = None
    QualityReport = None
    QualityIssue = None
    QualityResult = None
    QualitySeverity = None
    QualityStatus = None
    BaseQualityRule = None
    LengthRatioRule = None
    NonEmptyTranslationRule = None
    PlaceholderIntegrityRule = None
    build_default_quality_registry = None
    build_default_quality_rules = None

__all__ = list(dict.fromkeys(__all__ + [
    "QualityContext",
    "TranslationQualityEngine",
    "QualityEvent",
    "QualityEventBus",
    "QualityPipeline",
    "QualityRuleRegistry",
    "build_default_quality_registry",
    "QualityReport",
    "QualityIssue",
    "QualityResult",
    "QualitySeverity",
    "QualityStatus",
    "BaseQualityRule",
    "LengthRatioRule",
    "NonEmptyTranslationRule",
    "PlaceholderIntegrityRule",
    "build_default_quality_rules",
]))

# NTPE 1.2 Professional Stage-15.2 Translation Completeness / Missing Segment Detection
try:
    from .completeness_analyzer import (
        CompletenessAnalysis,
        CompletenessSegment,
        TranslationCompletenessAnalyzer,
    )
    from .completeness_report import CompletenessReport
    from .completeness_rules import (
        MissingSegmentRule,
        ShortSegmentRule,
        TotalCompletenessRatioRule,
        build_completeness_rules,
    )
except Exception:
    CompletenessAnalysis = None
    CompletenessSegment = None
    TranslationCompletenessAnalyzer = None
    CompletenessReport = None
    MissingSegmentRule = None
    ShortSegmentRule = None
    TotalCompletenessRatioRule = None
    build_completeness_rules = None

# Stage-15.3 Terminology / Character Consistency Engine exports
try:
    from .terminology_consistency import (
        TerminologyAnalysis,
        TerminologyConsistencyAnalyzer,
        TerminologyEntry,
        TerminologyIssue,
        build_default_character_glossary,
    )
    from .terminology_report import TerminologyReport
    from .terminology_rules import TerminologyConsistencyRule, build_terminology_rules
except Exception:
    # Optional in older Stage-15 builds.
    pass


# NTPE 1.2 Professional Stage-15.4 Repetition / Duplicate Content Detection exports
try:
    from .repetition_detection import RepetitionAnalysis, RepetitionDetector, RepetitionSpan
    from .repetition_report import RepetitionReport
    from .repetition_rules import RepetitionDuplicateContentRule, build_repetition_rules
except Exception:
    RepetitionAnalysis = None
    RepetitionDetector = None
    RepetitionSpan = None
    RepetitionReport = None
    RepetitionDuplicateContentRule = None
    build_repetition_rules = None

__all__ = list(dict.fromkeys(__all__ + [
    "RepetitionAnalysis",
    "RepetitionDetector",
    "RepetitionSpan",
    "RepetitionReport",
    "RepetitionDuplicateContentRule",
    "build_repetition_rules",
]))

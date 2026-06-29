try:
    from .semantic_engine import SemanticTranslationEngine
except Exception:
    SemanticTranslationEngine = None

try:
    from .structure_engine import DocumentStructureEngine
except Exception:
    DocumentStructureEngine = None

from .coverage_analyzer import CoverageAnalyzer
from .coverage_checker import CoverageChecker

__all__ = [
    "SemanticTranslationEngine",
    "DocumentStructureEngine",
    "CoverageAnalyzer",
    "CoverageChecker",
]

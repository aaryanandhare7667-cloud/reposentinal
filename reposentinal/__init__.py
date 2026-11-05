"""
RepoSentinel: Autonomous Bug Discovery Agent for GitHub Repositories.
"""
__version__ = "0.3.0"

from reposentinal.models import (
    Severity,
    BugFinding,
    FileContext,
    ScanSummary,
)
from reposentinal.indexer import (
    SymbolKind,
    Symbol,
    ImportStatement,
    DependencyGraph,
    RepositoryIndex,
    build_repository_index,
)
from reposentinal.hypothesis import (
    Confidence,
    BugStatus,
    BugHypothesis,
    HypothesisEvaluationMetrics,
)
from reposentinal.context import (
    RepositoryContext,
    RepositoryContextBuilder,
)
from reposentinal.hypothesis_engine import (
    BaseHypothesisEngine,
    RuleBasedHypothesisEngine,
    LLMHypothesisEngine,
)

__all__ = [
    "Severity",
    "BugFinding",
    "FileContext",
    "ScanSummary",
    "SymbolKind",
    "Symbol",
    "ImportStatement",
    "DependencyGraph",
    "RepositoryIndex",
    "build_repository_index",
    "Confidence",
    "BugStatus",
    "BugHypothesis",
    "HypothesisEvaluationMetrics",
    "RepositoryContext",
    "RepositoryContextBuilder",
    "BaseHypothesisEngine",
    "RuleBasedHypothesisEngine",
    "LLMHypothesisEngine",
]

"""
RepoSentinel: Autonomous Bug Discovery Agent for GitHub Repositories.
"""
__version__ = "0.2.0"

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
]

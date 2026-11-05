"""
Backward compatibility bridge to backend.analysis.indexer.
"""
from backend.analysis.indexer import *
from backend.analysis.indexer import (
    SymbolKind,
    Symbol,
    ImportStatement,
    DependencyGraph,
    RepositoryIndex,
    build_repository_index,
    PythonASTVisitor,
    _resolve_module_to_file,
)

__all__ = [
    "SymbolKind",
    "Symbol",
    "ImportStatement",
    "DependencyGraph",
    "RepositoryIndex",
    "build_repository_index",
    "PythonASTVisitor",
    "_resolve_module_to_file",
]

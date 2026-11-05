"""
RepoSentinel: Autonomous Bug Discovery Agent for GitHub Repositories.
"""
__version__ = "0.4.0"

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
from reposentinal.test_generator import (
    AdversarialTest,
    TestSafetyValidator,
    DeterministicTestGenerator,
)
from reposentinal.sandbox import (
    BaseSandbox,
    DockerSandbox,
    SafeSubprocessSandbox,
    get_sandbox_backend,
)
from reposentinal.verification import (
    VerificationStatus,
    ExecutionResult,
    VerificationEvidence,
)
from reposentinal.verifier import (
    HypothesisVerifier,
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
    "AdversarialTest",
    "TestSafetyValidator",
    "DeterministicTestGenerator",
    "BaseSandbox",
    "DockerSandbox",
    "SafeSubprocessSandbox",
    "get_sandbox_backend",
    "VerificationStatus",
    "ExecutionResult",
    "VerificationEvidence",
    "HypothesisVerifier",
]

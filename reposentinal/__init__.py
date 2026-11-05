"""
RepoSentinel: Autonomous Bug Discovery Agent for GitHub Repositories.
"""
__version__ = "0.5.0"

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
from reposentinal.patch_models import (
    PatchVerificationStatus,
    GeneratedPatch,
    PatchVerificationResult,
    PatchQualityMetrics,
)
from reposentinal.patch_safety import (
    PatchSafetyValidator,
)
from reposentinal.patch_workspace import (
    IsolatedPatchWorkspace,
)
from reposentinal.patch_applier import (
    PatchApplier,
)
from reposentinal.patch_generator import (
    DeterministicPatchGenerator,
)
from reposentinal.patch_verifier import (
    PatchVerifier,
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
    "PatchVerificationStatus",
    "GeneratedPatch",
    "PatchVerificationResult",
    "PatchQualityMetrics",
    "PatchSafetyValidator",
    "IsolatedPatchWorkspace",
    "PatchApplier",
    "DeterministicPatchGenerator",
    "PatchVerifier",
]

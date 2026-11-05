"""
RepoSentinel: Autonomous Bug Discovery Agent for GitHub Repositories.
"""
__version__ = "0.5.0"

from backend.models.models import (
    Severity,
    BugFinding,
    FileContext,
    ScanSummary,
)
from backend.scanner.scanner import (
    scan_repository,
    prepare_target,
)
from backend.analysis.analyzer import (
    RepoSentinelAgent,
)
from backend.analysis.indexer import (
    SymbolKind,
    Symbol,
    ImportStatement,
    DependencyGraph,
    RepositoryIndex,
    build_repository_index,
)
from backend.models.hypothesis import (
    Confidence,
    BugStatus,
    BugHypothesis,
    HypothesisEvaluationMetrics,
)
from backend.analysis.context import (
    RepositoryContext,
    RepositoryContextBuilder,
)
from backend.analysis.hypothesis_engine import (
    BaseHypothesisEngine,
    RuleBasedHypothesisEngine,
    LLMHypothesisEngine,
)
from backend.verification.test_generator import (
    AdversarialTest,
    TestSafetyValidator,
    DeterministicTestGenerator,
)
from backend.verification.sandbox import (
    BaseSandbox,
    DockerSandbox,
    SafeSubprocessSandbox,
    get_sandbox_backend,
)
from backend.verification.verification import (
    VerificationStatus,
    ExecutionResult,
    VerificationEvidence,
)
from backend.verification.verifier import (
    HypothesisVerifier,
)
from backend.models.patch_models import (
    PatchVerificationStatus,
    GeneratedPatch,
    PatchVerificationResult,
    PatchQualityMetrics,
)
from backend.patching.patch_safety import (
    PatchSafetyValidator,
)
from backend.patching.patch_workspace import (
    IsolatedPatchWorkspace,
)
from backend.patching.patch_applier import (
    PatchApplier,
)
from backend.patching.patch_generator import (
    DeterministicPatchGenerator,
)
from backend.patching.patch_verifier import (
    PatchVerifier,
)

__all__ = [
    "Severity",
    "BugFinding",
    "FileContext",
    "ScanSummary",
    "scan_repository",
    "prepare_target",
    "RepoSentinelAgent",
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

"""
RepoSentinel Verification: Adversarial test generation, sandboxed test execution, and empirical hypothesis verification.
"""
from backend.verification.verification import (
    VerificationStatus,
    ExecutionResult,
    VerificationEvidence,
)
from backend.verification.verifier import (
    HypothesisVerifier,
)
from backend.verification.sandbox import (
    BaseSandbox,
    DockerSandbox,
    SafeSubprocessSandbox,
    get_sandbox_backend,
)
from backend.verification.test_generator import (
    AdversarialTest,
    TestSafetyValidator,
    DeterministicTestGenerator,
)

__all__ = [
    "VerificationStatus",
    "ExecutionResult",
    "VerificationEvidence",
    "HypothesisVerifier",
    "BaseSandbox",
    "DockerSandbox",
    "SafeSubprocessSandbox",
    "get_sandbox_backend",
    "AdversarialTest",
    "TestSafetyValidator",
    "DeterministicTestGenerator",
]

"""
Backward compatibility bridge to backend.verification.verification.
"""
from backend.verification.verification import (
    VerificationStatus,
    ExecutionResult,
    VerificationEvidence,
)

__all__ = [
    "VerificationStatus",
    "ExecutionResult",
    "VerificationEvidence",
]

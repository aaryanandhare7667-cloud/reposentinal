"""
Backward compatibility bridge to backend.models.patch_models.
"""
from backend.models.patch_models import (
    PatchVerificationStatus,
    GeneratedPatch,
    PatchVerificationResult,
    PatchQualityMetrics,
)

__all__ = [
    "PatchVerificationStatus",
    "GeneratedPatch",
    "PatchVerificationResult",
    "PatchQualityMetrics",
]

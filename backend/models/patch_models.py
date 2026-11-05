import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


class PatchVerificationStatus(str, Enum):
    """
    Explicit lifecycle states for patch generation and verification.
    Only deterministic runtime verification evidence can promote a patch to VERIFIED.
    """
    GENERATED = "GENERATED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    APPLY_FAILED = "APPLY_FAILED"
    APPLIED = "APPLIED"
    VULNERABILITY_FIXED = "VULNERABILITY_FIXED"
    REGRESSION_DETECTED = "REGRESSION_DETECTED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    VERIFIED = "VERIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class GeneratedPatch:
    """
    Structured model representing an automated candidate patch.
    Contains unified diff, target symbol, original code context, and generation rationale.
    """
    patch_id: str
    hypothesis_id: str
    target_file: str
    target_symbol: Optional[str]
    bug_category: str
    patch_objective: str
    original_code: str
    patched_code: str
    unified_diff: str
    rationale: str
    validation_status: str = "PENDING"  # "PASSED", "FAILED"
    validation_error: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "hypothesis_id": self.hypothesis_id,
            "target_file": self.target_file,
            "target_symbol": self.target_symbol,
            "bug_category": self.bug_category,
            "patch_objective": self.patch_objective,
            "original_code": self.original_code,
            "patched_code": self.patched_code,
            "unified_diff": self.unified_diff,
            "rationale": self.rationale,
            "validation_status": self.validation_status,
            "validation_error": self.validation_error,
            "created_at": round(self.created_at, 2),
        }


@dataclass
class PatchVerificationResult:
    """
    Comprehensive verification result after applying candidate patch in an isolated workspace
    and executing both original adversarial reproduction tests and regression tests.
    """
    patch_id: str
    hypothesis_id: str
    status: PatchVerificationStatus
    vulnerability_fixed: bool = False
    regression_passed: bool = False
    repro_test_stdout: str = ""
    repro_test_stderr: str = ""
    regression_test_stdout: str = ""
    regression_test_stderr: str = ""
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    final_diff: str = ""
    verification_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "hypothesis_id": self.hypothesis_id,
            "status": self.status.value,
            "vulnerability_fixed": self.vulnerability_fixed,
            "regression_passed": self.regression_passed,
            "duration_seconds": round(self.duration_seconds, 2),
            "error_message": self.error_message,
            "final_diff": self.final_diff,
            "verification_notes": self.verification_notes,
        }


@dataclass
class PatchQualityMetrics:
    """
    Empirical research metrics for patch generation and verification benchmarking.
    """
    patches_generated: int = 0
    patches_validated: int = 0
    patches_applied: int = 0
    patches_verified: int = 0
    patch_application_failures: int = 0
    verification_failures: int = 0
    regression_detected_count: int = 0
    vulnerability_fix_rate: float = 0.0
    patch_verification_rate: float = 0.0
    average_patch_time: float = 0.0
    average_verification_time: float = 0.0
    total_lines_added: int = 0
    total_lines_removed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patches_generated": self.patches_generated,
            "patches_validated": self.patches_validated,
            "patches_applied": self.patches_applied,
            "patches_verified": self.patches_verified,
            "patch_application_failures": self.patch_application_failures,
            "verification_failures": self.verification_failures,
            "regression_detected_count": self.regression_detected_count,
            "vulnerability_fix_rate": self.vulnerability_fix_rate,
            "patch_verification_rate": self.patch_verification_rate,
            "average_patch_time": self.average_patch_time,
            "average_verification_time": self.average_verification_time,
            "total_lines_added": self.total_lines_added,
            "total_lines_removed": self.total_lines_removed,
        }

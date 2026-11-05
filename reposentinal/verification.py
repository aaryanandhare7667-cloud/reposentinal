from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Optional, Any


class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    REPRODUCED = "REPRODUCED"
    NOT_REPRODUCED = "NOT_REPRODUCED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


@dataclass
class ExecutionResult:
    test_id: str
    hypothesis_id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    sandbox_backend: str
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationEvidence:
    hypothesis_id: str
    test_id: str
    status: VerificationStatus
    execution: ExecutionResult
    reproduction_trace: Optional[str] = None
    failure_reason: Optional[str] = None
    verification_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

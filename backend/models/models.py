from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class BugFinding:
    file_path: str
    line_start: int
    line_end: int
    title: str
    category: str  # e.g., "Security", "Logic Error", "Resource Leak", "Concurrency"
    severity: Severity
    description: str
    remediation: str
    code_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class FileContext:
    abs_path: str
    rel_path: str
    language: str
    line_count: int
    size_bytes: int
    content: str


@dataclass
class ScanSummary:
    target: str
    scanned_files: int
    total_lines: int
    findings: List[BugFinding] = field(default_factory=list)
    duration_seconds: float = 0.0
    provider_used: str = "mock"
    topology_summary: Optional[Dict[str, Any]] = None
    hypotheses: List[Any] = field(default_factory=list)
    metrics: Optional[Dict[str, Any]] = None
    verification_evidence: List[Any] = field(default_factory=list)
    verification_metrics: Optional[Dict[str, Any]] = None
    patches: List[Any] = field(default_factory=list)
    patch_results: List[Any] = field(default_factory=list)
    patch_metrics: Optional[Dict[str, Any]] = None

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.LOW)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.INFO)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "target": self.target,
            "scanned_files": self.scanned_files,
            "total_lines": self.total_lines,
            "duration_seconds": round(self.duration_seconds, 2),
            "provider_used": self.provider_used,
            "counts": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
                "total": len(self.findings),
            },
            "findings": [f.to_dict() for f in self.findings],
        }
        if self.topology_summary is not None:
            result["topology"] = self.topology_summary
        if self.hypotheses:
            result["hypotheses"] = [h.to_dict() if hasattr(h, "to_dict") else h for h in self.hypotheses]
        if self.metrics is not None:
            result["metrics"] = self.metrics
        if self.verification_evidence:
            result["verification_evidence"] = [e.to_dict() if hasattr(e, "to_dict") else e for e in self.verification_evidence]
        if self.verification_metrics is not None:
            result["verification_metrics"] = self.verification_metrics
        if self.patches:
            result["patches"] = [p.to_dict() if hasattr(p, "to_dict") else p for p in self.patches]
        if self.patch_results:
            result["patch_results"] = [r.to_dict() if hasattr(r, "to_dict") else r for r in self.patch_results]
        if self.patch_metrics is not None:
            result["patch_metrics"] = self.patch_metrics
        return result

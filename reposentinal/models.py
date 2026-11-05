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
        return {
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

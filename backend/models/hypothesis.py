import hashlib
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from backend.models.models import Severity


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BugStatus(str, Enum):
    POTENTIAL = "Potential Bug"
    LIKELY = "Likely Bug"
    CONFIRMED = "Confirmed Bug"


@dataclass
class BugHypothesis:
    """
    Represents a structured, repository-aware bug hypothesis.
    Maintains a strict distinction between Potential, Likely, and Confirmed bugs.
    """
    hypothesis_id: str
    title: str
    category: str
    severity: Severity
    confidence: Confidence
    status: BugStatus
    affected_file: str
    line_start: int
    line_end: int
    explanation: str
    reasoning: str
    suggested_test: str
    affected_symbol: Optional[str] = None
    related_symbols: List[str] = field(default_factory=list)
    code_snippet: str = ""
    remediation: str = ""
    is_verified: bool = False

    def validate(self) -> None:
        """
        Validate hypothesis fields and invariants.
        Raises ValueError if fields are invalid or invariants are violated.
        """
        if not self.hypothesis_id or not isinstance(self.hypothesis_id, str):
            raise ValueError("hypothesis_id must be a non-empty string")
        if not self.title or not isinstance(self.title, str):
            raise ValueError("title must be a non-empty string")
        if not self.affected_file or not isinstance(self.affected_file, str):
            raise ValueError("affected_file must be a non-empty string")
        if not isinstance(self.severity, Severity):
            raise ValueError(f"Invalid severity: {self.severity}")
        if not isinstance(self.confidence, Confidence):
            raise ValueError(f"Invalid confidence: {self.confidence}")
        if not isinstance(self.status, BugStatus):
            raise ValueError(f"Invalid bug status: {self.status}")
        if self.line_start <= 0 or self.line_end <= 0 or self.line_start > self.line_end:
            raise ValueError(f"Invalid line range: {self.line_start}-{self.line_end}")

        # Invariant: Hypotheses cannot be marked 'Confirmed Bug' without independent execution proof
        # LLM or static generation can only produce POTENTIAL or LIKELY
        if self.status == BugStatus.CONFIRMED and not self.is_verified:
            raise ValueError("Hypotheses cannot be self-marked as 'Confirmed Bug' without deterministic reproduction")

    def confirm(self) -> None:
        """Promote hypothesis to Confirmed Bug based on verified execution evidence."""
        self.is_verified = True
        self.status = BugStatus.CONFIRMED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "status": self.status.value,
            "affected_file": self.affected_file,
            "affected_symbol": self.affected_symbol,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "explanation": self.explanation,
            "reasoning": self.reasoning,
            "related_symbols": self.related_symbols,
            "suggested_test": self.suggested_test,
            "code_snippet": self.code_snippet,
            "remediation": self.remediation,
            "is_verified": self.is_verified,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BugHypothesis":
        # Safe severity parsing
        sev_str = str(data.get("severity", "MEDIUM")).upper()
        severity = Severity.__members__.get(sev_str, Severity.MEDIUM)

        # Safe confidence parsing
        conf_str = str(data.get("confidence", "MEDIUM")).upper()
        confidence = Confidence.__members__.get(conf_str, Confidence.MEDIUM)

        # Safe status parsing - enforce that status cannot be Confirmed Bug without verification
        is_verified = bool(data.get("is_verified", False))
        status_val = data.get("status", BugStatus.POTENTIAL.value)
        if status_val == BugStatus.CONFIRMED.value and not is_verified:
            # Automatically downgrade unverified claims of 'Confirmed' to 'Likely Bug'
            status = BugStatus.LIKELY
        elif status_val == BugStatus.CONFIRMED.value and is_verified:
            status = BugStatus.CONFIRMED
        elif status_val == BugStatus.LIKELY.value or status_val == "LIKELY":
            status = BugStatus.LIKELY
        else:
            status = BugStatus.POTENTIAL

        line_start = int(data.get("line_start", 1))
        line_end = int(data.get("line_end", max(1, line_start)))
        if line_end < line_start:
            line_end = line_start

        hyp_id = data.get("hypothesis_id")
        if not hyp_id:
            # Deterministic hash ID based on file, lines, and title
            raw_key = f"{data.get('affected_file')}:{line_start}:{data.get('title')}"
            hyp_id = f"HYP-{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:8].upper()}"

        return cls(
            hypothesis_id=hyp_id,
            title=str(data.get("title", "Unnamed Hypothesis")),
            category=str(data.get("category", "Logic Error")),
            severity=severity,
            confidence=confidence,
            status=status,
            affected_file=str(data.get("affected_file", "unknown")),
            affected_symbol=data.get("affected_symbol"),
            line_start=line_start,
            line_end=line_end,
            explanation=str(data.get("explanation", "")),
            reasoning=str(data.get("reasoning", "")),
            related_symbols=list(data.get("related_symbols", [])),
            suggested_test=str(data.get("suggested_test", "")),
            code_snippet=str(data.get("code_snippet", "")),
            remediation=str(data.get("remediation", "")),
        )


@dataclass
class HypothesisEvaluationMetrics:
    """
    Research-oriented evaluation metrics for bug hypothesis generation.
    Enables future benchmarking (code-only vs repo-aware vs adversarial testing).
    """
    total_hypotheses: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    by_confidence: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    cross_file_count: int = 0
    symbol_mapped_count: int = 0

    @classmethod
    def calculate(cls, hypotheses: List[BugHypothesis]) -> "HypothesisEvaluationMetrics":
        m = cls(total_hypotheses=len(hypotheses))
        for h in hypotheses:
            sev = h.severity.value
            m.by_severity[sev] = m.by_severity.get(sev, 0) + 1

            conf = h.confidence.value
            m.by_confidence[conf] = m.by_confidence.get(conf, 0) + 1

            stat = h.status.value
            m.by_status[stat] = m.by_status.get(stat, 0) + 1

            cat = h.category
            m.by_category[cat] = m.by_category.get(cat, 0) + 1

            if h.related_symbols or "cross" in h.reasoning.lower() or "imported" in h.reasoning.lower():
                m.cross_file_count += 1

            if h.affected_symbol:
                m.symbol_mapped_count += 1

        return m

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_hypotheses": self.total_hypotheses,
            "by_severity": self.by_severity,
            "by_confidence": self.by_confidence,
            "by_status": self.by_status,
            "by_category": self.by_category,
            "cross_file_count": self.cross_file_count,
            "symbol_mapped_count": self.symbol_mapped_count,
            "cross_file_ratio": round(self.cross_file_count / max(1, self.total_hypotheses), 2),
        }

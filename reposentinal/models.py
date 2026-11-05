"""
Backward compatibility bridge to backend.models.models.
"""
from backend.models.models import (
    Severity,
    BugFinding,
    FileContext,
    ScanSummary,
)

__all__ = [
    "Severity",
    "BugFinding",
    "FileContext",
    "ScanSummary",
]

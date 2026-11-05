"""
Backward compatibility bridge to backend.cli.reporter.
"""
from backend.cli.reporter import (
    TerminalReporter,
    MarkdownReporter,
    JSONReporter,
    RESET,
    BOLD,
    DIM,
    RED,
    GREEN,
    YELLOW,
    BLUE,
    MAGENTA,
    CYAN,
    WHITE,
    BG_RED,
    BG_YELLOW,
    get_severity_badge,
)

__all__ = [
    "TerminalReporter",
    "MarkdownReporter",
    "JSONReporter",
    "RESET",
    "BOLD",
    "DIM",
    "RED",
    "GREEN",
    "YELLOW",
    "BLUE",
    "MAGENTA",
    "CYAN",
    "WHITE",
    "BG_RED",
    "BG_YELLOW",
    "get_severity_badge",
]

"""
Backward compatibility bridge to backend.analysis.hypothesis_engine.
"""
from backend.analysis.hypothesis_engine import (
    BaseHypothesisEngine,
    RuleBasedHypothesisEngine,
    LLMHypothesisEngine,
    HYPOTHESIS_SYSTEM_PROMPT,
)

__all__ = [
    "BaseHypothesisEngine",
    "RuleBasedHypothesisEngine",
    "LLMHypothesisEngine",
    "HYPOTHESIS_SYSTEM_PROMPT",
]

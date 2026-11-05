"""
Backward compatibility bridge to backend.verification.test_generator.
"""
from backend.verification.test_generator import (
    AdversarialTest,
    TestSafetyValidator,
    DeterministicTestGenerator,
)

__all__ = [
    "AdversarialTest",
    "TestSafetyValidator",
    "DeterministicTestGenerator",
]

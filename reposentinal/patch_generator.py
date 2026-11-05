"""
Backward compatibility bridge to backend.patching.patch_generator.
"""
from backend.patching.patch_generator import (
    BasePatchGenerator,
    DeterministicPatchGenerator,
)

__all__ = [
    "BasePatchGenerator",
    "DeterministicPatchGenerator",
]

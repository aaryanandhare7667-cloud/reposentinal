"""
RepoSentinel Patching: Patch generation, safety validation, isolated workspaces, diff generation, and dual-phase patch verification.
"""
from backend.patching.patch_verifier import PatchVerifier
from backend.patching.patch_generator import (
    BasePatchGenerator,
    DeterministicPatchGenerator,
)
from backend.patching.patch_safety import PatchSafetyValidator
from backend.patching.patch_workspace import IsolatedPatchWorkspace
from backend.patching.patch_applier import PatchApplier

__all__ = [
    "PatchVerifier",
    "BasePatchGenerator",
    "DeterministicPatchGenerator",
    "PatchSafetyValidator",
    "IsolatedPatchWorkspace",
    "PatchApplier",
]

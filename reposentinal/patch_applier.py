import ast
from pathlib import Path
from typing import Tuple

from reposentinal.patch_models import GeneratedPatch
from reposentinal.patch_safety import PatchSafetyValidator
from reposentinal.patch_workspace import IsolatedPatchWorkspace


class PatchApplier:
    """
    Applies candidate patches exclusively inside an isolated temporary workspace.
    Verifies that the target file exists, the applied code parses without syntax errors,
    and the user's host repository remains completely untouched.
    """

    @classmethod
    def apply_patch(
        cls, patch: GeneratedPatch, workspace: IsolatedPatchWorkspace
    ) -> Tuple[bool, str]:
        """
        Applies a GeneratedPatch to the isolated workspace.
        Returns (success: bool, status_message: str).
        """
        # 1. Structural safety validation before modifying workspace
        try:
            PatchSafetyValidator.validate(patch, workspace.source_dir)
        except ValueError as exc:
            return False, f"VALIDATION_FAILED: {exc}"

        # 2. Write patched content into isolated workspace
        try:
            workspace.apply_file_content(patch.target_file, patch.patched_code)
        except Exception as exc:
            return False, f"APPLY_FAILED: Could not write patched file: {exc}"

        # 3. Verify applied file integrity in workspace
        try:
            written_content = workspace.read_file(patch.target_file)
            if patch.target_file.endswith(".py"):
                ast.parse(written_content)
        except Exception as exc:
            return False, f"APPLY_FAILED: Applied code failed syntax verification: {exc}"

        return True, "APPLIED"

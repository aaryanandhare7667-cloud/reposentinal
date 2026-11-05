import ast
import re
from pathlib import Path
from typing import List, Optional
from reposentinal.patch_models import GeneratedPatch


class PatchSafetyValidator:
    """
    Defensive validation layer that inspects candidate patches before workspace application.
    Enforces strict security checks against malicious patterns, secret leaks, unauthorized
    file modifications, and malformed code.
    Fails closed: any security or syntax violation raises a ValueError.
    """

    DANGEROUS_PATTERNS = [
        r"""shutil\.rmtree\s*\(\s*['\"][/\\]""",  # rmtree /
        r"""os\.remove\s*\(\s*['\"][/\\]""",
        r"""subprocess\.(?:run|call|Popen)\s*\(\s*['\"][^'\"]*(?:rm\s+-rf\s+[/~]|mkfs|dd\s+if=)""",
        r"""os\.system\s*\(\s*['\"][^'\"]*(?:rm\s+-rf\s+[/~]|mkfs|dd\s+if=)""",
    ]

    SECRET_PATTERNS = [
        r"""(?i)(?:api_key|token|secret|password|auth_token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]""",
        r"""ghp_[A-Za-z0-9]{36}""",
        r"""sk-[A-Za-z0-9]{20,}""",
    ]

    PROTECTED_PATHS = [
        ".github/workflows",
        ".circleci",
        "reposentinal/sandbox.py",
        "reposentinal/verifier.py",
        "reposentinal/patch_safety.py",
    ]

    @classmethod
    def validate(cls, patch: GeneratedPatch, root_dir: Path) -> None:
        """
        Validates safety, syntax, and scope of a GeneratedPatch.
        Raises ValueError if the patch is unsafe, malformed, or exceeds allowed scope.
        """
        if not patch.patch_id or not patch.patch_id.strip():
            raise ValueError("Patch ID cannot be empty")

        if not patch.target_file or not patch.target_file.strip():
            raise ValueError("Target file cannot be empty")

        # 1. Scope Check: Ensure patch does not modify protected system infrastructure
        target_norm = patch.target_file.replace("\\", "/").strip()
        for protected in cls.PROTECTED_PATHS:
            if protected in target_norm:
                raise ValueError(f"Patch attempts to modify protected system path: {protected}")

        # 2. Scope Check: Ensure target file exists within target directory
        full_target = (root_dir / patch.target_file).resolve()
        if not full_target.exists():
            # If target file was given as an absolute path or relative to parent
            if Path(patch.target_file).exists():
                full_target = Path(patch.target_file).resolve()
            else:
                raise ValueError(f"Target file does not exist in repository: {patch.target_file}")

        # 3. Content Check: Patched code must not be empty or completely wiped
        if not patch.patched_code or not patch.patched_code.strip():
            raise ValueError("Patched code cannot be empty (prevent accidental file deletion)")

        # 4. Content Check: Patched code size sanity (prevent gigantic or runaway LLM outputs)
        if len(patch.patched_code) > 500_000:
            raise ValueError("Patched code exceeds maximum safe size threshold (500KB)")

        # 5. Security Check: Search for dangerous destructive commands
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, patch.patched_code):
                raise ValueError(f"Dangerous destructive pattern detected in patched code: {pattern}")

        # 6. Security Check: Search for hardcoded credentials or tokens
        for pattern in cls.SECRET_PATTERNS:
            if re.search(pattern, patch.patched_code):
                raise ValueError("Potential credential or secret detected in patch content")

        # 7. Syntax Check: Patched Python code must parse without SyntaxError
        if patch.target_file.endswith(".py"):
            try:
                ast.parse(patch.patched_code)
            except SyntaxError as exc:
                raise ValueError(f"Invalid Python syntax in patched code: {exc}")

        # 8. Diff Check: Unified diff format validation
        if not patch.unified_diff or not patch.unified_diff.strip():
            raise ValueError("Unified diff cannot be empty")

        # Ensure diff contains standard diff markers
        if "---" not in patch.unified_diff and "+++" not in patch.unified_diff:
            raise ValueError("Unified diff missing standard header markers ('---' and '+++')")

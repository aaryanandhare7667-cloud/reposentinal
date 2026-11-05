import difflib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List


class IsolatedPatchWorkspace:
    """
    Manages an isolated ephemeral workspace for applying candidate patches and verifying fixes.
    Ensures that the user's host repository is NEVER modified or contaminated during verification.
    Automatically scrubs sensitive dotfiles and cleans up ephemeral directories upon exit.
    """

    EXCLUDED_PATTERNS = {
        ".git",
        ".github",
        ".env",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
    }

    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir).resolve()
        self.temp_dir: Optional[str] = None
        self.workspace_dir: Optional[Path] = None

    def __enter__(self) -> "IsolatedPatchWorkspace":
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def create(self) -> Path:
        """
        Creates an isolated temporary copy of the repository for safe patch experimentation.
        """
        self.temp_dir = tempfile.mkdtemp(prefix="reposentinal_patch_ws_")
        self.workspace_dir = Path(self.temp_dir)
        self._copy_tree_safe(self.source_dir, self.workspace_dir)
        return self.workspace_dir

    def _copy_tree_safe(self, src: Path, dst: Path):
        """Copies source files to isolated destination excluding credentials and caches."""
        if src.is_file():
            shutil.copy2(src, dst / src.name)
            return

        for item in src.iterdir():
            if item.name in self.EXCLUDED_PATTERNS or item.name.startswith(".env"):
                continue

            target = dst / item.name
            if item.is_dir():
                shutil.copytree(
                    item,
                    target,
                    ignore=shutil.ignore_patterns("*.pyc", "__pycache__", ".git*"),
                )
            elif item.is_file():
                shutil.copy2(item, target)

    def resolve_path(self, rel_or_abs_path: str) -> Path:
        """
        Resolves a target file path relative to the isolated workspace.
        """
        if not self.workspace_dir:
            raise RuntimeError("Workspace has not been created yet")

        path_obj = Path(rel_or_abs_path)
        if path_obj.is_absolute():
            try:
                rel = path_obj.resolve().relative_to(self.source_dir)
                return self.workspace_dir / rel
            except ValueError:
                return self.workspace_dir / path_obj.name
        return self.workspace_dir / rel_or_abs_path

    def read_file(self, target_path_str: str) -> str:
        """Reads file content from isolated workspace."""
        full_path = self.resolve_path(target_path_str)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found in workspace: {target_path_str}")
        return full_path.read_text(encoding="utf-8")

    def apply_file_content(self, target_path_str: str, new_content: str) -> None:
        """
        Writes patched content to target file in isolated workspace.
        """
        full_path = self.resolve_path(target_path_str)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(new_content, encoding="utf-8")

    def compute_diff(self, target_path_str: str, original_content: str, new_content: str) -> str:
        """
        Generates standard unified diff between original and patched contents.
        """
        norm_name = Path(target_path_str).name
        orig_lines = original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff_lines = list(
            difflib.unified_diff(
                orig_lines,
                new_lines,
                fromfile=f"a/{norm_name}",
                tofile=f"b/{norm_name}",
            )
        )
        return "".join(diff_lines)

    def cleanup(self) -> None:
        """Completely removes ephemeral workspace from host filesystem."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
            self.workspace_dir = None

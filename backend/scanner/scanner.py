import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
from backend.models.models import FileContext

# Recognized extensions mapped to language identifier
EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".sh": "shell",
    ".bash": "shell",
    ".sql": "sql",
}

IGNORED_DIRS = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    "out",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "vendor",
    "eggs",
    ".eggs",
}

IGNORED_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Cargo.lock",
    "go.sum",
    "Pipfile.lock",
}

MAX_FILE_SIZE_BYTES = 150 * 1024  # 150 KB


def is_binary_string(bytes_data: bytes) -> bool:
    """Check if byte sequence contains null byte (common in binaries)."""
    return b"\x00" in bytes_data[:1024]


def prepare_target(target: str) -> Tuple[Path, Optional[str]]:
    """
    Prepare the scan target directory.
    If target is a git URL, clones shallowly to a temporary directory.
    Returns (Path to root dir, optional temp directory path to clean up).
    """
    if target.startswith("http://") or target.startswith("https://") or target.startswith("git@"):
        temp_dir = tempfile.mkdtemp(prefix="reposentinal_")
        cmd = ["git", "clone", "--depth", "1", target, temp_dir]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository '{target}': {result.stderr.strip()}")
        return Path(temp_dir), temp_dir

    p = Path(target).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Target path does not exist: {target}")
    return p, None


def scan_repository(
    target_path: Path,
    max_files: int = 50,
    languages: Optional[List[str]] = None,
) -> List[FileContext]:
    """
    Scan repository files and collect source file contexts.
    """
    selected_files: List[FileContext] = []
    normalized_langs = {l.lower() for l in languages} if languages else None

    # Handle scanning a single file directly
    if target_path.is_file():
        ext = target_path.suffix.lower()
        lang = EXTENSION_MAP.get(ext)
        if lang:
            try:
                content = target_path.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                return [
                    FileContext(
                        abs_path=str(target_path),
                        rel_path=target_path.name,
                        language=lang,
                        line_count=len(lines),
                        size_bytes=target_path.stat().st_size,
                        content=content,
                    )
                ]
            except Exception:
                return []
        return []

    for root, dirs, files in os.walk(target_path):
        # Prune ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        for file_name in files:
            if len(selected_files) >= max_files:
                break

            if file_name in IGNORED_FILES or file_name.startswith("."):
                continue

            file_path = Path(root) / file_name
            ext = file_path.suffix.lower()
            lang = EXTENSION_MAP.get(ext)

            if not lang:
                continue

            if normalized_langs and lang not in normalized_langs:
                continue

            try:
                st = file_path.stat()
                if st.st_size > MAX_FILE_SIZE_BYTES or st.st_size == 0:
                    continue

                raw_bytes = file_path.read_bytes()
                if is_binary_string(raw_bytes):
                    continue

                content = raw_bytes.decode("utf-8", errors="replace")
                lines = content.splitlines()

                rel_path = str(file_path.relative_to(target_path))

                selected_files.append(
                    FileContext(
                        abs_path=str(file_path),
                        rel_path=rel_path,
                        language=lang,
                        line_count=len(lines),
                        size_bytes=st.st_size,
                        content=content,
                    )
                )
            except Exception:
                continue

        if len(selected_files) >= max_files:
            break

    return selected_files

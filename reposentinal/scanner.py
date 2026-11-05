"""
Backward compatibility bridge to backend.scanner.scanner.
"""
from backend.scanner.scanner import (
    scan_repository,
    prepare_target,
    is_binary_string,
    EXTENSION_MAP,
    IGNORED_DIRS,
    MAX_FILE_SIZE_BYTES,
)

__all__ = [
    "scan_repository",
    "prepare_target",
    "is_binary_string",
    "EXTENSION_MAP",
    "IGNORED_DIRS",
    "MAX_FILE_SIZE_BYTES",
]

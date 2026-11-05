"""
Backward compatibility bridge to backend.verification.sandbox.
"""
from backend.verification.sandbox import (
    BaseSandbox,
    DockerSandbox,
    SafeSubprocessSandbox,
    get_sandbox_backend,
)

__all__ = [
    "BaseSandbox",
    "DockerSandbox",
    "SafeSubprocessSandbox",
    "get_sandbox_backend",
]

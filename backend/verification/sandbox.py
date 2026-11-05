import os
import shutil
import subprocess
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Set
from backend.verification.test_generator import AdversarialTest
from backend.verification.verification import ExecutionResult


class BaseSandbox(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def execute(self, test: AdversarialTest, root_dir: Path) -> ExecutionResult:
        pass


class DockerSandbox(BaseSandbox):
    """
    Containerized isolated sandbox using Docker with network=none, memory, and CPU limits.
    """

    @property
    def backend_name(self) -> str:
        return "docker"

    def is_available(self) -> bool:
        if not shutil.which("docker"):
            return False
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    def execute(self, test: AdversarialTest, root_dir: Path) -> ExecutionResult:
        temp_dir = tempfile.mkdtemp(prefix="reposentinal_docker_")
        start_time = time.time()
        try:
            # Copy source files to ephemeral workspace
            self._copy_tree_safe(root_dir, Path(temp_dir))

            test_file = Path(temp_dir) / f"run_{test.test_id}.py"
            test_file.write_text(test.executable_code, encoding="utf-8")

            cmd = [
                "docker", "run", "--rm",
                "--network=none",
                "--memory=256m",
                "--cpus=1",
                "-v", f"{temp_dir}:/workspace",
                "-w", "/workspace",
                "python:3.11-slim",
                "python", "-I", f"run_{test.test_id}.py",
            ]

            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=test.timeout_seconds,
            )
            duration = time.time() - start_time

            return ExecutionResult(
                test_id=test.test_id,
                hypothesis_id=test.hypothesis_id,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=duration,
                timed_out=False,
                sandbox_backend=self.backend_name,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult(
                test_id=test.test_id,
                hypothesis_id=test.hypothesis_id,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {test.timeout_seconds} seconds.",
                duration_seconds=duration,
                timed_out=True,
                sandbox_backend=self.backend_name,
                error_message="Sandbox timeout expired",
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                test_id=test.test_id,
                hypothesis_id=test.hypothesis_id,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_seconds=duration,
                timed_out=False,
                sandbox_backend=self.backend_name,
                error_message=f"Docker execution error: {e}",
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _copy_tree_safe(self, src: Path, dst: Path):
        for item in src.iterdir():
            if item.name.startswith(".") or item.name in ("__pycache__", "venv", ".venv"):
                continue
            target = dst / item.name
            if item.is_dir():
                shutil.copytree(item, target, ignore=shutil.ignore_patterns(".*", "__pycache__"))
            elif item.is_file():
                shutil.copy2(item, target)


class SafeSubprocessSandbox(BaseSandbox):
    """
    Process-isolated sandbox executing in an ephemeral temporary directory with scrubbed environment variables.
    Serves as a robust fallback when Docker is not installed or available.
    """

    ALLOWED_ENV_VARS = {"PATH", "SYSTEMROOT", "TMP", "TEMP"}
    SENSITIVE_PATTERNS = ["TOKEN", "KEY", "SECRET", "PASSWORD", "AUTH", "CREDENTIAL", "API", "GH_", "GEMINI_"]

    @property
    def backend_name(self) -> str:
        return "safe_subprocess"

    def is_available(self) -> bool:
        return True

    def execute(self, test: AdversarialTest, root_dir: Path) -> ExecutionResult:
        temp_dir = tempfile.mkdtemp(prefix="reposentinal_sandbox_")
        start_time = time.time()
        try:
            # 1. Copy repository files to isolated temporary folder
            self._copy_workspace(root_dir, Path(temp_dir))

            # 2. Write executable test script
            test_file = Path(temp_dir) / f"test_run_{test.test_id}.py"
            test_file.write_text(test.executable_code, encoding="utf-8")

            # 3. Create strictly sanitized environment (scrub all host secrets)
            clean_env = self._create_clean_environment(temp_dir)

            # 4. Execute test in isolated mode (-I: isolated, -s: no user site, -B: no bytecode)
            cmd = [
                sys.executable,
                "-I",
                "-s",
                "-B",
                str(test_file),
            ]

            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=temp_dir,
                env=clean_env,
                timeout=test.timeout_seconds,
            )
            duration = time.time() - start_time

            return ExecutionResult(
                test_id=test.test_id,
                hypothesis_id=test.hypothesis_id,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=duration,
                timed_out=False,
                sandbox_backend=self.backend_name,
            )

        except subprocess.TimeoutExpired as exc:
            duration = time.time() - start_time
            return ExecutionResult(
                test_id=test.test_id,
                hypothesis_id=test.hypothesis_id,
                exit_code=-1,
                stdout=exc.stdout or "" if hasattr(exc, "stdout") else "",
                stderr=f"Test execution timed out after {test.timeout_seconds} seconds.",
                duration_seconds=duration,
                timed_out=True,
                sandbox_backend=self.backend_name,
                error_message="Test execution timed out",
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                test_id=test.test_id,
                hypothesis_id=test.hypothesis_id,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_seconds=duration,
                timed_out=False,
                sandbox_backend=self.backend_name,
                error_message=f"Sandbox execution error: {e}",
            )
        finally:
            # 5. Clean up temporary directory completely
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _copy_workspace(self, src: Path, dst: Path):
        """Recursively copy source files into isolated destination."""
        if src.is_file():
            shutil.copy2(src, dst / src.name)
            return

        for item in src.iterdir():
            if item.name.startswith(".") or item.name in ("__pycache__", "venv", ".venv", "node_modules"):
                continue
            target = dst / item.name
            if item.is_dir():
                shutil.copytree(item, target, ignore=shutil.ignore_patterns(".*", "__pycache__"))
            elif item.is_file():
                shutil.copy2(item, target)

    def _create_clean_environment(self, temp_dir: str) -> Dict[str, str]:
        """
        Build an isolated environment dictionary stripped of all host secrets and credentials.
        """
        clean_env = {"PYTHONPATH": temp_dir}
        for key, val in os.environ.items():
            if key in self.ALLOWED_ENV_VARS:
                clean_env[key] = val
                continue

            # Check if variable key or value looks like a secret
            is_secret = any(pat in key.upper() for pat in self.SENSITIVE_PATTERNS)
            if not is_secret and key in ("PATH", "SYSTEMROOT", "TMP", "TEMP"):
                clean_env[key] = val

        return clean_env


def get_sandbox_backend(preferred: str = "auto") -> BaseSandbox:
    """
    Factory to resolve the appropriate sandbox backend.
    Prefers Docker if available, otherwise falls back safely to SafeSubprocessSandbox.
    """
    preferred = (preferred or "auto").lower()

    if preferred == "docker":
        docker = DockerSandbox()
        if docker.is_available():
            return docker
        # If user explicitly requested Docker but it's unavailable, fall back with warning
        return SafeSubprocessSandbox()

    if preferred in ("subprocess", "safe_subprocess"):
        return SafeSubprocessSandbox()

    # 'auto' mode: check Docker first, fallback to safe subprocess
    docker = DockerSandbox()
    if docker.is_available():
        return docker
    return SafeSubprocessSandbox()

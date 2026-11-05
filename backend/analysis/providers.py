import json
import re
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.models.models import BugFinding, FileContext, Severity


SYSTEM_PROMPT = """You are RepoSentinel, an expert autonomous software security & bug discovery agent.
Your task is to analyze source code and find real, high-impact bugs, security vulnerabilities, logic errors, and resource leaks.

DO NOT flag trivial style issues (e.g. whitespace, variable naming, missing docstrings).
FOCUS ON:
1. Security Vulnerabilities: Injection (SQL, Command, Template), XSS, Insecure Deserialization, Hardcoded Secrets, Path Traversal, Broken Access Control.
2. Logic Errors & Edge Cases: Off-by-one errors, infinite loops, incorrect Boolean conditions, unhandled null/None pointer dereferences, incorrect exception handling.
3. Resource Leaks & Concurrency: Unclosed file handles/sockets/database connections, race conditions, deadlock risks.

Respond STRICTLY with a valid JSON object in this format:
{
  "findings": [
    {
      "line_start": 12,
      "line_end": 14,
      "title": "Short descriptive title of the bug",
      "category": "Security" | "Logic Error" | "Resource Leak" | "Concurrency" | "Performance",
      "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
      "description": "Clear explanation of why this is a bug and how it can be triggered or cause failure.",
      "remediation": "Concrete code snippet or actionable step to fix the bug.",
      "code_snippet": "Relevant line(s) of code"
    }
  ]
}
If no bugs are found, return {"findings": []}.
"""


class BaseLLMProvider(ABC):
    @abstractmethod
    def analyze_file(self, file_ctx: FileContext) -> List[BugFinding]:
        """Analyze a file context and return identified bug findings."""
        pass


class MockProvider(BaseLLMProvider):
    """
    Offline heuristic analyzer. Works instantly with zero API keys or network connection.
    Finds real vulnerabilities and logic errors using static heuristics.
    """

    PATTERNS = [
        (
            r"""(?i)(?:api_key|secret|password|auth_token|access_token|private_key)\s*=\s*['\"][A-Za-z0-9_\-\.\/+=]{8,}['\"]""",
            "Hardcoded Sensitive Credential or Secret",
            "Security",
            Severity.CRITICAL,
            "Hardcoded secret detected. Committing credentials to source control exposes systems to credential stuffing and unauthorized access.",
            "Move sensitive credentials to environment variables or a secure secret manager (e.g., Vault, AWS Secrets Manager).",
        ),
        (
            r"""(?:os\.system|subprocess\.Popen|subprocess\.run|subprocess\.call)\s*\([^)]*shell\s*=\s*True""",
            "Potential Command Injection via shell=True",
            "Security",
            Severity.CRITICAL,
            "Executing shell commands with shell=True is susceptible to arbitrary command injection if input is untrusted.",
            "Pass arguments as a list without shell=True, or sanitize arguments using shlex.quote().",
        ),
        (
            r"""os\.system\s*\(""",
            "Unsafe Command Execution via os.system",
            "Security",
            Severity.HIGH,
            "os.system runs directly in the system shell and doesn't offer proper argument escaping.",
            "Use subprocess.run with argument vectors (list of strings) instead of os.system.",
        ),
        (
            r"""(?:eval|exec)\s*\(""",
            "Dangerous Dynamic Code Evaluation (eval/exec)",
            "Security",
            Severity.CRITICAL,
            "eval() or exec() executes arbitrary code strings. If any input is tainted, it leads directly to Remote Code Execution (RCE).",
            "Refactor code to use safe parsers like ast.literal_eval() or explicit dispatch dictionaries.",
        ),
        (
            r"""(?i)(?:(?:execute|cursor\.execute)\s*\(\s*f['\"]|f['\"][^\n\r]*(?:SELECT|INSERT|UPDATE|DELETE)[^\n\r]*\{[^}\n\r]+\})""",
            "SQL Injection via Formatted String Query",
            "Security",
            Severity.CRITICAL,
            "Direct interpolation of variables into SQL queries bypasses query parametrization and enables SQL Injection.",
            "Use parameterized queries: cursor.execute('SELECT ... WHERE col = %s', (value,))",
        ),
        (
            r"""except(?:\s*Exception)?\s*:\s*\n\s*(?:pass|\.\.\.)""",
            "Swallowed Exception (Silent Failure)",
            "Logic Error",
            Severity.MEDIUM,
            "Catching exceptions with an empty 'pass' block masks unexpected runtime errors, corrupted state, and debugging information.",
            "Log the exception with traceback (e.g. logger.exception) or handle specific exception classes.",
        ),
        (
            r"""requests\.(?:get|post|put|delete)\s*\([^)]*verify\s*=\s*False""",
            "Disabled SSL/TLS Certificate Verification",
            "Security",
            Severity.HIGH,
            "Disabling SSL verification allows man-in-the-middle (MITM) attackers to intercept or manipulate HTTPS traffic.",
            "Ensure verify=True (the default in requests) or provide a trusted CA bundle path.",
        ),
        (
            r"""(?:open\s*\([^)]+\))(?![\s\S]{0,100}\bwith\b)""",
            "Potential Unclosed File Resource",
            "Resource Leak",
            Severity.LOW,
            "Calling open() without a context manager ('with open(...)') or explicit close() can cause file descriptor exhaustion.",
            "Wrap file operations inside a 'with open(...) as f:' context block.",
        ),
    ]

    def analyze_file(self, file_ctx: FileContext) -> List[BugFinding]:
        findings: List[BugFinding] = []
        lines = file_ctx.content.splitlines()

        for pattern, title, category, severity, desc, remediation in self.PATTERNS:
            for match in re.finditer(pattern, file_ctx.content):
                # Calculate line number
                start_idx = match.start()
                line_no = file_ctx.content[:start_idx].count("\n") + 1
                matched_line = lines[line_no - 1].strip() if line_no <= len(lines) else match.group(0)

                findings.append(
                    BugFinding(
                        file_path=file_ctx.rel_path,
                        line_start=line_no,
                        line_end=line_no,
                        title=title,
                        category=category,
                        severity=severity,
                        description=desc,
                        remediation=remediation,
                        code_snippet=matched_line,
                    )
                )

        return findings


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini REST API Provider.
    """

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def analyze_file(self, file_ctx: FileContext) -> List[BugFinding]:
        user_prompt = f"File: {file_ctx.rel_path} ({file_ctx.language})\n\n```\n{file_ctx.content}\n```"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"}],
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                return self._parse_findings(raw_text, file_ctx)
        except Exception as e:
            # Fallback to Mock heuristic if API call fails
            return MockProvider().analyze_file(file_ctx)

    def _parse_findings(self, raw_text: str, file_ctx: FileContext) -> List[BugFinding]:
        try:
            parsed = json.loads(raw_text)
            items = parsed.get("findings", [])
            results: List[BugFinding] = []
            for item in items:
                sev_str = item.get("severity", "MEDIUM").upper()
                sev = Severity.__members__.get(sev_str, Severity.MEDIUM)
                results.append(
                    BugFinding(
                        file_path=file_ctx.rel_path,
                        line_start=int(item.get("line_start", 1)),
                        line_end=int(item.get("line_end", 1)),
                        title=str(item.get("title", "Detected Issue")),
                        category=str(item.get("category", "Logic Error")),
                        severity=sev,
                        description=str(item.get("description", "")),
                        remediation=str(item.get("remediation", "")),
                        code_snippet=str(item.get("code_snippet", "")),
                    )
                )
            return results
        except Exception:
            return MockProvider().analyze_file(file_ctx)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI-compatible REST API Provider (works with OpenAI, Groq, Ollama, DeepSeek, vLLM).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key or "sk-dummy"
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.url = f"{self.base_url}/chat/completions"

    def analyze_file(self, file_ctx: FileContext) -> List[BugFinding]:
        user_prompt = f"File: {file_ctx.rel_path} ({file_ctx.language})\n\n```\n{file_ctx.content}\n```"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                raw_text = res_json["choices"][0]["message"]["content"]
                return self._parse_findings(raw_text, file_ctx)
        except Exception:
            return MockProvider().analyze_file(file_ctx)

    def _parse_findings(self, raw_text: str, file_ctx: FileContext) -> List[BugFinding]:
        try:
            parsed = json.loads(raw_text)
            items = parsed.get("findings", [])
            results: List[BugFinding] = []
            for item in items:
                sev_str = item.get("severity", "MEDIUM").upper()
                sev = Severity.__members__.get(sev_str, Severity.MEDIUM)
                results.append(
                    BugFinding(
                        file_path=file_ctx.rel_path,
                        line_start=int(item.get("line_start", 1)),
                        line_end=int(item.get("line_end", 1)),
                        title=str(item.get("title", "Detected Issue")),
                        category=str(item.get("category", "Logic Error")),
                        severity=sev,
                        description=str(item.get("description", "")),
                        remediation=str(item.get("remediation", "")),
                        code_snippet=str(item.get("code_snippet", "")),
                    )
                )
            return results
        except Exception:
            return MockProvider().analyze_file(file_ctx)


def get_provider(
    name: str = "mock",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> BaseLLMProvider:
    """Factory to get the configured provider."""
    name = (name or "mock").lower()

    if name in ("gemini", "google"):
        if not api_key:
            # If no key provided, notify and fallback to mock
            return MockProvider()
        return GeminiProvider(api_key=api_key, model=model or "gemini-1.5-flash")

    if name in ("openai", "ollama", "groq", "deepseek"):
        url = base_url or ("http://localhost:11434/v1" if name == "ollama" else "https://api.openai.com/v1")
        default_model = "llama3" if name == "ollama" else "gpt-4o-mini"
        return OpenAIProvider(api_key=api_key or "", model=model or default_model, base_url=url)

    return MockProvider()

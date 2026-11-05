import ast
import json
import re
import urllib.request
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from backend.models.models import FileContext, Severity
from backend.models.hypothesis import BugHypothesis, BugStatus, Confidence
from backend.analysis.context import RepositoryContext

HYPOTHESIS_SYSTEM_PROMPT = """You are RepoSentinel, an advanced repository-aware autonomous bug hypothesis engine.
Your objective is to reason about how different modules, functions, and symbols interact across the codebase to uncover real vulnerabilities and logic bugs.

You are provided with:
1. The target source code file.
2. The Repository Cross-File Context (imported modules, function signatures, docstrings, caller usages, and contracts).

FOCUS YOUR REASONING ON CROSS-MODULE INTERACTIONS & ARCHITECTURAL WEAKNESSES:
1. Unsafe input flow: Untrusted data from callers passed into sinks without validation.
2. Incorrect assumptions & Missing validation: Caller assumes a function always returns valid data, but the callee contract specifies it can return None or raise an exception.
3. Exception-handling flaws: Swallowed exceptions masking failure or missing error handlers for callee exceptions.
4. Security vulnerabilities: Command injection, SQL injection, hardcoded credentials, insecure configuration.
5. Resource management: Leaked connections, descriptors, or locks across inter-module calls.

STATUS CLASSIFICATION RULE:
- Set status to "Likely Bug" if there is strong, direct structural evidence in the code and cross-module contracts.
- Set status to "Potential Bug" if the bug is plausible but depends on external runtime state or input boundaries.
- NEVER set status to "Confirmed Bug" (confirmation requires deterministic test execution).

RESPOND STRICTLY WITH A JSON OBJECT IN THIS EXACT FORMAT:
{
  "hypotheses": [
    {
      "hypothesis_id": "HYP-001",
      "title": "Concise bug title",
      "category": "Unsafe Input Flow" | "Incorrect Assumptions" | "Missing Validation" | "Exception Handling Problem" | "Security" | "Resource Management",
      "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "status": "Potential Bug" | "Likely Bug",
      "affected_file": "path/to/file.py",
      "affected_symbol": "function_or_class_name",
      "line_start": 10,
      "line_end": 14,
      "explanation": "Detailed explanation of the issue.",
      "reasoning": "Evidence citing caller-callee interactions, imported contracts, or code flows.",
      "related_symbols": ["module.callee_func", "caller_module.func"],
      "suggested_test": "Concrete test scenario describing input and expected assertion failure.",
      "code_snippet": "Relevant source line(s)",
      "remediation": "Suggested remediation code or approach."
    }
  ]
}
If no issues are found, return {"hypotheses": []}.
"""


class BaseHypothesisEngine(ABC):
    @abstractmethod
    def generate_hypotheses(
        self, file_ctx: FileContext, context: RepositoryContext
    ) -> List[BugHypothesis]:
        """Generate structured bug hypotheses for a file using repository context."""
        pass


class RuleBasedHypothesisEngine(BaseHypothesisEngine):
    """
    Deterministic repository-aware hypothesis generator.
    Works 100% offline with zero external dependencies.
    Analyzes inter-module assumptions, return contracts, and intra-file vulnerability patterns.
    """

    def generate_hypotheses(
        self, file_ctx: FileContext, context: RepositoryContext
    ) -> List[BugHypothesis]:
        hypotheses: List[BugHypothesis] = []
        lines = file_ctx.content.splitlines()

        # 1. Cross-Module Null/None Dereference & Missing Validation
        # Check if imported functions documented or named as returning None/Optional/User/Item are accessed without null checks
        hypotheses.extend(self._check_cross_module_null_assumptions(file_ctx, context, lines))

        # 2. Hardcoded Secrets (Security)
        for m in re.finditer(
            r"""(?i)(?:api_key|secret|password|auth_token|access_token|private_key)\s*=\s*['\"][A-Za-z0-9_\-\.\/+=]{8,}['\"]""",
            file_ctx.content,
        ):
            line_no = file_ctx.content[: m.start()].count("\n") + 1
            snippet = lines[line_no - 1].strip() if line_no <= len(lines) else m.group(0)
            symbol = self._find_enclosing_symbol(line_no, context)
            hypotheses.append(
                BugHypothesis(
                    hypothesis_id=f"HYP-SEC-CRED-{line_no}",
                    title="Hardcoded Sensitive Credential or Secret",
                    category="Potential Security Vulnerability",
                    severity=Severity.CRITICAL,
                    confidence=Confidence.HIGH,
                    status=BugStatus.LIKELY,
                    affected_file=file_ctx.rel_path,
                    affected_symbol=symbol,
                    line_start=line_no,
                    line_end=line_no,
                    explanation="Sensitive credential or token is hardcoded in source control.",
                    reasoning="Credential string matched known secret patterns; commits to version control expose authentication secrets.",
                    related_symbols=[],
                    suggested_test="Verify if token is valid and assert it should not be checked into repository history.",
                    code_snippet=snippet,
                    remediation="Extract credentials into environment variables or secrets manager.",
                )
            )

        # 3. Command Injection via shell=True
        for m in re.finditer(
            r"""(?:subprocess\.run|subprocess\.Popen|subprocess\.call|os\.system)\s*\([^)]*shell\s*=\s*True""",
            file_ctx.content,
        ):
            line_no = file_ctx.content[: m.start()].count("\n") + 1
            snippet = lines[line_no - 1].strip() if line_no <= len(lines) else m.group(0)
            symbol = self._find_enclosing_symbol(line_no, context)
            hypotheses.append(
                BugHypothesis(
                    hypothesis_id=f"HYP-SEC-CMD-{line_no}",
                    title="Command Injection via shell=True Execution",
                    category="Potential Security Vulnerability",
                    severity=Severity.CRITICAL,
                    confidence=Confidence.HIGH,
                    status=BugStatus.LIKELY,
                    affected_file=file_ctx.rel_path,
                    affected_symbol=symbol,
                    line_start=line_no,
                    line_end=line_no,
                    explanation="Execution of system command with shell=True allows arbitrary shell syntax injection.",
                    reasoning="Subprocess call passes user or runtime arguments through the system shell interpreter without argument escaping.",
                    related_symbols=[],
                    suggested_test="Supply argument containing command delimiters (e.g. '; id;') and assert command execution is blocked.",
                    code_snippet=snippet,
                    remediation="Pass command arguments as an array of strings without shell=True.",
                )
            )

        # 4. SQL Injection via Formatted String Query
        for m in re.finditer(
            r"""(?i)(?:(?:execute|cursor\.execute)\s*\(\s*f['\"]|f['\"][^\n\r]*(?:SELECT|INSERT|UPDATE|DELETE)[^\n\r]*\{[^}\n\r]+\})""",
            file_ctx.content,
        ):
            line_no = file_ctx.content[: m.start()].count("\n") + 1
            snippet = lines[line_no - 1].strip() if line_no <= len(lines) else m.group(0)
            symbol = self._find_enclosing_symbol(line_no, context)
            hypotheses.append(
                BugHypothesis(
                    hypothesis_id=f"HYP-SEC-SQL-{line_no}",
                    title="SQL Injection via Dynamic String Interpolation",
                    category="Potential Security Vulnerability",
                    severity=Severity.CRITICAL,
                    confidence=Confidence.HIGH,
                    status=BugStatus.LIKELY,
                    affected_file=file_ctx.rel_path,
                    affected_symbol=symbol,
                    line_start=line_no,
                    line_end=line_no,
                    explanation="Dynamic formatting of variables into SQL statement bypasses query parameterization.",
                    reasoning="Query string interpolates variables directly; untrusted input can alter SQL abstract syntax tree.",
                    related_symbols=[],
                    suggested_test="Supply username containing single quote (\"admin' OR '1'='1\") and observe query syntax bypass.",
                    code_snippet=snippet,
                    remediation="Use parameterized queries: cursor.execute('SELECT ... WHERE u = %s', (val,))",
                )
            )

        # 5. Disabled SSL/TLS Verification
        for m in re.finditer(r"""requests\.(?:get|post|put|delete)\s*\([^)]*verify\s*=\s*False""", file_ctx.content):
            line_no = file_ctx.content[: m.start()].count("\n") + 1
            snippet = lines[line_no - 1].strip() if line_no <= len(lines) else m.group(0)
            symbol = self._find_enclosing_symbol(line_no, context)
            hypotheses.append(
                BugHypothesis(
                    hypothesis_id=f"HYP-CONF-SSL-{line_no}",
                    title="Insecure Configuration: Disabled SSL Certificate Verification",
                    category="Insecure Configuration",
                    severity=Severity.HIGH,
                    confidence=Confidence.HIGH,
                    status=BugStatus.LIKELY,
                    affected_file=file_ctx.rel_path,
                    affected_symbol=symbol,
                    line_start=line_no,
                    line_end=line_no,
                    explanation="verify=False disables TLS peer certificate verification.",
                    reasoning="HTTP client request ignores certificate validity, enabling Man-in-the-Middle traffic interception.",
                    related_symbols=[],
                    suggested_test="Assert requests connection enforces verify=True with valid certificate authority bundle.",
                    code_snippet=snippet,
                    remediation="Remove verify=False or provide trusted certificate bundle path.",
                )
            )

        # 6. Swallowed Exception / Silent Failure
        for m in re.finditer(r"""except(?:\s*Exception)?\s*:\s*\n\s*(?:pass|\.\.\.)""", file_ctx.content):
            line_no = file_ctx.content[: m.start()].count("\n") + 1
            snippet = lines[line_no - 1].strip() if line_no <= len(lines) else m.group(0)
            symbol = self._find_enclosing_symbol(line_no, context)
            hypotheses.append(
                BugHypothesis(
                    hypothesis_id=f"HYP-LOGIC-EXC-{line_no}",
                    title="Exception Handling Problem: Swallowed Exception Block",
                    category="Exception-Handling Problems",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    status=BugStatus.LIKELY,
                    affected_file=file_ctx.rel_path,
                    affected_symbol=symbol,
                    line_start=line_no,
                    line_end=line_no,
                    explanation="Empty except: pass block silently ignores runtime failures.",
                    reasoning="Catching base Exception without logging or re-raising conceals corrupted program state and debugging traces.",
                    related_symbols=[],
                    suggested_test="Trigger an intentional runtime exception inside try block and assert exception is logged or handled.",
                    code_snippet=snippet,
                    remediation="Log exception details with logger.exception() or handle specific expected exceptions.",
                )
            )

        # 7. Resource Management Problem: Unclosed file/socket handle
        for m in re.finditer(r"""(?:open\s*\([^)]+\))(?![\s\S]{0,100}\bwith\b)""", file_ctx.content):
            line_no = file_ctx.content[: m.start()].count("\n") + 1
            snippet = lines[line_no - 1].strip() if line_no <= len(lines) else m.group(0)
            symbol = self._find_enclosing_symbol(line_no, context)
            hypotheses.append(
                BugHypothesis(
                    hypothesis_id=f"HYP-RES-LEAK-{line_no}",
                    title="Resource Management Problem: Unclosed File Handle",
                    category="Resource-Management Problems",
                    severity=Severity.LOW,
                    confidence=Confidence.MEDIUM,
                    status=BugStatus.POTENTIAL,
                    affected_file=file_ctx.rel_path,
                    affected_symbol=symbol,
                    line_start=line_no,
                    line_end=line_no,
                    explanation="File descriptor opened without context manager or explicit close call.",
                    reasoning="Unclosed file objects risk descriptor exhaustion under high concurrent load or exceptions.",
                    related_symbols=[],
                    suggested_test="Open multiple files in a tight loop and check process file descriptor limits.",
                    code_snippet=snippet,
                    remediation="Use 'with open(...) as f:' context manager.",
                )
            )

        return hypotheses

    def _check_cross_module_null_assumptions(
        self, file_ctx: FileContext, context: RepositoryContext, lines: List[str]
    ) -> List[BugHypothesis]:
        """
        Reason about cross-module assumptions:
        When a function imported from another module can return None or fail,
        check if the caller directly subscripts or invokes methods on it without a null check.
        """
        hypotheses: List[BugHypothesis] = []
        if not context.imported_symbols:
            return hypotheses

        # Identify imported functions whose docs or names indicate they return Optional / None / User / Token
        nullable_funcs = {}
        for imp in context.imported_symbols:
            name_lower = imp.symbol_name.lower()
            doc_lower = (imp.docstring or "").lower()
            if (
                "none" in doc_lower
                or "optional" in doc_lower
                or "invalid" in doc_lower
                or "verify" in name_lower
                or "authenticate" in name_lower
                or "get_" in name_lower
                or "find_" in name_lower
            ):
                nullable_funcs[imp.symbol_name] = imp

        if not nullable_funcs:
            return hypotheses

        # Look for pattern: var = nullable_func(...) followed by var[...] or var.attr without 'if var'
        for func_name, imp_ctx in nullable_funcs.items():
            pattern = rf"""(\b[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*{func_name}\s*\("""
            for match in re.finditer(pattern, file_ctx.content):
                var_name = match.group(1)
                call_pos = match.start()
                line_no = file_ctx.content[:call_pos].count("\n") + 1

                # Search downstream lines in the same function for unsafe dereference
                subsequent_text = "\n".join(lines[line_no : min(len(lines), line_no + 12)])
                deref_pattern = rf"""\b{var_name}\s*\[|\b{var_name}\.[a-zA-Z_]"""
                guard_pattern = rf"""if\s+(?:not\s+)?{var_name}\b|if\s+{var_name}\s+is\s+(?:not\s+)?None"""

                if re.search(deref_pattern, subsequent_text) and not re.search(guard_pattern, subsequent_text):
                    symbol = self._find_enclosing_symbol(line_no, context)
                    hypotheses.append(
                        BugHypothesis(
                            hypothesis_id=f"HYP-CROSS-NULL-{line_no}",
                            title=f"Incorrect Assumption: Unchecked Return Value from `{func_name}`",
                            category="Incorrect Assumptions",
                            severity=Severity.HIGH,
                            confidence=Confidence.HIGH,
                            status=BugStatus.LIKELY,
                            affected_file=file_ctx.rel_path,
                            affected_symbol=symbol,
                            line_start=line_no,
                            line_end=line_no + 3,
                            explanation=(
                                f"Variable `{var_name}` is assigned from cross-module function `{func_name}` "
                                f"(from `{imp_ctx.module_file}`) and dereferenced without checking if it is None."
                            ),
                            reasoning=(
                                f"Cross-module dependency analysis: `{imp_ctx.module_file}` defines `{func_name}`. "
                                f"Its contract/docstring indicates it can return None on failure. "
                                f"`{file_ctx.rel_path}` directly accesses properties on `{var_name}` without a null guard."
                            ),
                            related_symbols=[f"{imp_ctx.module_file}:{func_name}"],
                            suggested_test=(
                                f"Mock or trigger `{func_name}` to return None and execute `{symbol or 'caller'}`; "
                                f"assert that TypeError or AttributeError occurs instead of handled failure."
                            ),
                            code_snippet=lines[line_no - 1].strip() if line_no <= len(lines) else "",
                            remediation=f"Add validation: `if {var_name} is None: raise ...` before accessing properties.",
                        )
                    )

        return hypotheses

    def _find_enclosing_symbol(self, line_no: int, context: RepositoryContext) -> Optional[str]:
        for sym in context.defined_symbols:
            if sym.line_start <= line_no <= sym.line_end:
                if sym.parent:
                    return f"{sym.parent}.{sym.name}"
                return sym.name
        return None


class LLMHypothesisEngine(BaseHypothesisEngine):
    """
    LLM-powered hypothesis generator supporting Gemini, OpenAI, DeepSeek, and Ollama.
    Enriches prompts with cross-file repository context and validates structured output.
    """

    def __init__(
        self,
        provider_name: str = "gemini",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider_name = provider_name.lower()
        self.api_key = api_key or ""
        self.model = model
        self.base_url = base_url
        self.fallback_engine = RuleBasedHypothesisEngine()

    def generate_hypotheses(
        self, file_ctx: FileContext, context: RepositoryContext
    ) -> List[BugHypothesis]:
        # If no API key or provider is mock, use deterministic engine
        if self.provider_name == "mock" or (not self.api_key and self.provider_name != "ollama"):
            return self.fallback_engine.generate_hypotheses(file_ctx, context)

        repo_context_block = context.to_prompt_context()
        user_prompt = (
            f"{repo_context_block}\n\n"
            f"### Target Source Code for `{file_ctx.rel_path}` ({file_ctx.language}):\n"
            f"```\n{file_ctx.content}\n```"
        )

        try:
            if self.provider_name in ("gemini", "google"):
                raw_json = self._call_gemini(user_prompt)
            else:
                raw_json = self._call_openai(user_prompt)

            return self._parse_and_validate(raw_json, file_ctx)
        except Exception:
            # On network or API error, fall back gracefully to deterministic rule engine
            return self.fallback_engine.generate_hypotheses(file_ctx, context)

    def _call_gemini(self, user_prompt: str) -> str:
        model = self.model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": f"{HYPOTHESIS_SYSTEM_PROMPT}\n\n{user_prompt}"}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.2},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=35) as res:
            res_json = json.loads(res.read().decode("utf-8"))
            return res_json["candidates"][0]["content"]["parts"][0]["text"]

    def _call_openai(self, user_prompt: str) -> str:
        base_url = self.base_url or ("http://localhost:11434/v1" if self.provider_name == "ollama" else "https://api.openai.com/v1")
        model = self.model or ("llama3" if self.provider_name == "ollama" else "gpt-4o-mini")
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": HYPOTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=35) as res:
            res_json = json.loads(res.read().decode("utf-8"))
            return res_json["choices"][0]["message"]["content"]

    def _parse_and_validate(self, raw_text: str, file_ctx: FileContext) -> List[BugHypothesis]:
        """
        Parse raw JSON output and validate against schema invariants.
        Enforces that LLM cannot self-certify as 'Confirmed Bug'.
        """
        if not raw_text or not raw_text.strip():
            return []

        # Strip markdown ```json blocks if present
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            parsed = json.loads(cleaned)
        except Exception:
            return []

        raw_items = parsed.get("hypotheses", [])
        if not isinstance(raw_items, list):
            return []

        validated: List[BugHypothesis] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            item.setdefault("affected_file", file_ctx.rel_path)
            try:
                hyp = BugHypothesis.from_dict(item)
                # Enforce rule: LLM cannot confirm bugs
                if hyp.status == BugStatus.CONFIRMED:
                    hyp.status = BugStatus.LIKELY
                hyp.validate()
                validated.append(hyp)
            except Exception:
                continue

        return validated

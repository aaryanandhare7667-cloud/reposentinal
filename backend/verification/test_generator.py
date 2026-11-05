import ast
import hashlib
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from backend.models.hypothesis import BugHypothesis


@dataclass
class AdversarialTest:
    """
    Executable reproduction test designed to trigger or falsify a BugHypothesis.
    """
    test_id: str
    hypothesis_id: str
    target_file: str
    target_symbol: Optional[str]
    test_objective: str
    setup_code: str
    adversarial_input: str
    expected_vulnerable_behavior: str
    expected_safe_behavior: str
    executable_code: str
    timeout_seconds: int = 10
    required_imports: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TestSafetyValidator:
    """
    Validates that generated test scripts do not contain arbitrary destructive system calls.
    """
    DANGEROUS_PATTERNS = [
        r"""shutil\.rmtree\s*\(\s*['\"][/\\]""",  # rmtree /
        r"""os\.remove\s*\(\s*['\"][/\\]""",
        r"""subprocess\.(?:run|call|Popen)\s*\(\s*['\"][^'\"]*(?:rm\s+-rf\s+[/~]|mkfs|dd\s+if=)""",
        r"""os\.system\s*\(\s*['\"][^'\"]*(?:rm\s+-rf\s+[/~]|mkfs|dd\s+if=)""",
    ]

    @classmethod
    def validate(cls, code: str) -> None:
        if not code or not code.strip():
            raise ValueError("Test code cannot be empty")

        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                raise ValueError(f"Dangerous destructive pattern detected in test code: {pattern}")

        # Ensure code is syntactically valid Python
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in generated test: {e}")


class DeterministicTestGenerator:
    """
    Synthesizes deterministic, executable adversarial reproduction tests for hypotheses.
    """

    def generate_test(self, hypothesis: BugHypothesis) -> Optional[AdversarialTest]:
        cat_lower = hypothesis.category.lower()
        title_lower = hypothesis.title.lower()

        test_id = f"TEST-{hypothesis.hypothesis_id}"
        target_stem = Path(hypothesis.affected_file).stem

        # Strategy 1: Cross-Module Null / Unchecked Return Assumption
        if "incorrect assumptions" in cat_lower or "unchecked return" in title_lower:
            return self._generate_null_assumption_test(hypothesis, test_id, target_stem)

        # Strategy 2: SQL Injection
        elif "sql" in title_lower or "sql injection" in cat_lower:
            return self._generate_sql_injection_test(hypothesis, test_id, target_stem)

        # Strategy 3: Command Injection via shell=True
        elif "command injection" in title_lower or "shell=true" in title_lower:
            return self._generate_command_injection_test(hypothesis, test_id, target_stem)

        # Strategy 4: Insecure Configuration (Disabled SSL)
        elif "ssl" in title_lower or "verify=false" in title_lower:
            return self._generate_ssl_verification_test(hypothesis, test_id, target_stem)

        # Strategy 5: Swallowed Exception
        elif "swallowed exception" in title_lower or "exception handling" in cat_lower:
            return self._generate_swallowed_exception_test(hypothesis, test_id, target_stem)

        # Default fallback generic test
        return self._generate_generic_assertion_test(hypothesis, test_id, target_stem)

    def _generate_null_assumption_test(
        self, hypothesis: BugHypothesis, test_id: str, target_stem: str
    ) -> AdversarialTest:
        callee_module = "auth_service"
        callee_func = "verify_jwt_token"

        if hypothesis.related_symbols:
            parts = hypothesis.related_symbols[0].split(":")
            if len(parts) == 2:
                callee_module = Path(parts[0]).stem
                callee_func = parts[1]

        target_func = hypothesis.affected_symbol or "process_order_checkout"

        code = f'''# Auto-generated Adversarial Reproduction Test
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    import {target_stem}
except Exception as e:
    print(f"SETUP_ERROR: Failed to import target module {target_stem}: {{e}}")
    sys.exit(3)

# Force the dependency ({callee_module}.{callee_func}) to return None
try:
    patch_target = f"{target_stem}.{callee_func}" if hasattr({target_stem}, "{callee_func}") else f"{callee_module}.{callee_func}"
    with patch(patch_target, return_value=None):
        func = getattr({target_stem}, "{target_func}", None)
        if not func:
            print(f"SETUP_ERROR: Function {target_func} not found in {target_stem}")
            sys.exit(3)

        try:
            # Trigger target function with test inputs
            func("invalid_token", "ORD-TEST-1", 10.0)
            # If function gracefully returned without raising unhandled TypeError/AttributeError:
            print("SAFE_HANDLING_OBSERVED: Function gracefully handled None without crashing.")
            sys.exit(2)
        except (TypeError, AttributeError) as exc:
            # Target crashed due to unhandled None dereference -> Vulnerability Reproduced!
            print(f"VULNERABILITY_REPRODUCED: {{type(exc).__name__}}: {{exc}}")
            sys.exit(0)
        except Exception as exc:
            print(f"OTHER_EXCEPTION: {{type(exc).__name__}}: {{exc}}")
            sys.exit(1)
except Exception as e:
    print(f"EXECUTION_ERROR: {{e}}")
    sys.exit(3)
'''
        TestSafetyValidator.validate(code)

        return AdversarialTest(
            test_id=test_id,
            hypothesis_id=hypothesis.hypothesis_id,
            target_file=hypothesis.affected_file,
            target_symbol=target_func,
            test_objective=f"Verify unhandled TypeError/AttributeError when {callee_func} returns None",
            setup_code=f"Mock {callee_module}.{callee_func} to return None",
            adversarial_input="invalid_token",
            expected_vulnerable_behavior="TypeError or AttributeError raised due to unhandled None dereference",
            expected_safe_behavior="Function validates return value and returns error response or raises custom AuthError",
            executable_code=code,
            timeout_seconds=10,
            required_imports=["unittest.mock"],
        )

    def _generate_sql_injection_test(
        self, hypothesis: BugHypothesis, test_id: str, target_stem: str
    ) -> AdversarialTest:
        target_func = hypothesis.affected_symbol or "query_user_profile"

        code = f'''# Auto-generated Adversarial SQL Injection Test
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    import {target_stem}
except Exception as e:
    print(f"SETUP_ERROR: Failed to import target module {target_stem}: {{e}}")
    sys.exit(3)

func = getattr({target_stem}, "{target_func}", None)
if not func:
    print(f"SETUP_ERROR: Function {target_func} not found")
    sys.exit(3)

# Test with SQL injection probe
malicious_id = "test' OR '1'='1"
mock_cursor = MagicMock()

try:
    # Attempt call with signature variations
    try:
        res = func(mock_cursor, malicious_id)
    except TypeError:
        try:
            res = func(malicious_id)
        except TypeError:
            res = func("valid_token", malicious_id, 100)

    # Inspect executed queries or return values for raw injection
    executed_sql = ""
    for call_item in mock_cursor.execute.call_args_list:
        args, _ = call_item
        if args:
            executed_sql += str(args[0])

    if not executed_sql and isinstance(res, str):
        executed_sql = res

    if "OR '1'='1" in executed_sql or "test' OR '1'='1" in executed_sql:
        print(f"VULNERABILITY_REPRODUCED: Unescaped SQL injection probe found in query: {{executed_sql}}")
        sys.exit(0)
    else:
        print("SAFE_HANDLING_OBSERVED: SQL query was parameterized or sanitized.")
        sys.exit(2)
except Exception as exc:
    print(f"EXECUTION_ERROR: {{type(exc).__name__}}: {{exc}}")
    sys.exit(1)
'''
        TestSafetyValidator.validate(code)

        return AdversarialTest(
            test_id=test_id,
            hypothesis_id=hypothesis.hypothesis_id,
            target_file=hypothesis.affected_file,
            target_symbol=target_func,
            test_objective="Assert unescaped SQL payload appears directly in query execution",
            setup_code="Mock database cursor and supply injection payload",
            adversarial_input="test' OR '1'='1",
            expected_vulnerable_behavior="Raw payload concatenated directly into SQL string",
            expected_safe_behavior="Query utilizes parameterized placeholders or rejects dangerous syntax",
            executable_code=code,
            timeout_seconds=10,
            required_imports=["unittest.mock"],
        )

    def _generate_command_injection_test(
        self, hypothesis: BugHypothesis, test_id: str, target_stem: str
    ) -> AdversarialTest:
        target_func = hypothesis.affected_symbol or "run_user_cmd"

        code = f'''# Auto-generated Adversarial Command Injection Test
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    import {target_stem}
except Exception as e:
    print(f"SETUP_ERROR: Failed to import {target_stem}: {{e}}")
    sys.exit(3)

func = getattr({target_stem}, "{target_func}", None)
if not func:
    print(f"SETUP_ERROR: Function {target_func} not found")
    sys.exit(3)

with patch("subprocess.run") as mock_sub:
    mock_sub.return_value = MagicMock(returncode=0)
    try:
        func("; echo VULNERABLE ;")
        # Check if shell=True was passed in call kwargs
        if mock_sub.call_count > 0:
            _, kwargs = mock_sub.call_args
            if kwargs.get("shell") is True:
                print("VULNERABILITY_REPRODUCED: Command executed with shell=True enabled.")
                sys.exit(0)
            else:
                print("SAFE_HANDLING_OBSERVED: Command executed safely without shell=True.")
                sys.exit(2)
        else:
            print("SAFE_HANDLING_OBSERVED: No shell execution was performed.")
            sys.exit(2)
    except Exception as exc:
        print(f"EXECUTION_ERROR: {{exc}}")
        sys.exit(1)
'''
        TestSafetyValidator.validate(code)

        return AdversarialTest(
            test_id=test_id,
            hypothesis_id=hypothesis.hypothesis_id,
            target_file=hypothesis.affected_file,
            target_symbol=target_func,
            test_objective="Assert subprocess is invoked with shell=True on untrusted input",
            setup_code="Mock subprocess.run and record invocation kwargs",
            adversarial_input="; echo VULNERABLE ;",
            expected_vulnerable_behavior="Invocation with shell=True",
            expected_safe_behavior="Execution with argument list and shell=False",
            executable_code=code,
            timeout_seconds=10,
            required_imports=["unittest.mock"],
        )

    def _generate_ssl_verification_test(
        self, hypothesis: BugHypothesis, test_id: str, target_stem: str
    ) -> AdversarialTest:
        target_func = hypothesis.affected_symbol or "fetch_data"

        code = f'''# Auto-generated Insecure SSL Configuration Test
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    import {target_stem}
except Exception as e:
    print(f"SETUP_ERROR: Failed to import {target_stem}: {{e}}")
    sys.exit(3)

func = getattr({target_stem}, "{target_func}", None)
if not func:
    print(f"SETUP_ERROR: Function {target_func} not found")
    sys.exit(3)

with patch("requests.get") as mock_get:
    mock_get.return_value = MagicMock(json=lambda: {{}})
    try:
        func("https://example.com/api")
        if mock_get.call_count > 0:
            _, kwargs = mock_get.call_args
            if kwargs.get("verify") is False:
                print("VULNERABILITY_REPRODUCED: HTTP client executed with verify=False.")
                sys.exit(0)
            else:
                print("SAFE_HANDLING_OBSERVED: SSL certificate verification is enabled.")
                sys.exit(2)
        else:
            print("SETUP_ERROR: requests.get was not invoked.")
            sys.exit(3)
    except Exception as exc:
        print(f"EXECUTION_ERROR: {{exc}}")
        sys.exit(1)
'''
        TestSafetyValidator.validate(code)

        return AdversarialTest(
            test_id=test_id,
            hypothesis_id=hypothesis.hypothesis_id,
            target_file=hypothesis.affected_file,
            target_symbol=target_func,
            test_objective="Verify whether HTTPS requests disable peer certificate validation",
            setup_code="Mock requests.get and inspect verify kwarg",
            adversarial_input="https://example.com/api",
            expected_vulnerable_behavior="requests.get called with verify=False",
            expected_safe_behavior="verify=True or omitted (default secure)",
            executable_code=code,
            timeout_seconds=10,
            required_imports=["unittest.mock"],
        )

    def _generate_swallowed_exception_test(
        self, hypothesis: BugHypothesis, test_id: str, target_stem: str
    ) -> AdversarialTest:
        target_func = hypothesis.affected_symbol or "process_file_data"

        code = f'''# Auto-generated Swallowed Exception Test
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    import {target_stem}
except Exception as e:
    print(f"SETUP_ERROR: Failed to import {target_stem}: {{e}}")
    sys.exit(3)

func = getattr({target_stem}, "{target_func}", None)
if not func:
    print(f"SETUP_ERROR: Function {target_func} not found")
    sys.exit(3)

# Pass nonexistent file or bad argument that should raise an error
try:
    res = func("/nonexistent/file/path/that/cannot/exist.txt")
    # If the function returned None silently without raising FileNotFoundError:
    if res is None:
        print("VULNERABILITY_REPRODUCED: Silent failure observed; exception was swallowed without trace.")
        sys.exit(0)
    else:
        print(f"SAFE_HANDLING_OBSERVED: Function returned explicit result: {{res}}")
        sys.exit(2)
except Exception as exc:
    print(f"SAFE_HANDLING_OBSERVED: Exception was raised or propagated: {{type(exc).__name__}}")
    sys.exit(2)
'''
        TestSafetyValidator.validate(code)

        return AdversarialTest(
            test_id=test_id,
            hypothesis_id=hypothesis.hypothesis_id,
            target_file=hypothesis.affected_file,
            target_symbol=target_func,
            test_objective="Assert unhandled exceptions are swallowed silently with None return",
            setup_code="Invoke target with nonexistent file parameter",
            adversarial_input="/nonexistent/file.txt",
            expected_vulnerable_behavior="Silent None return without exception",
            expected_safe_behavior="Exception logged or re-raised",
            executable_code=code,
            timeout_seconds=10,
            required_imports=[],
        )

    def _generate_generic_assertion_test(
        self, hypothesis: BugHypothesis, test_id: str, target_stem: str
    ) -> AdversarialTest:
        code = f'''# Generic Hypothesis Probe Test
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    import {target_stem}
    print("MODULE_LOADED_OK")
    sys.exit(2)  # Inconclusive/Not reproduced directly without specific driver
except Exception as e:
    print(f"IMPORT_FAILURE: {{e}}")
    sys.exit(3)
'''
        TestSafetyValidator.validate(code)

        return AdversarialTest(
            test_id=test_id,
            hypothesis_id=hypothesis.hypothesis_id,
            target_file=hypothesis.affected_file,
            target_symbol=hypothesis.affected_symbol,
            test_objective="Smoke check target module syntax and load integrity",
            setup_code="Import target module",
            adversarial_input="none",
            expected_vulnerable_behavior="N/A",
            expected_safe_behavior="Module loads cleanly",
            executable_code=code,
            timeout_seconds=5,
        )

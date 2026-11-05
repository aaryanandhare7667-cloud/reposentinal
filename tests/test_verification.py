import os
import unittest
from pathlib import Path

from reposentinal.hypothesis import BugHypothesis, BugStatus, Confidence
from reposentinal.models import Severity, FileContext
from reposentinal.test_generator import (
    AdversarialTest,
    TestSafetyValidator,
    DeterministicTestGenerator,
)
from reposentinal.sandbox import SafeSubprocessSandbox, get_sandbox_backend
from reposentinal.verification import (
    VerificationStatus,
    ExecutionResult,
    VerificationEvidence,
)
from reposentinal.verifier import HypothesisVerifier
from reposentinal.analyzer import RepoSentinelAgent
from reposentinal.providers import MockProvider
from reposentinal.scanner import scan_repository


class TestVerificationPipeline(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path(__file__).parent / "fixtures" / "cross_file_repo"
        self.safe_fixtures_dir = Path(__file__).parent / "fixtures" / "safe_repo"

    def test_adversarial_test_generation_null_assumption(self):
        gen = DeterministicTestGenerator()
        hyp = BugHypothesis(
            hypothesis_id="HYP-T1",
            title="Unchecked Return Assumption",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.LIKELY,
            affected_file=str(self.fixtures_dir / "order_service.py"),
            affected_symbol="process_order_checkout",
            line_start=6,
            line_end=8,
            explanation="Assumes verify_jwt_token never returns None",
            reasoning="verify_jwt_token returns None on invalid tokens",
            related_symbols=["auth_service.py:verify_jwt_token"],
            suggested_test="Call with invalid token",
        )

        test = gen.generate_test(hyp)
        self.assertIsNotNone(test)
        self.assertEqual(test.hypothesis_id, "HYP-T1")
        self.assertEqual(test.target_symbol, "process_order_checkout")
        self.assertIn("patch_target", test.executable_code)
        self.assertIn("VULNERABILITY_REPRODUCED", test.executable_code)

        # Validation should succeed without error
        TestSafetyValidator.validate(test.executable_code)

    def test_adversarial_test_generation_sql_injection(self):
        gen = DeterministicTestGenerator()
        hyp = BugHypothesis(
            hypothesis_id="HYP-T2",
            title="SQL Injection in Order Query",
            category="Security Vulnerabilities",
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            status=BugStatus.LIKELY,
            affected_file=str(self.fixtures_dir / "order_service.py"),
            affected_symbol="process_order_checkout",
            line_start=12,
            line_end=13,
            explanation="Unsanitized order_id concatenated into SQL query",
            reasoning="Direct f-string SQL interpolation",
            suggested_test="Test with malicious payload",
        )

        test = gen.generate_test(hyp)
        self.assertIsNotNone(test)
        self.assertIn("OR '1'='1", test.executable_code)
        TestSafetyValidator.validate(test.executable_code)

    def test_test_safety_validator_rejects_dangerous_patterns(self):
        dangerous_codes = [
            "import shutil\nshutil.rmtree('/')",
            "import os\nos.remove('/etc/passwd')",
            "import subprocess\nsubprocess.run('rm -rf /', shell=True)",
            "import os\nos.system('dd if=/dev/zero of=/dev/sda')",
        ]

        for code in dangerous_codes:
            with self.assertRaises(ValueError):
                TestSafetyValidator.validate(code)

    def test_test_safety_validator_rejects_malformed_syntax(self):
        with self.assertRaises(ValueError):
            TestSafetyValidator.validate("def broken_syntax(:")

    def test_test_safety_validator_rejects_empty_code(self):
        with self.assertRaises(ValueError):
            TestSafetyValidator.validate("   \n  ")

    def test_sandbox_lifecycle_and_output_capture(self):
        sandbox = SafeSubprocessSandbox()
        test = AdversarialTest(
            test_id="TEST-SMOKE-1",
            hypothesis_id="HYP-SMOKE-1",
            target_file="none.py",
            target_symbol=None,
            test_objective="Verify stdout capture",
            setup_code="none",
            adversarial_input="none",
            expected_vulnerable_behavior="none",
            expected_safe_behavior="none",
            executable_code="print('HELLO_SANDBOX_STDOUT')\nimport sys\nsys.exit(0)\n",
            timeout_seconds=5,
        )

        res = sandbox.execute(test, self.fixtures_dir)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("HELLO_SANDBOX_STDOUT", res.stdout)
        self.assertFalse(res.timed_out)
        self.assertGreater(res.duration_seconds, 0)
        self.assertEqual(res.sandbox_backend, "safe_subprocess")

    def test_sandbox_timeout_handling(self):
        sandbox = SafeSubprocessSandbox()
        test = AdversarialTest(
            test_id="TEST-TIMEOUT",
            hypothesis_id="HYP-TIMEOUT",
            target_file="none.py",
            target_symbol=None,
            test_objective="Assert timeout trigger",
            setup_code="none",
            adversarial_input="none",
            expected_vulnerable_behavior="none",
            expected_safe_behavior="none",
            executable_code="import time\ntime.sleep(5)\n",
            timeout_seconds=1,
        )

        res = sandbox.execute(test, self.fixtures_dir)
        self.assertTrue(res.timed_out)
        self.assertEqual(res.exit_code, -1)
        self.assertIn("timed out after 1 seconds", res.stderr)

    def test_sandbox_scrubs_host_secrets(self):
        os.environ["OPENAI_API_KEY"] = "sk-sensitive-secret-token"
        os.environ["GEMINI_API_KEY"] = "gemini-secret-api-key"

        try:
            sandbox = SafeSubprocessSandbox()
            test = AdversarialTest(
                test_id="TEST-ENV-SCRUB",
                hypothesis_id="HYP-ENV",
                target_file="none.py",
                target_symbol=None,
                test_objective="Assert host secrets are scrubbed",
                setup_code="none",
                adversarial_input="none",
                expected_vulnerable_behavior="none",
                expected_safe_behavior="none",
                executable_code="""import os, sys
if os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY"):
    print("LEAK_DETECTED")
    sys.exit(1)
print("SECRETS_SCRUBBED_CLEAN")
sys.exit(0)
""",
                timeout_seconds=5,
            )

            res = sandbox.execute(test, self.fixtures_dir)
            self.assertEqual(res.exit_code, 0)
            self.assertIn("SECRETS_SCRUBBED_CLEAN", res.stdout)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("GEMINI_API_KEY", None)

    def test_reproduction_on_vulnerable_fixture(self):
        hyp = BugHypothesis(
            hypothesis_id="HYP-REPRO-1",
            title="Unchecked Return Assumption",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.LIKELY,
            affected_file=str(self.fixtures_dir / "order_service.py"),
            affected_symbol="process_order_checkout",
            line_start=6,
            line_end=8,
            explanation="Assumes verify_jwt_token never returns None",
            reasoning="verify_jwt_token returns None on invalid tokens",
            related_symbols=["auth_service.py:verify_jwt_token"],
            suggested_test="Call with invalid token",
        )

        verifier = HypothesisVerifier(sandbox=SafeSubprocessSandbox())
        evidence = verifier.verify_hypothesis(hyp, self.fixtures_dir)

        # Vulnerability should be reproduced
        self.assertEqual(evidence.status, VerificationStatus.REPRODUCED)
        self.assertIn("TypeError", evidence.reproduction_trace)
        # Hypothesis status should be promoted to Confirmed Bug
        self.assertEqual(hyp.status, BugStatus.CONFIRMED)
        self.assertTrue(hyp.is_verified)

    def test_false_positive_differentiation(self):
        # Test safe_order_service.py which handles None gracefully
        hyp = BugHypothesis(
            hypothesis_id="HYP-FP-1",
            title="Unchecked Return Assumption",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.LIKELY,
            affected_file=str(self.safe_fixtures_dir / "safe_order_service.py"),
            affected_symbol="safe_checkout",
            line_start=10,
            line_end=12,
            explanation="Assumes verify_jwt_token never returns None",
            reasoning="verify_jwt_token returns None on invalid tokens",
            related_symbols=["auth_service.py:verify_jwt_token"],
            suggested_test="Call with invalid token",
        )

        verifier = HypothesisVerifier(sandbox=SafeSubprocessSandbox())
        evidence = verifier.verify_hypothesis(hyp, self.safe_fixtures_dir)

        # Since safe_checkout gracefully checks user is None, it should NOT reproduce vulnerability
        self.assertEqual(evidence.status, VerificationStatus.FALSE_POSITIVE)
        # Crucial invariant: Hypotheses must NOT be confirmed if safe behavior is observed!
        self.assertNotEqual(hyp.status, BugStatus.CONFIRMED)
        self.assertFalse(hyp.is_verified)

    def test_inconclusive_on_setup_failure(self):
        hyp = BugHypothesis(
            hypothesis_id="HYP-INCONCL",
            title="Unchecked Return Assumption",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.LIKELY,
            affected_file="/nonexistent/module_file.py",
            affected_symbol="some_func",
            line_start=1,
            line_end=5,
            explanation="Testing setup failure",
            reasoning="Testing",
            suggested_test="Test",
        )

        verifier = HypothesisVerifier(sandbox=SafeSubprocessSandbox())
        evidence = verifier.verify_hypothesis(hyp, self.fixtures_dir)

        self.assertEqual(evidence.status, VerificationStatus.INCONCLUSIVE)
        self.assertNotEqual(hyp.status, BugStatus.CONFIRMED)

    def test_research_metrics_calculation(self):
        verifier = HypothesisVerifier(sandbox=SafeSubprocessSandbox())
        hyp1 = BugHypothesis(
            hypothesis_id="HYP-M1",
            title="Unchecked Return Assumption",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.LIKELY,
            affected_file=str(self.fixtures_dir / "order_service.py"),
            affected_symbol="process_order_checkout",
            line_start=6,
            line_end=8,
            explanation="Test",
            reasoning="Test",
            related_symbols=["auth_service.py:verify_jwt_token"],
            suggested_test="Test",
        )
        hyp2 = BugHypothesis(
            hypothesis_id="HYP-M2",
            title="Unchecked Return Assumption",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.LIKELY,
            affected_file=str(self.safe_fixtures_dir / "safe_order_service.py"),
            affected_symbol="safe_checkout",
            line_start=10,
            line_end=12,
            explanation="Test",
            reasoning="Test",
            related_symbols=["auth_service.py:verify_jwt_token"],
            suggested_test="Test",
        )

        updated_hyps, evidence_list, metrics = verifier.verify_all([hyp1, hyp2], self.fixtures_dir)
        self.assertEqual(metrics["total_hypotheses"], 2)
        self.assertEqual(metrics["tests_executed"], 2)
        self.assertEqual(metrics["reproduced_count"], 1)
        self.assertEqual(metrics["confirmed_count"], 1)
        self.assertEqual(metrics["false_positive_count"], 1)
        self.assertEqual(metrics["reproduction_rate"], 0.5)
        self.assertEqual(metrics["sandbox_backend"], "safe_subprocess")

    def test_end_to_end_agent_with_verification(self):
        files = scan_repository(self.fixtures_dir)
        agent = RepoSentinelAgent(
            provider=MockProvider(),
            verifier=HypothesisVerifier(sandbox=SafeSubprocessSandbox()),
            verify=True,
            target_root_dir=self.fixtures_dir,
        )

        summary = agent.analyze("Cross-File-Fixture", files, root_dir=self.fixtures_dir)
        self.assertIsNotNone(summary.verification_metrics)
        self.assertGreater(len(summary.verification_evidence), 0)
        # At least one hypothesis should be CONFIRMED (from order_service.py)
        confirmed_hyps = [h for h in summary.hypotheses if h.status == BugStatus.CONFIRMED]
        self.assertGreater(len(confirmed_hyps), 0)


if __name__ == "__main__":
    unittest.main()

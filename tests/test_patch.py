import os
import unittest
from pathlib import Path

from reposentinal.hypothesis import BugHypothesis, BugStatus, Confidence
from reposentinal.models import Severity
from reposentinal.verification import VerificationEvidence, VerificationStatus, ExecutionResult
from reposentinal.patch_models import (
    GeneratedPatch,
    PatchVerificationStatus,
    PatchVerificationResult,
)
from reposentinal.patch_safety import PatchSafetyValidator
from reposentinal.patch_workspace import IsolatedPatchWorkspace
from reposentinal.patch_applier import PatchApplier
from reposentinal.patch_generator import DeterministicPatchGenerator
from reposentinal.patch_verifier import PatchVerifier
from reposentinal.sandbox import SafeSubprocessSandbox
from reposentinal.analyzer import RepoSentinelAgent
from reposentinal.providers import MockProvider
from reposentinal.scanner import scan_repository


class TestPatchPipeline(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path(__file__).parent / "fixtures" / "cross_file_repo"
        self.order_file = self.fixtures_dir / "order_service.py"
        self.original_order_code = self.order_file.read_text(encoding="utf-8")

    def tearDown(self):
        # Guarantee original file is never corrupted
        if self.order_file.exists():
            self.order_file.write_text(self.original_order_code, encoding="utf-8")

    def _create_confirmed_null_hypothesis(self) -> Tuple[BugHypothesis, VerificationEvidence]:
        hyp = BugHypothesis(
            hypothesis_id="HYP-P1",
            title="Unchecked Return Assumption from verify_jwt_token",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.CONFIRMED,
            affected_file=str(self.order_file),
            affected_symbol="process_order_checkout",
            line_start=6,
            line_end=8,
            explanation="Assumes verify_jwt_token never returns None",
            reasoning="verify_jwt_token returns None on invalid tokens",
            related_symbols=["auth_service.py:verify_jwt_token"],
            suggested_test="Call with invalid token",
            is_verified=True,
        )
        ev = VerificationEvidence(
            hypothesis_id="HYP-P1",
            test_id="TEST-HYP-P1",
            status=VerificationStatus.REPRODUCED,
            execution=ExecutionResult(
                test_id="TEST-HYP-P1",
                hypothesis_id="HYP-P1",
                exit_code=0,
                stdout="VULNERABILITY_REPRODUCED: TypeError: 'NoneType' object is not subscriptable",
                stderr="",
                duration_seconds=0.1,
                timed_out=False,
                sandbox_backend="safe_subprocess",
            ),
            reproduction_trace="TypeError: 'NoneType' object is not subscriptable",
        )
        return hyp, ev

    def test_deterministic_patch_generation_null_assumption(self):
        gen = DeterministicPatchGenerator()
        hyp, ev = self._create_confirmed_null_hypothesis()

        patch = gen.generate_patch(hyp, self.fixtures_dir, ev)
        self.assertIsNotNone(patch)
        self.assertEqual(patch.hypothesis_id, "HYP-P1")
        self.assertEqual(patch.target_symbol, "process_order_checkout")
        self.assertIn("if user is None:", patch.patched_code)
        self.assertIn("+++", patch.unified_diff)
        self.assertIn("---", patch.unified_diff)
        self.assertEqual(patch.validation_status, "PASSED")

        # Must pass safety validation
        PatchSafetyValidator.validate(patch, self.fixtures_dir)

    def test_patch_safety_validator_rejects_destructive_patterns(self):
        hyp, ev = self._create_confirmed_null_hypothesis()
        dangerous_codes = [
            "import shutil\nshutil.rmtree('/')\n",
            "import os\nos.remove('/etc/passwd')\n",
            "import subprocess\nsubprocess.run('rm -rf /', shell=True)\n",
        ]

        for code in dangerous_codes:
            bad_patch = GeneratedPatch(
                patch_id="PATCH-BAD",
                hypothesis_id=hyp.hypothesis_id,
                target_file=str(self.order_file),
                target_symbol="func",
                bug_category="Security",
                patch_objective="Bad",
                original_code="orig",
                patched_code=code,
                unified_diff="--- a/f\n+++ b/f\n@@ -1 +1 @@\n",
                rationale="Bad",
            )
            with self.assertRaises(ValueError):
                PatchSafetyValidator.validate(bad_patch, self.fixtures_dir)

    def test_patch_safety_validator_rejects_credentials(self):
        hyp, ev = self._create_confirmed_null_hypothesis()
        bad_patch = GeneratedPatch(
            patch_id="PATCH-LEAK",
            hypothesis_id=hyp.hypothesis_id,
            target_file=str(self.order_file),
            target_symbol="func",
            bug_category="Security",
            patch_objective="Leak",
            original_code="orig",
            patched_code="API_KEY = 'sk-1234567890123456789012345'\n",
            unified_diff="--- a/f\n+++ b/f\n@@ -1 +1 @@\n",
            rationale="Leak",
        )
        with self.assertRaises(ValueError):
            PatchSafetyValidator.validate(bad_patch, self.fixtures_dir)

    def test_patch_safety_validator_rejects_syntax_errors(self):
        hyp, ev = self._create_confirmed_null_hypothesis()
        bad_patch = GeneratedPatch(
            patch_id="PATCH-SYNTAX",
            hypothesis_id=hyp.hypothesis_id,
            target_file=str(self.order_file),
            target_symbol="func",
            bug_category="Security",
            patch_objective="Broken syntax",
            original_code="orig",
            patched_code="def broken_syntax(:\n",
            unified_diff="--- a/f\n+++ b/f\n@@ -1 +1 @@\n",
            rationale="Broken",
        )
        with self.assertRaises(ValueError):
            PatchSafetyValidator.validate(bad_patch, self.fixtures_dir)

    def test_patch_safety_validator_rejects_protected_system_paths(self):
        hyp, ev = self._create_confirmed_null_hypothesis()
        bad_patch = GeneratedPatch(
            patch_id="PATCH-PROT",
            hypothesis_id=hyp.hypothesis_id,
            target_file=".github/workflows/ci.yml",
            target_symbol="func",
            bug_category="Security",
            patch_objective="Alter CI",
            original_code="orig",
            patched_code="name: CI\n",
            unified_diff="--- a/f\n+++ b/f\n@@ -1 +1 @@\n",
            rationale="Alter CI",
        )
        with self.assertRaises(ValueError):
            PatchSafetyValidator.validate(bad_patch, self.fixtures_dir)

    def test_isolated_workspace_lifecycle_and_immutability(self):
        """
        Critical Invariant 5: The user's original repository must remain unchanged during verification.
        """
        original_mtime = self.order_file.stat().st_mtime
        original_bytes = self.order_file.read_bytes()

        with IsolatedPatchWorkspace(self.fixtures_dir) as ws:
            self.assertIsNotNone(ws.workspace_dir)
            self.assertTrue(ws.workspace_dir.exists())

            # Read and modify workspace file
            target_rel = "order_service.py"
            content = ws.read_file(target_rel)
            self.assertEqual(content, self.original_order_code)

            ws.apply_file_content(target_rel, "# Patched in isolated workspace\n")
            modified_in_ws = ws.read_file(target_rel)
            self.assertIn("# Patched in isolated workspace", modified_in_ws)

            # Original host file must be completely untouched!
            self.assertEqual(self.order_file.read_bytes(), original_bytes)
            self.assertEqual(self.order_file.stat().st_mtime, original_mtime)

        # After workspace exit, temp dir must be cleaned up
        self.assertFalse(ws.workspace_dir.exists() if ws.workspace_dir else False)

    def test_patch_applier_verifies_clean_syntax(self):
        hyp, ev = self._create_confirmed_null_hypothesis()
        gen = DeterministicPatchGenerator()
        patch = gen.generate_patch(hyp, self.fixtures_dir, ev)

        with IsolatedPatchWorkspace(self.fixtures_dir) as ws:
            success, msg = PatchApplier.apply_patch(patch, ws)
            self.assertTrue(success)
            self.assertEqual(msg, "APPLIED")

            # Check that applied code in workspace contains null check
            applied_code = ws.read_file(patch.target_file)
            self.assertIn("if user is None:", applied_code)

    def test_successful_patch_verification_dual_phase(self):
        """
        Full Dual-Phase Verification:
        Step A: Original vulnerability is no longer reproduced -> Fixed
        Step B: Functional regression tests pass -> Verified
        """
        hyp, ev = self._create_confirmed_null_hypothesis()
        verifier = PatchVerifier(sandbox=SafeSubprocessSandbox())

        patch, result = verifier.verify_patch(hyp, ev, self.fixtures_dir)

        self.assertIsNotNone(patch)
        self.assertEqual(result.status, PatchVerificationStatus.VERIFIED)
        self.assertTrue(result.vulnerability_fixed)
        self.assertTrue(result.regression_passed)
        self.assertIn("SAFE_HANDLING_OBSERVED", result.repro_test_stdout)
        self.assertIn("REGRESSION_TEST_PASSED", result.regression_test_stdout)
        self.assertIn("+++", result.final_diff)

        # Host file must remain untouched
        self.assertEqual(self.order_file.read_text(encoding="utf-8"), self.original_order_code)

    def test_regression_detected_when_patch_breaks_valid_calls(self):
        """
        Regression Protection (Requirement 10):
        If a patch eliminates the crash on invalid input but breaks legitimate functionality,
        the system must flag REGRESSION_DETECTED and refuse to mark it VERIFIED.
        """
        hyp, ev = self._create_confirmed_null_hypothesis()

        # Create a buggy patch that disables valid checkout by returning 401 on all tokens
        regressive_code = """from auth_service import verify_jwt_token
from db_gateway import DatabaseGateway

def process_order_checkout(token: str, order_id: str, amount: float):
    # Regression: incorrectly rejects legitimate valid tokens as unauthorized
    return {"error": "Unauthorized: service temporarily disabled", "status": 401}
"""
        regressive_diff = "--- a/order_service.py\n+++ b/order_service.py\n@@ -1,5 +1,5 @@\n"

        regressive_patch = GeneratedPatch(
            patch_id="PATCH-REGRESSIVE",
            hypothesis_id=hyp.hypothesis_id,
            target_file=str(self.order_file),
            target_symbol="process_order_checkout",
            bug_category=hyp.category,
            patch_objective="Regressive dummy patch",
            original_code=self.original_order_code,
            patched_code=regressive_code,
            unified_diff=regressive_diff,
            rationale="Testing regression detection",
            validation_status="PASSED",
        )

        class FakeRegressiveGenerator:
            def generate_patch(self, h, root, ev):
                return regressive_patch

        verifier = PatchVerifier(
            sandbox=SafeSubprocessSandbox(),
            patch_generator=FakeRegressiveGenerator(),
        )

        patch, result = verifier.verify_patch(hyp, ev, self.fixtures_dir)

        # Vulnerability fixed (does not crash on None), BUT regression detected!
        self.assertTrue(result.vulnerability_fixed)
        self.assertFalse(result.regression_passed)
        self.assertEqual(result.status, PatchVerificationStatus.REGRESSION_DETECTED)
        self.assertIn("REGRESSION_FAILURE", result.regression_test_stdout)

    def test_verification_failed_when_vulnerability_still_reproduces(self):
        """
        If candidate patch does not fix the underlying vulnerability,
        verification must fail with VERIFICATION_FAILED.
        """
        hyp, ev = self._create_confirmed_null_hypothesis()

        # Ineffective patch that only adds a comment without adding a null check
        ineffective_code = self.original_order_code.replace(
            "user = verify_jwt_token(token)",
            "user = verify_jwt_token(token) # Added comment but no guard",
        )
        ineffective_diff = "--- a/order_service.py\n+++ b/order_service.py\n@@ -6 +6 @@\n"

        ineffective_patch = GeneratedPatch(
            patch_id="PATCH-INEFFECTIVE",
            hypothesis_id=hyp.hypothesis_id,
            target_file=str(self.order_file),
            target_symbol="process_order_checkout",
            bug_category=hyp.category,
            patch_objective="Ineffective dummy patch",
            original_code=self.original_order_code,
            patched_code=ineffective_code,
            unified_diff=ineffective_diff,
            rationale="Testing verification failure",
            validation_status="PASSED",
        )

        class FakeIneffectiveGenerator:
            def generate_patch(self, h, root, ev):
                return ineffective_patch

        verifier = PatchVerifier(
            sandbox=SafeSubprocessSandbox(),
            patch_generator=FakeIneffectiveGenerator(),
        )

        patch, result = verifier.verify_patch(hyp, ev, self.fixtures_dir)

        self.assertFalse(result.vulnerability_fixed)
        self.assertEqual(result.status, PatchVerificationStatus.VERIFICATION_FAILED)

    def test_invariant_unconfirmed_hypothesis_rejected_for_patching(self):
        """
        Critical Invariant: Only confirmed/reproduced bugs can receive candidate patches.
        """
        hyp = BugHypothesis(
            hypothesis_id="HYP-UNCONFIRMED",
            title="Unconfirmed Theory",
            category="Security",
            severity=Severity.MEDIUM,
            confidence=Confidence.LOW,
            status=BugStatus.POTENTIAL,  # Unconfirmed
            affected_file=str(self.order_file),
            line_start=1,
            line_end=5,
            explanation="Unconfirmed",
            reasoning="Theory",
            suggested_test="Test",
        )
        ev = VerificationEvidence(
            hypothesis_id="HYP-UNCONFIRMED",
            test_id="TEST-1",
            status=VerificationStatus.UNVERIFIED,
            execution=ExecutionResult(
                test_id="TEST-1",
                hypothesis_id="HYP-UNCONFIRMED",
                exit_code=-1,
                stdout="",
                stderr="",
                duration_seconds=0,
                timed_out=False,
                sandbox_backend="safe_subprocess",
            ),
        )

        verifier = PatchVerifier(sandbox=SafeSubprocessSandbox())
        patch, result = verifier.verify_patch(hyp, ev, self.fixtures_dir)

        self.assertIsNone(patch)
        self.assertEqual(result.status, PatchVerificationStatus.INCONCLUSIVE)

    def test_end_to_end_agent_with_patching(self):
        files = scan_repository(self.fixtures_dir)
        agent = RepoSentinelAgent(
            provider=MockProvider(),
            verify=True,
            patch=True,
            target_root_dir=self.fixtures_dir,
        )

        summary = agent.analyze("Cross-File-Fixture", files, root_dir=self.fixtures_dir)

        self.assertIsNotNone(summary.verification_metrics)
        self.assertIsNotNone(summary.patch_metrics)
        self.assertGreater(len(summary.patches), 0)
        self.assertGreater(len(summary.patch_results), 0)

        verified_patches = [r for r in summary.patch_results if r.status == PatchVerificationStatus.VERIFIED]
        self.assertGreater(len(verified_patches), 0)

        # Host repository files must be 100% unchanged
        self.assertEqual(self.order_file.read_text(encoding="utf-8"), self.original_order_code)


if __name__ == "__main__":
    unittest.main()

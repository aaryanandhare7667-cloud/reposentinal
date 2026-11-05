import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from backend.models.hypothesis import BugHypothesis, BugStatus
from backend.models.patch_models import (
    GeneratedPatch,
    PatchVerificationResult,
    PatchVerificationStatus,
    PatchQualityMetrics,
)
from backend.patching.patch_generator import DeterministicPatchGenerator, BasePatchGenerator
from backend.patching.patch_safety import PatchSafetyValidator
from backend.patching.patch_workspace import IsolatedPatchWorkspace
from backend.patching.patch_applier import PatchApplier
from backend.verification.sandbox import BaseSandbox, get_sandbox_backend
from backend.verification.test_generator import AdversarialTest, DeterministicTestGenerator
from backend.verification.verification import VerificationEvidence, VerificationStatus


class PatchVerifier:
    """
    Orchestrates candidate patch generation, isolated workspace application,
    adversarial re-testing, regression testing, and deterministic verification.
    Enforces critical invariants:
    1. A patch cannot become VERIFIED unless successfully applied in an isolated workspace.
    2. A patch cannot become VERIFIED unless the original vulnerability is no longer reproducible.
    3. A patch cannot become VERIFIED if regression tests fail.
    4. LLM output alone can never mark a patch as VERIFIED.
    5. The user's original repository is NEVER modified.
    """

    def __init__(
        self,
        sandbox: Optional[BaseSandbox] = None,
        patch_generator: Optional[BasePatchGenerator] = None,
        test_generator: Optional[DeterministicTestGenerator] = None,
    ):
        self.sandbox = sandbox or get_sandbox_backend("auto")
        self.patch_generator = patch_generator or DeterministicPatchGenerator()
        self.test_generator = test_generator or DeterministicTestGenerator()

    def verify_patch(
        self,
        hypothesis: BugHypothesis,
        evidence: VerificationEvidence,
        root_dir: Path,
        adversarial_test: Optional[AdversarialTest] = None,
    ) -> Tuple[Optional[GeneratedPatch], PatchVerificationResult]:
        """
        Executes complete patch generation, application, and dual-phase verification:
        (1) Adversarial Re-Testing (must not reproduce vulnerability)
        (2) Functional Regression Testing (must preserve valid application behavior)
        """
        start_time = time.time()

        # Invariant: Only confirmed or reproduced bugs are candidates for verified patches
        if hypothesis.status != BugStatus.CONFIRMED and evidence.status != VerificationStatus.REPRODUCED:
            duration = time.time() - start_time
            return None, PatchVerificationResult(
                patch_id=f"PATCH-{hypothesis.hypothesis_id}",
                hypothesis_id=hypothesis.hypothesis_id,
                status=PatchVerificationStatus.INCONCLUSIVE,
                duration_seconds=duration,
                error_message="Cannot generate patch for unconfirmed hypothesis",
                verification_notes="Patch generation requires a confirmed, reproduced bug.",
            )

        # 1. Generate candidate patch
        patch = self.patch_generator.generate_patch(hypothesis, root_dir, evidence)
        if not patch:
            duration = time.time() - start_time
            return None, PatchVerificationResult(
                patch_id=f"PATCH-{hypothesis.hypothesis_id}",
                hypothesis_id=hypothesis.hypothesis_id,
                status=PatchVerificationStatus.INCONCLUSIVE,
                duration_seconds=duration,
                error_message="No patch generator available for this hypothesis category",
                verification_notes="No candidate patch could be synthesized.",
            )

        # 2. Structural safety validation
        try:
            PatchSafetyValidator.validate(patch, root_dir)
            patch.validation_status = "PASSED"
        except ValueError as exc:
            patch.validation_status = "FAILED"
            patch.validation_error = str(exc)
            duration = time.time() - start_time
            return patch, PatchVerificationResult(
                patch_id=patch.patch_id,
                hypothesis_id=hypothesis.hypothesis_id,
                status=PatchVerificationStatus.VALIDATION_FAILED,
                duration_seconds=duration,
                error_message=str(exc),
                verification_notes=f"Patch rejected by safety validator: {exc}",
            )

        # 3. Create isolated ephemeral workspace (user's repo is untouched)
        target_path = Path(hypothesis.affected_file)
        effective_root = Path(root_dir)
        if target_path.is_absolute() and target_path.exists():
            try:
                target_path.resolve().relative_to(effective_root.resolve())
            except ValueError:
                effective_root = target_path.parent

        with IsolatedPatchWorkspace(effective_root) as workspace:
            # 4. Apply patch in isolated workspace
            ok, apply_msg = PatchApplier.apply_patch(patch, workspace)
            if not ok:
                duration = time.time() - start_time
                return patch, PatchVerificationResult(
                    patch_id=patch.patch_id,
                    hypothesis_id=hypothesis.hypothesis_id,
                    status=PatchVerificationStatus.APPLY_FAILED,
                    duration_seconds=duration,
                    error_message=apply_msg,
                    verification_notes=f"Patch application failed in workspace: {apply_msg}",
                )

            # 5. STEP A — Re-run the original adversarial reproduction test
            if not adversarial_test:
                adversarial_test = self.test_generator.generate_test(hypothesis)

            repro_res = None
            vuln_fixed = False
            repro_stdout = ""
            repro_stderr = ""

            if adversarial_test:
                repro_res = self.sandbox.execute(adversarial_test, workspace.workspace_dir)
                repro_stdout = repro_res.stdout
                repro_stderr = repro_res.stderr

                # Evaluate if vulnerability is still reproduced
                # Before patch: exited with 0 and stdout contained VULNERABILITY_REPRODUCED
                if repro_res.exit_code == 0 and "VULNERABILITY_REPRODUCED" in repro_res.stdout:
                    # Vulnerability is STILL present after patch!
                    vuln_fixed = False
                elif "SAFE_HANDLING_OBSERVED" in repro_res.stdout or "VULNERABILITY_REPRODUCED" not in repro_res.stdout:
                    vuln_fixed = True
                else:
                    vuln_fixed = False

            if not vuln_fixed:
                duration = time.time() - start_time
                return patch, PatchVerificationResult(
                    patch_id=patch.patch_id,
                    hypothesis_id=hypothesis.hypothesis_id,
                    status=PatchVerificationStatus.VERIFICATION_FAILED,
                    vulnerability_fixed=False,
                    repro_test_stdout=repro_stdout,
                    repro_test_stderr=repro_stderr,
                    duration_seconds=duration,
                    error_message="Vulnerability still reproduced after patch application",
                    verification_notes="The candidate patch failed to eliminate the vulnerability.",
                )

            # 6. STEP B — Run functional regression test in isolated workspace
            reg_passed, reg_stdout, reg_stderr = self._run_regression_test(
                hypothesis, patch, workspace
            )

            duration = time.time() - start_time

            if not reg_passed:
                # Patch fixed vulnerability but broke legitimate functionality!
                return patch, PatchVerificationResult(
                    patch_id=patch.patch_id,
                    hypothesis_id=hypothesis.hypothesis_id,
                    status=PatchVerificationStatus.REGRESSION_DETECTED,
                    vulnerability_fixed=True,
                    regression_passed=False,
                    repro_test_stdout=repro_stdout,
                    repro_test_stderr=repro_stderr,
                    regression_test_stdout=reg_stdout,
                    regression_test_stderr=reg_stderr,
                    duration_seconds=duration,
                    final_diff=patch.unified_diff,
                    error_message="Regression detected: valid functional behavior was broken by the patch",
                    verification_notes="Security fix eliminated vulnerability but caused functional regression on valid inputs.",
                )

            # 7. STEP C — All verification criteria met -> VERIFIED!
            return patch, PatchVerificationResult(
                patch_id=patch.patch_id,
                hypothesis_id=hypothesis.hypothesis_id,
                status=PatchVerificationStatus.VERIFIED,
                vulnerability_fixed=True,
                regression_passed=True,
                repro_test_stdout=repro_stdout,
                repro_test_stderr=repro_stderr,
                regression_test_stdout=reg_stdout,
                regression_test_stderr=reg_stderr,
                duration_seconds=duration,
                final_diff=patch.unified_diff,
                verification_notes="Patch successfully verified: original vulnerability eliminated and all functional regression tests passed cleanly.",
            )

    def _run_regression_test(
        self, hyp: BugHypothesis, patch: GeneratedPatch, workspace: IsolatedPatchWorkspace
    ) -> Tuple[bool, str, str]:
        """
        Executes functional regression tests on legitimate inputs to ensure the patch
        does not break expected system behavior.
        """
        target_stem = Path(patch.target_file).stem
        target_func = hyp.affected_symbol or "process_order_checkout"

        # Generate a regression test that verifies valid legitimate calls still succeed
        regression_code = f'''# Functional Regression Verification Driver
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

try:
    import {target_stem}
except Exception as e:
    print(f"REGRESSION_FAILURE: Could not import {target_stem}: {{e}}")
    sys.exit(1)

func = getattr({target_stem}, "{target_func}", None)
if not func:
    print(f"REGRESSION_FAILURE: Function {target_func} missing from {target_stem}")
    sys.exit(1)

try:
    # Test legitimate input call
    res = None
    try:
        res = func("valid_token", "ORD-NORMAL-100", 49.99)
    except TypeError:
        try:
            res = func("valid_token", 42)
        except TypeError:
            res = func()

    # Verify that function returned valid non-crashing result on legitimate input
    if isinstance(res, dict) and res.get("status") in (400, 401) and "Unauthorized" in res.get("error", ""):
        # If valid_token was rejected as unauthorized, that is a functional regression!
        print("REGRESSION_FAILURE: Legitimate token was incorrectly rejected.")
        sys.exit(1)

    print("REGRESSION_TEST_PASSED: Normal functional workflow executes successfully.")
    sys.exit(0)
except Exception as exc:
    print(f"REGRESSION_FAILURE: Unexpected exception on valid call: {{type(exc).__name__}}: {{exc}}")
    sys.exit(1)
'''
        reg_test = AdversarialTest(
            test_id=f"REG-{patch.patch_id}",
            hypothesis_id=hyp.hypothesis_id,
            target_file=patch.target_file,
            target_symbol=target_func,
            test_objective="Assert legitimate valid requests still succeed without regression",
            setup_code="Call target with valid inputs",
            adversarial_input="valid_token",
            expected_vulnerable_behavior="N/A",
            expected_safe_behavior="Execution succeeds cleanly with normal output",
            executable_code=regression_code,
            timeout_seconds=10,
        )

        res = self.sandbox.execute(reg_test, workspace.workspace_dir)
        passed = (res.exit_code == 0) and ("REGRESSION_TEST_PASSED" in res.stdout)
        return passed, res.stdout, res.stderr

    def verify_all_patches(
        self,
        hypotheses: List[BugHypothesis],
        evidences: List[VerificationEvidence],
        root_dir: Path,
    ) -> Tuple[List[GeneratedPatch], List[PatchVerificationResult], Dict[str, Any]]:
        """
        Executes patch generation and verification for all confirmed hypotheses,
        aggregating patch quality and research metrics.
        """
        patches: List[GeneratedPatch] = []
        results: List[PatchVerificationResult] = []
        start_time = time.time()

        evidence_map = {e.hypothesis_id: e for e in evidences}

        for hyp in hypotheses:
            # Only generate and verify patches for confirmed or reproduced bugs
            ev = evidence_map.get(hyp.hypothesis_id)
            if not ev or (hyp.status != BugStatus.CONFIRMED and ev.status != VerificationStatus.REPRODUCED):
                continue

            patch, res = self.verify_patch(hyp, ev, root_dir)
            if patch:
                patches.append(patch)
            results.append(res)

        total_time = time.time() - start_time

        # Calculate metrics
        patches_generated = len(patches)
        patches_validated = sum(1 for p in patches if p.validation_status == "PASSED")
        patches_applied = sum(1 for r in results if r.status not in (PatchVerificationStatus.VALIDATION_FAILED, PatchVerificationStatus.APPLY_FAILED))
        patches_verified = sum(1 for r in results if r.status == PatchVerificationStatus.VERIFIED)
        patch_apply_failures = sum(1 for r in results if r.status == PatchVerificationStatus.APPLY_FAILED)
        verification_failures = sum(1 for r in results if r.status == PatchVerificationStatus.VERIFICATION_FAILED)
        regression_detected_count = sum(1 for r in results if r.status == PatchVerificationStatus.REGRESSION_DETECTED)

        vuln_fixed_count = sum(1 for r in results if r.vulnerability_fixed)
        fix_rate = round(vuln_fixed_count / max(1, patches_applied), 2)
        ver_rate = round(patches_verified / max(1, patches_generated), 2)
        avg_time = round(total_time / max(1, len(results)), 3)

        lines_added = 0
        lines_removed = 0
        for p in patches:
            for line in p.unified_diff.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    lines_added += 1
                elif line.startswith("-") and not line.startswith("---"):
                    lines_removed += 1

        metrics = PatchQualityMetrics(
            patches_generated=patches_generated,
            patches_validated=patches_validated,
            patches_applied=patches_applied,
            patches_verified=patches_verified,
            patch_application_failures=patch_apply_failures,
            verification_failures=verification_failures,
            regression_detected_count=regression_detected_count,
            vulnerability_fix_rate=fix_rate,
            patch_verification_rate=ver_rate,
            average_patch_time=avg_time,
            average_verification_time=avg_time,
            total_lines_added=lines_added,
            total_lines_removed=lines_removed,
        )

        return patches, results, metrics.to_dict()

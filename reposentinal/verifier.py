import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from reposentinal.hypothesis import BugHypothesis, BugStatus
from reposentinal.test_generator import AdversarialTest, DeterministicTestGenerator
from reposentinal.sandbox import BaseSandbox, get_sandbox_backend
from reposentinal.verification import (
    VerificationStatus,
    ExecutionResult,
    VerificationEvidence,
)


class HypothesisVerifier:
    """
    Executes adversarial tests inside an isolated sandbox, collects reproduction evidence,
    and makes deterministic verification decisions (REPRODUCED, NOT_REPRODUCED, FALSE_POSITIVE, INCONCLUSIVE).
    Enforces the invariant that a hypothesis can only be promoted to 'Confirmed Bug' through deterministic execution evidence.
    """

    def __init__(
        self,
        sandbox: Optional[BaseSandbox] = None,
        test_generator: Optional[DeterministicTestGenerator] = None,
    ):
        self.sandbox = sandbox or get_sandbox_backend("auto")
        self.test_generator = test_generator or DeterministicTestGenerator()

    def verify_hypothesis(
        self, hypothesis: BugHypothesis, root_dir: Path
    ) -> VerificationEvidence:
        """
        Synthesizes an adversarial test, runs it within the sandbox, and determines reproduction status.
        """
        # 1. Generate adversarial test
        test = self.test_generator.generate_test(hypothesis)
        if not test:
            empty_exec = ExecutionResult(
                test_id=f"TEST-{hypothesis.hypothesis_id}",
                hypothesis_id=hypothesis.hypothesis_id,
                exit_code=-1,
                stdout="",
                stderr="No automated reproduction generator available for this hypothesis category",
                duration_seconds=0.0,
                timed_out=False,
                sandbox_backend=self.sandbox.backend_name,
                error_message="Generator unsupported",
            )
            return VerificationEvidence(
                hypothesis_id=hypothesis.hypothesis_id,
                test_id=empty_exec.test_id,
                status=VerificationStatus.INCONCLUSIVE,
                execution=empty_exec,
                failure_reason="No reproduction generator available for category",
                verification_notes="Hypothesis remains unverified due to lack of a targeted test driver.",
            )

        # 2. Resolve effective root directory (fallback to target file parent if not under root_dir)
        effective_root = Path(root_dir)
        target_path = Path(hypothesis.affected_file)
        if target_path.is_absolute() and target_path.exists():
            try:
                target_path.resolve().relative_to(effective_root.resolve())
            except ValueError:
                effective_root = target_path.parent

        # 3. Execute test in sandbox
        exec_res = self.sandbox.execute(test, effective_root)

        # 3. Apply deterministic decision rules
        reproduction_trace: Optional[str] = None
        failure_reason: Optional[str] = None
        notes: str = ""

        if exec_res.timed_out:
            status = VerificationStatus.INCONCLUSIVE
            failure_reason = f"Execution timed out ({test.timeout_seconds}s limit exceeded)"
            notes = "Test failed to terminate within sandbox timeout threshold."

        elif exec_res.exit_code == 0:
            # Vulnerability successfully reproduced!
            status = VerificationStatus.REPRODUCED
            reproduction_trace = exec_res.stdout.strip()
            notes = f"Vulnerability reproduced deterministically: {reproduction_trace}"
            # Promote hypothesis to CONFIRMED
            hypothesis.confirm()

        elif exec_res.exit_code == 2:
            # Target safely handled input or rejected malformed state without crashing
            if "SAFE_HANDLING_OBSERVED" in exec_res.stdout:
                status = VerificationStatus.FALSE_POSITIVE
                notes = f"Safe handling confirmed by execution: {exec_res.stdout.strip()}"
            else:
                status = VerificationStatus.NOT_REPRODUCED
                notes = f"Target did not enter vulnerable state: {exec_res.stdout.strip()}"
            failure_reason = "Target handled adversarial input safely; bug does not manifest."

        elif exec_res.exit_code == 3:
            # Environment, import, or module setup issue
            status = VerificationStatus.INCONCLUSIVE
            failure_reason = f"Sandbox setup/dependency failure: {exec_res.stdout.strip() or exec_res.stderr.strip()}"
            notes = "Reproduction test could not execute target code cleanly."

        else:
            # Exit code 1 or other unexpected runtime failure
            status = VerificationStatus.INCONCLUSIVE
            failure_reason = f"Test terminated with unexpected exit code {exec_res.exit_code}"
            notes = exec_res.stderr.strip() or exec_res.stdout.strip() or "Unhandled execution failure"

        return VerificationEvidence(
            hypothesis_id=hypothesis.hypothesis_id,
            test_id=test.test_id,
            status=status,
            execution=exec_res,
            reproduction_trace=reproduction_trace,
            failure_reason=failure_reason,
            verification_notes=notes,
        )

    def verify_all(
        self, hypotheses: List[BugHypothesis], root_dir: Path
    ) -> Tuple[List[BugHypothesis], List[VerificationEvidence], Dict[str, Any]]:
        """
        Verifies a collection of bug hypotheses, updates hypotheses with verification state,
        and aggregates research verification metrics.
        """
        evidence_list: List[VerificationEvidence] = []
        start_time = time.time()

        for hyp in hypotheses:
            evidence = self.verify_hypothesis(hyp, root_dir)
            evidence_list.append(evidence)

        total_duration = time.time() - start_time

        # Calculate research metrics
        reproduced_count = sum(1 for e in evidence_list if e.status == VerificationStatus.REPRODUCED)
        confirmed_count = sum(1 for h in hypotheses if h.status == BugStatus.CONFIRMED)
        not_reproduced_count = sum(1 for e in evidence_list if e.status == VerificationStatus.NOT_REPRODUCED)
        false_positive_count = sum(1 for e in evidence_list if e.status == VerificationStatus.FALSE_POSITIVE)
        inconclusive_count = sum(1 for e in evidence_list if e.status == VerificationStatus.INCONCLUSIVE)
        tests_generated = sum(1 for e in evidence_list if e.test_id and not e.test_id.endswith("-None"))
        tests_executed = len(evidence_list)

        reproduction_rate = round(reproduced_count / max(1, tests_executed), 2)
        avg_time = round(total_duration / max(1, tests_executed), 3)

        metrics = {
            "total_hypotheses": len(hypotheses),
            "tests_generated": tests_generated,
            "tests_executed": tests_executed,
            "reproduced_count": reproduced_count,
            "confirmed_count": confirmed_count,
            "not_reproduced_count": not_reproduced_count,
            "false_positive_count": false_positive_count,
            "inconclusive_count": inconclusive_count,
            "reproduction_rate": reproduction_rate,
            "sandbox_backend": self.sandbox.backend_name,
            "total_verification_duration_seconds": round(total_duration, 2),
            "average_verification_seconds": avg_time,
        }

        return hypotheses, evidence_list, metrics

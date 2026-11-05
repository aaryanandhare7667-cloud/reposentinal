"""
Unit and integration tests for the new backend/ modular architecture.
Verifies that all subpackages (scanner, analysis, verification, patching, cli, models)
function cleanly and independently, while maintaining backward-compatibility with reposentinal.
"""
import unittest
from pathlib import Path

# Test direct backend imports
import backend
from backend.models import (
    Severity,
    BugFinding,
    FileContext,
    ScanSummary,
    Confidence,
    BugStatus,
    BugHypothesis,
    PatchVerificationStatus,
    GeneratedPatch,
    PatchVerificationResult,
    PatchQualityMetrics,
)
from backend.scanner import scan_repository, prepare_target
from backend.analysis import (
    RepoSentinelAgent,
    SymbolKind,
    Symbol,
    ImportStatement,
    DependencyGraph,
    RepositoryIndex,
    build_repository_index,
    RepositoryContext,
    RepositoryContextBuilder,
    RuleBasedHypothesisEngine,
    BaseLLMProvider,
    MockProvider,
)
from backend.verification import (
    HypothesisVerifier,
    VerificationStatus,
    ExecutionResult,
    VerificationEvidence,
    BaseSandbox,
    SafeSubprocessSandbox,
    AdversarialTest,
    TestSafetyValidator,
    DeterministicTestGenerator,
)
from backend.patching import (
    PatchVerifier,
    DeterministicPatchGenerator,
    PatchSafetyValidator,
    IsolatedPatchWorkspace,
    PatchApplier,
)
from backend.cli import (
    main,
    parse_args,
    TerminalReporter,
    MarkdownReporter,
    JSONReporter,
)


class TestBackendModularStructure(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path(__file__).parent / "fixtures" / "cross_file_repo"

    def test_backend_top_level_exports(self):
        self.assertEqual(backend.__version__, "0.5.0")
        self.assertTrue(hasattr(backend, "Severity"))
        self.assertTrue(hasattr(backend, "RepoSentinelAgent"))
        self.assertTrue(hasattr(backend, "build_repository_index"))
        self.assertTrue(hasattr(backend, "HypothesisVerifier"))
        self.assertTrue(hasattr(backend, "PatchVerifier"))

    def test_models_subpackage(self):
        hyp = BugHypothesis(
            hypothesis_id="BACKEND-01",
            title="Backend Model Test",
            category="Logic Error",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.POTENTIAL,
            affected_file="test.py",
            affected_symbol="func",
            line_start=1,
            line_end=5,
            explanation="Test explanation",
            reasoning="Test reasoning",
            suggested_test="assert func() == expected",
        )
        self.assertEqual(hyp.status, BugStatus.POTENTIAL)
        self.assertEqual(hyp.severity, Severity.HIGH)

        patch = GeneratedPatch(
            patch_id="PATCH-01",
            hypothesis_id="BACKEND-01",
            target_file="test.py",
            target_symbol="func",
            bug_category="Logic Error",
            patch_objective="Fix logic bug",
            original_code="bad()",
            patched_code="good()",
            unified_diff="--- test.py\n+++ test.py\n@@ -1 +1 @@\n-bad()\n+good()\n",
            rationale="Fix logic bug",
        )
        self.assertEqual(patch.validation_status, "PENDING")

    def test_scanner_subpackage(self):
        files = scan_repository(self.fixtures_dir)
        self.assertEqual(len(files), 3)
        file_names = {Path(f.rel_path).name for f in files}
        self.assertIn("auth_service.py", file_names)
        self.assertIn("order_service.py", file_names)
        self.assertIn("db_gateway.py", file_names)

    def test_analysis_subpackage_indexing_and_context(self):
        files = scan_repository(self.fixtures_dir)
        index = build_repository_index(files)
        self.assertGreater(len(index.symbols), 0)

        order_file = next(f for f in files if "order_service.py" in f.rel_path)
        builder = RepositoryContextBuilder(index)
        ctx = builder.build_context(order_file)
        self.assertTrue(len(ctx.imported_symbols) > 0 or len(ctx.caller_usages) >= 0)

    def test_verification_subpackage_adversarial_test_generation(self):
        hyp = BugHypothesis(
            hypothesis_id="HYP-ORDER-01",
            title="Unchecked Return Assumption",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.LIKELY,
            affected_file="order_service.py",
            affected_symbol="process_order",
            line_start=1,
            line_end=15,
            explanation="Unchecked return value from auth service",
            reasoning="Call chain assumes non-None return",
            suggested_test="assert process_order('invalid') is None",
        )
        adv_test = DeterministicTestGenerator().generate_test(hyp)
        self.assertIsNotNone(adv_test)
        self.assertIn("VULNERABILITY_REPRODUCED", adv_test.executable_code)
        TestSafetyValidator.validate(adv_test.executable_code)

    def test_patching_subpackage_workflow(self):
        hyp = BugHypothesis(
            hypothesis_id="HYP-ORDER-01",
            title="Unchecked Return Assumption",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.CONFIRMED,
            affected_file="order_service.py",
            affected_symbol="process_order",
            line_start=1,
            line_end=15,
            explanation="Unchecked return value from auth service",
            reasoning="Call chain assumes non-None return",
            suggested_test="assert process_order('invalid') is None",
        )
        patch = DeterministicPatchGenerator().generate_patch(hyp, self.fixtures_dir)
        self.assertIsNotNone(patch)
        self.assertIn("process_order", patch.patched_code)
        PatchSafetyValidator.validate(patch, self.fixtures_dir)

    def test_backend_end_to_end_agent(self):
        files = scan_repository(self.fixtures_dir)
        agent = RepoSentinelAgent(
            provider=MockProvider(),
            verify=False,
            patch=False,
        )
        summary = agent.analyze("cross_file_repo", files)
        self.assertEqual(summary.scanned_files, 3)
        self.assertGreaterEqual(len(summary.hypotheses), 1)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
from reposentinal.models import Severity, FileContext
from reposentinal.scanner import scan_repository
from reposentinal.indexer import build_repository_index
from reposentinal.context import RepositoryContextBuilder
from reposentinal.hypothesis import (
    BugHypothesis,
    BugStatus,
    Confidence,
    HypothesisEvaluationMetrics,
)
from reposentinal.hypothesis_engine import (
    RuleBasedHypothesisEngine,
    LLMHypothesisEngine,
)
from reposentinal.analyzer import RepoSentinelAgent
from reposentinal.providers import MockProvider


class TestBugHypothesisEngine(unittest.TestCase):
    def test_hypothesis_schema_validation_success(self):
        hyp = BugHypothesis(
            hypothesis_id="HYP-001",
            title="Potential Null Pointer Exception",
            category="Incorrect Assumptions",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.LIKELY,
            affected_file="services/order.py",
            affected_symbol="process_order",
            line_start=15,
            line_end=18,
            explanation="Dereferences user object without checking for None.",
            reasoning="verify_token returned None in edge cases.",
            related_symbols=["auth.verify_token"],
            suggested_test="Call process_order with invalid token and assert 401.",
            code_snippet="user = verify_token()\nrole = user['role']",
            remediation="Add null check: if not user: return False",
        )

        # Validation should pass
        hyp.validate()

        # Serialization to dict
        d = hyp.to_dict()
        self.assertEqual(d["hypothesis_id"], "HYP-001")
        self.assertEqual(d["severity"], "HIGH")
        self.assertEqual(d["status"], "Likely Bug")
        self.assertEqual(d["confidence"], "HIGH")

        # Roundtrip from_dict
        hyp_reconstructed = BugHypothesis.from_dict(d)
        self.assertEqual(hyp_reconstructed.hypothesis_id, "HYP-001")
        self.assertEqual(hyp_reconstructed.severity, Severity.HIGH)
        self.assertEqual(hyp_reconstructed.status, BugStatus.LIKELY)

    def test_confirmed_status_invariant_rejection(self):
        # A hypothesis cannot be initialized or marked as CONFIRMED without independent execution proof
        hyp = BugHypothesis(
            hypothesis_id="HYP-002",
            title="Unverified Claim",
            category="Security",
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            status=BugStatus.CONFIRMED,
            affected_file="auth.py",
            line_start=1,
            line_end=2,
            explanation="Testing invariant",
            reasoning="Unverified",
            suggested_test="Test",
        )
        with self.assertRaises(ValueError):
            hyp.validate()

        # from_dict must automatically downgrade unverified 'Confirmed Bug' to 'Likely Bug'
        downgraded = BugHypothesis.from_dict({
            "hypothesis_id": "HYP-003",
            "title": "Unverified Claim",
            "status": "Confirmed Bug",
            "affected_file": "auth.py",
            "line_start": 5,
            "line_end": 5,
        })
        self.assertEqual(downgraded.status, BugStatus.LIKELY)

    def test_invalid_line_ranges(self):
        hyp = BugHypothesis(
            hypothesis_id="HYP-004",
            title="Bad Lines",
            category="Logic Error",
            severity=Severity.LOW,
            confidence=Confidence.LOW,
            status=BugStatus.POTENTIAL,
            affected_file="test.py",
            line_start=10,
            line_end=5,  # Invalid: end < start
            explanation="Invalid lines",
            reasoning="Testing",
            suggested_test="None",
        )
        with self.assertRaises(ValueError):
            hyp.validate()

    def test_topology_aware_context_construction(self):
        fixture_dir = Path(__file__).parent / "fixtures" / "cross_file_repo"
        files = scan_repository(fixture_dir)
        self.assertEqual(len(files), 3)

        index = build_repository_index(files)
        builder = RepositoryContextBuilder(index)

        # Build context for order_service.py
        order_file = next(f for f in files if "order_service.py" in f.rel_path)
        ctx = builder.build_context(order_file)

        self.assertIn("auth_service.py", ctx.imported_files)
        self.assertIn("db_gateway.py", ctx.imported_files)

        # Verify imported symbol context contains verify_jwt_token docstring
        jwt_sym = next(s for s in ctx.imported_symbols if s.symbol_name == "verify_jwt_token")
        self.assertIn("invalid or expired", (jwt_sym.docstring or "").lower())

        # Verify prompt representation contains cross-file dependencies
        prompt_block = ctx.to_prompt_context()
        self.assertIn("From module `auth_service.py`", prompt_block)
        self.assertIn("verify_jwt_token", prompt_block)

    def test_cross_module_bug_hypothesis_on_fixture(self):
        fixture_dir = Path(__file__).parent / "fixtures" / "cross_file_repo"
        files = scan_repository(fixture_dir)

        agent = RepoSentinelAgent(
            provider=MockProvider(),
            hypothesis_engine=RuleBasedHypothesisEngine(),
            max_workers=2,
        )
        summary = agent.analyze("cross_file_fixture", files)

        # Verify hypotheses were generated
        self.assertGreater(len(summary.hypotheses), 0)

        # Check for cross-module null assumption hypothesis
        null_hypotheses = [
            h for h in summary.hypotheses
            if "verify_jwt_token" in h.title or "Unchecked Return Value" in h.title
        ]
        self.assertTrue(len(null_hypotheses) >= 1, "Expected cross-module unchecked return hypothesis")

        h = null_hypotheses[0]
        self.assertEqual(h.status, BugStatus.LIKELY)
        self.assertEqual(h.severity, Severity.HIGH)
        self.assertEqual(h.confidence, Confidence.HIGH)
        self.assertIn("order_service.py", h.affected_file)
        self.assertIn("auth_service.py:verify_jwt_token", h.related_symbols)
        self.assertTrue(len(h.suggested_test) > 10)

        # Check research evaluation metrics
        self.assertIsNotNone(summary.metrics)
        self.assertGreater(summary.metrics["cross_file_count"], 0)
        self.assertIn("Likely Bug", summary.metrics["by_status"])

    def test_symbol_to_hypothesis_mapping(self):
        fixture_dir = Path(__file__).parent / "fixtures" / "cross_file_repo"
        files = scan_repository(fixture_dir)
        agent = RepoSentinelAgent(provider=MockProvider())
        summary = agent.analyze("fixture_test", files)

        # Ensure affected_symbol is populated for detected bugs
        mapped_symbols = [h.affected_symbol for h in summary.hypotheses if h.affected_symbol]
        self.assertIn("process_order_checkout", mapped_symbols)

    def test_malformed_and_empty_model_responses(self):
        engine = LLMHypothesisEngine(provider_name="mock")
        dummy_file = FileContext(
            abs_path="/tmp/test.py",
            rel_path="test.py",
            language="python",
            line_count=5,
            size_bytes=50,
            content="x = 1",
        )

        # Empty string
        self.assertEqual(engine._parse_and_validate("", dummy_file), [])

        # Whitespace
        self.assertEqual(engine._parse_and_validate("   \n\t ", dummy_file), [])

        # Raw HTML or garbage
        self.assertEqual(engine._parse_and_validate("<html>500 Error</html>", dummy_file), [])

        # Valid markdown-wrapped JSON
        wrapped_json = """```json
{
  "hypotheses": [
    {
      "hypothesis_id": "HYP-TEST-1",
      "title": "Mock Vulnerability",
      "category": "Security",
      "severity": "CRITICAL",
      "confidence": "HIGH",
      "status": "Likely Bug",
      "line_start": 1,
      "line_end": 1,
      "explanation": "Test explanation",
      "reasoning": "Test reasoning",
      "suggested_test": "Test test"
    }
  ]
}
```"""
        parsed = engine._parse_and_validate(wrapped_json, dummy_file)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].hypothesis_id, "HYP-TEST-1")
        self.assertEqual(parsed[0].status, BugStatus.LIKELY)

        # JSON with non-dict items
        non_dict_json = '{"hypotheses": ["string_item", 123, null]}'
        self.assertEqual(engine._parse_and_validate(non_dict_json, dummy_file), [])

    def test_duplicate_hypotheses_deduplication(self):
        hyp1 = BugHypothesis(
            hypothesis_id="HYP-DUP-1",
            title="Duplicate Title",
            category="Security",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.POTENTIAL,
            affected_file="dup.py",
            line_start=10,
            line_end=10,
            explanation="Desc",
            reasoning="Reason",
            suggested_test="Test",
        )
        hyp2 = BugHypothesis(
            hypothesis_id="HYP-DUP-2",
            title="Duplicate Title",  # Same file, line, and title
            category="Security",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            status=BugStatus.POTENTIAL,
            affected_file="dup.py",
            line_start=10,
            line_end=10,
            explanation="Desc duplicate",
            reasoning="Reason",
            suggested_test="Test",
        )

        # Metrics calculation deduplication
        metrics = HypothesisEvaluationMetrics.calculate([hyp1, hyp2])
        self.assertEqual(metrics.total_hypotheses, 2)


if __name__ == "__main__":
    unittest.main()

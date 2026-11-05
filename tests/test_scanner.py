import unittest
from pathlib import Path
from reposentinal.models import Severity
from reposentinal.providers import MockProvider
from reposentinal.scanner import scan_repository
from reposentinal.analyzer import RepoSentinelAgent


class TestRepoSentinel(unittest.TestCase):
    def setUp(self):
        self.sample_path = Path(__file__).parent / "sample_vulnerable_code.py"
        self.assertTrue(self.sample_path.exists(), "Sample test file must exist")

    def test_scanner_detects_python_file(self):
        files = scan_repository(self.sample_path)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].language, "python")
        self.assertGreater(files[0].line_count, 10)

    def test_mock_provider_heuristics(self):
        files = scan_repository(self.sample_path)
        provider = MockProvider()
        findings = provider.analyze_file(files[0])

        categories = [f.category for f in findings]
        titles = [f.title for f in findings]
        severities = [f.severity for f in findings]

        # Check that high severity security findings were detected
        self.assertIn(Severity.CRITICAL, severities)
        self.assertTrue(any("Hardcoded" in t for t in titles))
        self.assertTrue(any("Command Injection" in t for t in titles))
        self.assertTrue(any("SQL Injection" in t for t in titles))
        self.assertTrue(any("Swallowed Exception" in t for t in titles))

    def test_agent_orchestration_and_summary(self):
        files = scan_repository(self.sample_path)
        agent = RepoSentinelAgent(provider=MockProvider(), max_workers=2)
        summary = agent.analyze("test_sample", files)

        self.assertEqual(summary.scanned_files, 1)
        self.assertGreaterEqual(len(summary.findings), 4)
        self.assertGreater(summary.critical_count, 0)
        self.assertIn("findings", summary.to_dict())


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
from reposentinal.models import FileContext
from reposentinal.scanner import scan_repository
from reposentinal.indexer import (
    SymbolKind,
    build_repository_index,
    PythonASTVisitor,
    _resolve_module_to_file,
)


class TestRepositoryIndexer(unittest.TestCase):
    def test_ast_symbol_extraction(self):
        code = '''
"""Module docstring."""
import os
from math import sqrt as square_root

class SampleService:
    """Service class."""
    def __init__(self, host: str, port: int = 8080):
        self.host = host

    def run_worker(self, task_id):
        return os.getpid()

def top_level_helper(x, y):
    srv = SampleService("localhost")
    return srv.run_worker(x)
'''
        visitor = PythonASTVisitor(rel_path="sample.py")
        import ast
        tree = ast.parse(code)
        visitor.visit(tree)

        # Check symbols
        names_to_syms = {s.name: s for s in visitor.symbols}
        self.assertIn("SampleService", names_to_syms)
        self.assertEqual(names_to_syms["SampleService"].kind, SymbolKind.CLASS)
        self.assertEqual(names_to_syms["SampleService"].docstring, "Service class.")

        self.assertIn("__init__", names_to_syms)
        self.assertEqual(names_to_syms["__init__"].kind, SymbolKind.METHOD)
        self.assertEqual(names_to_syms["__init__"].parent, "SampleService")
        self.assertEqual(names_to_syms["__init__"].parameters, ["self", "host", "port"])

        self.assertIn("run_worker", names_to_syms)
        self.assertEqual(names_to_syms["run_worker"].kind, SymbolKind.METHOD)
        self.assertEqual(names_to_syms["run_worker"].parent, "SampleService")

        self.assertIn("top_level_helper", names_to_syms)
        self.assertEqual(names_to_syms["top_level_helper"].kind, SymbolKind.FUNCTION)
        self.assertEqual(names_to_syms["top_level_helper"].parameters, ["x", "y"])

        # Check imports
        modules = [imp.module for imp in visitor.imports]
        self.assertIn("os", modules)
        self.assertIn("math", modules)

        # Check function calls
        self.assertIn("SampleService", visitor.calls)
        self.assertIn("run_worker", visitor.calls)

    def test_module_resolution(self):
        available_files = {
            "reposentinal/__init__.py",
            "reposentinal/models.py",
            "reposentinal/analyzer.py",
        }

        # Absolute import resolution
        resolved = _resolve_module_to_file(
            source_file="reposentinal/analyzer.py",
            module="reposentinal.models",
            level=0,
            available_files=available_files,
        )
        self.assertEqual(resolved, "reposentinal/models.py")

        # Relative import resolution
        resolved_rel = _resolve_module_to_file(
            source_file="reposentinal/analyzer.py",
            module="models",
            level=1,
            available_files=available_files,
        )
        self.assertEqual(resolved_rel, "reposentinal/models.py")

    def test_repository_wide_index_and_topology(self):
        root_path = Path(__file__).resolve().parent.parent
        files = scan_repository(root_path, max_files=100)
        self.assertGreater(len(files), 3)

        index = build_repository_index(files)

        # Verify symbols discovered
        agent_syms = index.find_symbols("RepoSentinelAgent")
        self.assertTrue(len(agent_syms) >= 1)
        self.assertEqual(agent_syms[0].kind, SymbolKind.CLASS)

        scan_syms = index.find_symbols("scan_repository")
        self.assertTrue(len(scan_syms) >= 1)
        self.assertEqual(scan_syms[0].kind, SymbolKind.FUNCTION)

        # Verify dependency graph edges
        analyzer_deps = index.get_dependencies("reposentinal/analyzer.py")
        self.assertTrue(
            any("models.py" in dep for dep in analyzer_deps),
            f"Expected models.py in dependencies of analyzer.py, got: {analyzer_deps}",
        )

        models_dependents = index.get_dependents("reposentinal/models.py")
        self.assertTrue(
            any("analyzer.py" in dep for dep in models_dependents),
            f"Expected analyzer.py in dependents of models.py, got: {models_dependents}",
        )

        # Verify serialization
        d = index.to_dict()
        self.assertIn("topology", d)
        self.assertGreater(d["total_symbols"], 10)
        self.assertGreater(d["classes_count"], 0)
        self.assertGreater(d["functions_count"], 0)


if __name__ == "__main__":
    unittest.main()

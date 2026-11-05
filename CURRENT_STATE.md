# RepoSentinel: Current State & Architecture Assessment

*Last Updated: 2026-11-05*  
*Document Version: 1.1.0 (Phase 2: Repository-Aware Symbol Index & Topology)*  
*Lead Engineer Status Report*

---

## 1. Executive Summary

RepoSentinel is an autonomous bug and vulnerability discovery system for GitHub repositories. With the completion of **Phase 2**, the system has evolved from a flat file-by-file scanner into a **repository-aware code intelligence engine**. It now constructs an Abstract Syntax Tree (AST) symbol index and dependency graph topology of the target codebase before running analysis.

The system continues to run on standard library Python (>=3.9) with zero external runtime dependencies.

---

## 2. System Architecture

The codebase contains the following modular components:

```
reposentinal/
├── bin/reposentinal          # Standalone executable CLI launcher
├── reposentinal/
│   ├── __init__.py           # Package versioning (v0.2.0) and top-level exports
│   ├── models.py             # Domain models (BugFinding, FileContext, ScanSummary, Severity)
│   ├── indexer.py            # AST Symbol Indexer & Dependency Topology Graph (Phase 2)
│   ├── scanner.py            # Target cloning, directory walker, binary filter, extension map
│   ├── providers.py          # LLM integrations (MockProvider, GeminiProvider, OpenAIProvider)
│   ├── analyzer.py           # Concurrency orchestrator (ThreadPoolExecutor, topology integration)
│   ├── reporter.py           # Formatting engines (ANSI Terminal, Markdown, JSON, Topology)
│   └── cli.py                # Command-line interface with --topology and --fail-on-bugs
├── tests/
│   ├── __init__.py
│   ├── sample_vulnerable_code.py  # Intentional multi-category vulnerability test fixture
│   ├── test_scanner.py            # Scanner, heuristic, and orchestrator unit tests
│   └── test_indexer.py            # AST symbol extraction, resolution, and topology tests
├── pyproject.toml            # Package configuration & standard entrypoints
└── requirements.txt          # Zero required runtime dependencies
```

### Architecture Data Flow:
```
[User / CLI Target]
        │
        ▼
[scanner.prepare_target] ──(Remote URL)──► [git clone --depth 1 to tempdir]
        │
        ▼
[scanner.scan_repository] ──► Extracts FileContext objects (filtered, size-checked, text-verified)
        │
        ▼
[indexer.build_repository_index] ──► Generates Symbol Index & Dependency Graph
        │                            (Classes, Functions, Methods, Imports, Call references)
        ▼
[analyzer.RepoSentinelAgent] ──► Concurrently dispatches FileContexts across ThreadPool
        │
        ├──► [MockProvider (Static Heuristics)] ──► Regex & structural pattern matching
        └──► [GeminiProvider / OpenAIProvider]  ──► Structured JSON prompting via REST API
        │
        ▼
[Deduplication, Severity Sorting, & Topology Enrichment]
        │
        ▼
[reporter.TerminalReporter / MarkdownReporter / JSONReporter] (Includes Topology Map)
```

---

## 3. Implemented Features (v0.2.0)

| Component | Capabilities | Status |
|---|---|---|
| **Symbol Indexer** | AST-based extraction of Classes, Functions, Methods, Docstrings, Parameters, Decorators, and Line spans | ✅ Complete (Phase 2) |
| **Dependency Topology** | Resolves absolute & relative Python imports, internal file-to-file graph edges, reverse dependencies, and external package imports | ✅ Complete (Phase 2) |
| **Call Reference Mapping** | Maps caller files to symbol invocations across the repository | ✅ Complete (Phase 2) |
| **CLI & Flags** | `--topology` flag to render complete dependency and symbol hierarchy; `--fail-on-bugs` for CI/CD gating | ✅ Complete |
| **Dual Engine** | Static Heuristics (Zero-network) + LLM Semantic Reasoning (Gemini, OpenAI, Ollama) | ✅ Complete |
| **Target Ingestion** | Local directory walk, single file scan, remote GitHub repository shallow cloning with auto cleanup | ✅ Complete |
| **Reporting** | ANSI Terminal cards with Topology stats, PR-ready Markdown report, structured JSON | ✅ Complete |

---

## 4. Test Suite & Verification Status

Automated test execution: `python3 -m unittest discover -v tests`
- `test_ast_symbol_extraction`: Validates AST extraction of classes, methods, docstrings, parameters, and calls.
- `test_module_resolution`: Validates resolution of both absolute (`reposentinal.models`) and relative (`.models`) import statements.
- `test_repository_wide_index_and_topology`: Tests whole-codebase topology generation and dependency edge mapping.
- `test_scanner_detects_python_file`: Verifies language detection, line counts, and metadata extraction.
- `test_mock_provider_heuristics`: Validates static detection across critical, high, and medium bug classes.
- `test_agent_orchestration_and_summary`: Confirms multi-threaded agent execution, deduplication, and summary metrics.

**Test Summary**: `6/6 passed (100%) in 0.028s`.

---

## 5. Current Limitations (Gaps to Research-Grade System)

With Phase 2 complete, the system has a structural model of the repository. The remaining gaps are:

1. **Attack Surface & Risk Prioritizer (Phase 3)**:
   - Scanning currently executes on all files concurrently. A research-grade engine should rank files based on attack surface risk (API routes, authentication, crypto, database operations) to scan critical code first.
2. **Context-Enriched Prompts (Phase 4)**:
   - The symbol index is not yet injected into LLM prompts. In Phase 4, when analyzing a file, the prompt will include signatures and docstrings of imported symbols.
3. **Autonomous False Positive Verification (Phase 5)**:
   - Second-pass reflection to cross-verify findings against caller sanitizers.
4. **Patch Synthesis (Phase 6)**:
   - Autonomous generation of unified `.patch` diffs.

---

## 6. Recommended Next Step: Phase 3 (Attack Surface & Risk Prioritizer)

- Create `reposentinal/prioritizer.py` to evaluate risk scores per file based on imported frameworks (e.g., Flask/FastAPI/Django routes), database calls, shell commands, and authentication modules.
- Reorder scanning queues so the highest-risk files are evaluated first.

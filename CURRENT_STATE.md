# RepoSentinel: Current State & Architecture Assessment

*Last Updated: 2026-11-05*  
*Document Version: 1.0.0*  
*Lead Engineer Status Report*

---

## 1. Executive Summary

RepoSentinel is an autonomous bug and vulnerability discovery system for GitHub repositories. The current MVP operates as a fast, zero-dependency command-line agent capable of scanning both local file paths and remote GitHub repositories. It integrates a dual-mode engine: an offline static heuristic detector and an LLM semantic agent supporting Google Gemini, OpenAI, DeepSeek, and local Ollama models.

The current implementation is functional, verified against intentional vulnerability test fixtures, and covered by automated unit tests.

---

## 2. System Architecture

The existing codebase is structured into modular components adhering strictly to standard library Python (>=3.9):

```
reposentinal/
├── bin/reposentinal          # Standalone executable CLI launcher
├── reposentinal/
│   ├── __init__.py           # Package versioning (v0.1.0)
│   ├── models.py             # Domain models (BugFinding, FileContext, ScanSummary, Severity)
│   ├── scanner.py            # Target cloning, directory walker, binary filter, extension map
│   ├── providers.py          # LLM integrations (MockProvider, GeminiProvider, OpenAIProvider)
│   ├── analyzer.py           # Concurrency orchestrator (ThreadPoolExecutor, deduplication)
│   ├── reporter.py           # Formatting engines (ANSI Terminal, Markdown, JSON)
│   └── cli.py                # Command-line interface & argument parser
├── tests/
│   ├── __init__.py
│   ├── sample_vulnerable_code.py  # Intentional multi-category vulnerability test fixture
│   └── test_scanner.py            # Unittest test cases
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
[analyzer.RepoSentinelAgent] ──► Concurrently dispatches FileContexts across ThreadPool
        │
        ├──► [MockProvider (Static Heuristics)] ──► Regex & structural pattern matching
        └──► [GeminiProvider / OpenAIProvider]  ──► Structured JSON prompting via REST API
        │
        ▼
[Deduplication & Severity Sorting]
        │
        ▼
[reporter.TerminalReporter / MarkdownReporter / JSONReporter]
```

---

## 3. Features Implemented

| Component | Capabilities | Status |
|---|---|---|
| **CLI & Packaging** | Zero runtime dependencies, standalone launcher (`bin/reposentinal`), argument parsing, env var fallback (`GEMINI_API_KEY`, `OPENAI_API_KEY`), `--fail-on-bugs` CI flag | ✅ Complete |
| **Ingestion** | Local directory walk, single file scan, remote GitHub repository shallow cloning and automated temp directory cleanup | ✅ Complete |
| **Language Coverage** | Python, TypeScript, JavaScript, Go, Rust, Java, C/C++, Ruby, PHP, SQL, Shell | ✅ Complete |
| **Static Heuristics** | Detects hardcoded secrets, command injection (`shell=True`, `os.system`), SQL injection via f-strings, disabled SSL verification, swallowed exceptions (`except: pass`), and unclosed file resources | ✅ Complete |
| **LLM Providers** | Gemini REST API (`generateContent`), OpenAI-compatible API (`/chat/completions`), Ollama local runner, Mock offline provider | ✅ Complete |
| **Reporting** | Rich ANSI terminal dashboard, GitHub PR/Issue-ready Markdown report, JSON schema export | ✅ Complete |

---

## 4. Test Suite & Verification Status

- **Automated Test Suite**: `python3 -m unittest discover -v tests`
  - `test_scanner_detects_python_file`: Verifies language detection, line counts, and metadata extraction.
  - `test_mock_provider_heuristics`: Validates static detection across critical, high, and medium bug classes.
  - `test_agent_orchestration_and_summary`: Confirms multi-threaded agent execution, deduplication, and summary metrics.
  - **Result**: `3/3 passed (100%) in 0.002s`.
- **End-to-End Verification**: Scanned `tests/sample_vulnerable_code.py` uncovering 6/6 intentional vulnerabilities across Security, Logic Error, and Resource Leak categories with accurate line numbers and remediations.

---

## 5. Current Limitations (Gaps to Research-Grade System)

While the MVP is robust and fast, it currently possesses architectural limitations inherent to file-level scanners:

1. **Isolated File Scope (Lack of Cross-File Context)**:
   - Each file is analyzed independently. Cross-file data flows (e.g. untrusted input received in `views.py` passed to an unparameterized database query in `db/crud.py`) are invisible to both the heuristic rules and the LLM prompt.
2. **No Repository Symbol & Dependency Graph**:
   - The system lacks an index of function declarations, class definitions, imports, and cross-references.
3. **Naive File Scheduling**:
   - Files are scanned in filesystem order rather than prioritizing critical attack surfaces (routes, authentication handlers, external API clients, payment handlers, database models).
4. **No Autonomous Verification & False Positive Triage**:
   - Findings from LLMs can occasionally include false positives (e.g. flagging a test mock secret or an internal trusted parameter as injection). A research-grade system requires a second-pass verification / reflection step to validate whether a finding is reachable and genuine.
5. **No Patch / Diff Generation**:
   - Findings provide textual remediation advice, but do not yet generate validated unified diffs ready for pull requests.

---

## 6. Recommended Next Steps

To evolve the MVP incrementally into a research-grade repository-aware system without breaking existing functionality:

- [ ] **Step 1: Repository Topology & Symbol Indexer (`reposentinal/indexer.py`)**:
  - Build a lightweight AST symbol indexer (classes, functions, imports, calls) to map the codebase structure.
- [ ] **Step 2: Attack Surface & Risk Prioritizer (`reposentinal/prioritizer.py`)**:
  - Rank files by architectural criticality (e.g. API endpoints, authentication, database calls) so high-risk code is prioritized.
- [ ] **Step 3: Repository-Aware Context Enrichment (`reposentinal/context.py`)**:
  - When analyzing a file, enrich the context with referenced definitions, import signatures, and project-level framework conventions.
- [ ] **Step 4: Two-Stage Verification & False-Positive Filter (`reposentinal/verifier.py`)**:
  - Implement an agentic self-verification stage that cross-checks candidate findings against call chains and sanitizers.
- [ ] **Step 5: Unified Patch & Fix Generator**:
  - Produce syntactically valid unified diffs for detected vulnerabilities.

# RepoSentinel: Current State & Architecture Assessment

*Last Updated: 2026-11-05*  
*Document Version: 1.2.0 (Phase 3: Repository-Aware Bug Hypothesis Generation)*  
*Lead Engineer Status Report*

---

## 1. Executive Summary

RepoSentinel is an autonomous bug discovery and vulnerability intelligence system for GitHub repositories. With the completion of **Phase 3**, the system has evolved from structure mapping into a **repository-aware bug hypothesis generation engine**. 

Instead of evaluating files in isolation, RepoSentinel now:
1. Synthesizes inter-module relationships, contracts, and call references from the AST symbol index.
2. Formulates structured **Bug Hypotheses** (`Potential Bug`, `Likely Bug`, and `Confirmed Bug`).
3. Enforces that model/heuristic findings are never prematurely marked as `Confirmed Bug` without deterministic runtime verification.
4. Generates concrete test scenarios describing how to reproduce or falsify each hypothesis.
5. Records research metrics (e.g. cross-file interaction ratios, confidence distribution, symbol mapping rates).

---

## 2. System Architecture

RepoSentinel maintains zero external runtime dependencies (Python >=3.9 standard library):

```
reposentinal/
├── bin/reposentinal          # Standalone executable CLI launcher
├── reposentinal/
│   ├── __init__.py           # Package versioning (v0.3.0) and top-level exports
│   ├── models.py             # Domain models (BugFinding, FileContext, ScanSummary, Severity)
│   ├── indexer.py            # AST Symbol Indexer & Dependency Topology Graph (Phase 2)
│   ├── context.py            # Repository Context Builder & Prompt Synthesizer (Phase 3)
│   ├── hypothesis.py         # BugHypothesis schema, BugStatus, Confidence & Metrics (Phase 3)
│   ├── hypothesis_engine.py  # RuleBasedHypothesisEngine & LLMHypothesisEngine (Phase 3)
│   ├── scanner.py            # Target cloning, directory walker, binary filter, extension map
│   ├── providers.py          # LLM integrations (MockProvider, GeminiProvider, OpenAIProvider)
│   ├── analyzer.py           # Multi-threaded orchestrator & hypothesis synthesis
│   ├── reporter.py           # Formatting engines (ANSI Terminal, Markdown, JSON, Research Metrics)
│   └── cli.py                # Command-line interface with --topology, --fail-on-bugs
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   └── cross_file_repo/  # Multi-file repository fixture (auth, orders, db)
│   │       ├── auth_service.py
│   │       ├── order_service.py
│   │       └── db_gateway.py
│   ├── sample_vulnerable_code.py  # Intentional vulnerability test fixture
│   ├── test_scanner.py            # Scanner, heuristic, and orchestrator unit tests
│   ├── test_indexer.py            # AST symbol extraction, resolution, and topology tests
│   └── test_hypothesis.py         # Hypothesis schema, cross-module reasoning, resilience tests
├── pyproject.toml            # Package configuration & standard entrypoints
└── requirements.txt          # Zero required runtime dependencies
```

### Architecture Data Flow (Phase 3):
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
[indexer.build_repository_index] ──► Generates Symbol Index & Dependency Topology Graph
        │
        ▼
[context.RepositoryContextBuilder] ──► Synthesizes per-file Cross-Module Context:
        │                              - Imported internal symbol contracts & docstrings
        │                              - Inbound callers and cross-module usages
        │                              - External library dependencies
        ▼
[analyzer.RepoSentinelAgent] ──► Multi-threaded dispatch across workers:
        │
        ├──► [BaseHypothesisEngine] (RuleBased or LLM: Gemini / OpenAI / Ollama)
        │         │
        │         ▼
        │    [Hypothesis Invariant Enforcement]
        │    - Validates schema and line ranges
        │    - Prevents unverified "Confirmed Bug" status (downgrades to Likely Bug)
        │    - Extracts related symbols and suggested test scenarios
        │
        ├──► [Legacy Finding Mapping] (Preserves 100% backward compatibility)
        │
        ▼
[Deduplication, Sorting by Severity & Confidence, Metrics Calculation]
        │
        ▼
[reporter.TerminalReporter / MarkdownReporter / JSONReporter]
```

---

## 3. Bug Hypothesis Schema

Each generated hypothesis contains the following structured fields:

```json
{
  "hypothesis_id": "HYP-CROSS-NULL-6",
  "title": "Incorrect Assumption: Unchecked Return Value from `verify_jwt_token`",
  "category": "Incorrect Assumptions",
  "severity": "HIGH",
  "confidence": "HIGH",
  "status": "Likely Bug",
  "affected_file": "order_service.py",
  "affected_symbol": "process_order_checkout",
  "line_start": 6,
  "line_end": 9,
  "explanation": "Variable `user` is assigned from cross-module function `verify_jwt_token` (from `auth_service.py`) and dereferenced without checking if it is None.",
  "reasoning": "Cross-module dependency analysis: `auth_service.py` defines `verify_jwt_token`. Its contract/docstring indicates it can return None on failure. `order_service.py` directly accesses properties on `user` without a null guard.",
  "related_symbols": ["auth_service.py:verify_jwt_token"],
  "suggested_test": "Mock or trigger `verify_jwt_token` to return None and execute `process_order_checkout`; assert that TypeError or AttributeError occurs instead of handled failure.",
  "code_snippet": "user = verify_jwt_token(token)",
  "remediation": "Add validation: `if user is None: raise ...` before accessing properties."
}
```

### Confirmation Status Invariant:
- `Potential Bug`: Hypothesized weakness based on code patterns, requiring validation of input boundaries.
- `Likely Bug`: High-confidence hypothesis supported by direct structural cross-module evidence (e.g. caller dereferences return value from callee documented as returning `None`).
- `Confirmed Bug`: Strictly reserved for bugs proven through deterministic test execution (never self-certified by an LLM).

---

## 4. How Repository Context is Constructed

The `RepositoryContextBuilder` transforms flat files into relational context:
1. **Defined Symbols**: Functions, methods, and classes defined in the current file with their parameter lists and line spans.
2. **Imported Contracts**: For each internal import, queries the symbol index for the target module's functions, classes, parameter signatures, and docstrings.
3. **Caller References**: Scans dependent files that import this module to detect which symbols are actively called by external modules.
4. **Prompt Serialization**: Compactly formats these relationships into an LLM-accessible prompt header (`context.to_prompt_context()`), allowing models to reason across file boundaries without exceeding token limits.

---

## 5. Test Suite & Verification Status

Automated test execution: `python3 -m unittest discover -v tests`
- `test_hypothesis_schema_validation_success`: Schema parsing, invariants, round-trip serialization.
- `test_confirmed_status_invariant_rejection`: Enforces that unconfirmed hypotheses cannot self-certify as `Confirmed Bug`.
- `test_invalid_line_ranges`: Validates rejection of negative lines or inverted ranges.
- `test_topology_aware_context_construction`: Validates cross-module contract extraction from `auth_service.py` into `order_service.py`.
- `test_cross_module_bug_hypothesis_on_fixture`: Detects unchecked return assumption on multi-file fixture with full metrics.
- `test_symbol_to_hypothesis_mapping`: Confirms enclosing function name resolution (`process_order_checkout`).
- `test_malformed_and_empty_model_responses`: Resiliency against empty strings, whitespace, HTML errors, non-dict payloads, and markdown code blocks.
- `test_duplicate_hypotheses_deduplication`: Verifies deduplication across identical file/line findings.
- `test_ast_symbol_extraction`: Phase 2 symbol visitor tests.
- `test_module_resolution`: Phase 2 import resolution tests.
- `test_repository_wide_index_and_topology`: Phase 2 codebase graph verification.
- `test_scanner_detects_python_file`: Phase 1 scanner verification.
- `test_mock_provider_heuristics`: Phase 1 heuristic rule verification.
- `test_agent_orchestration_and_summary`: Phase 1 multi-threaded execution and backward compatibility.

**Total**: `14/14 tests passing (100%) in 0.049s`.

---

## 6. Research Metrics Output

When scanned, RepoSentinel computes evaluation metrics designed for benchmark studies:
- `total_hypotheses`: Total generated candidate bugs.
- `by_status`: Distribution across `Likely Bug`, `Potential Bug`, and `Confirmed Bug`.
- `by_confidence`: Distribution across `HIGH`, `MEDIUM`, and `LOW`.
- `cross_file_count`: Hypotheses whose discovery required cross-module structural reasoning.
- `cross_file_ratio`: Ratio of cross-file bugs to total bugs.
- `symbol_mapped_count`: Number of hypotheses mapped to specific AST symbols.

---

## 7. Current Limitations & Next Planned Phase

1. **Sandboxed Test Execution (Phase 4)**:
   - While hypotheses suggest concrete test cases (`suggested_test`), the system does not yet autonomously execute them in an isolated sandbox to elevate `Likely Bug` into `Confirmed Bug`.
2. **Patch Synthesis (Phase 5)**:
   - Unified diff patch generation will be addressed in a subsequent phase.

### Recommended Next Milestone: Phase 4 (Adversarial Verification & Sandboxed Test Execution)
- Build an isolated test executor to run reproduction test scripts for high-confidence hypotheses.
- Promote successfully reproduced hypotheses from `Likely Bug` to `Confirmed Bug`.

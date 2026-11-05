# RepoSentinel: Current State & Architecture Assessment

*Last Updated: 2026-11-05*  
*Document Version: 1.3.0 (Phase 4: Adversarial Test Generation & Sandboxed Verification)*  
*Lead Engineer Status Report*

---

## 1. Executive Summary

RepoSentinel is an autonomous bug discovery and vulnerability intelligence system for GitHub repositories. With the completion of **Phase 4**, the system has advanced into a full **adversarial verification pipeline**:

$$\text{BugHypothesis} \longrightarrow \text{Adversarial Test Generation} \longrightarrow \text{Sandboxed Execution} \longrightarrow \text{Evidence Collection} \longrightarrow \text{Verification Decision}$$

Instead of relying on model self-reporting or heuristic confidence alone, RepoSentinel now:
1. Synthesizes executable Python reproduction tests tailored to each hypothesis category (cross-module null assumptions, SQL injection, command injection, insecure configuration, swallowed exceptions).
2. Executes reproduction tests safely inside an isolated sandbox (`DockerSandbox` if Docker is installed, or `SafeSubprocessSandbox` fallback with environment secret scrubbing, ephemeral filesystem isolation, and timeout enforcement).
3. Evaluates deterministic execution evidence:
   - **REPRODUCED**: Target entered expected vulnerable state / crash -> promotes hypothesis to `Confirmed Bug`.
   - **FALSE_POSITIVE** / **NOT_REPRODUCED**: Target safely handled or rejected input -> hypothesis remains unconfirmed and is flagged to prevent false alarms.
   - **INCONCLUSIVE**: Environment setup failure, missing dependency, or execution timeout.
4. Enforces strict confirmation invariants: an LLM or static rule can never mark a bug as `Confirmed Bug` without deterministic reproduction evidence.
5. Captures comprehensive research metrics (reproduction rate, false positive prevention rate, test execution time, confidence distribution).

---

## 2. System Architecture

RepoSentinel maintains zero external runtime dependencies (Python >=3.9 standard library):

```
reposentinal/
├── bin/reposentinal          # Standalone executable CLI launcher
├── reposentinal/
│   ├── __init__.py           # Package versioning (v0.4.0) and top-level exports
│   ├── models.py             # Domain models (BugFinding, FileContext, ScanSummary, Severity)
│   ├── indexer.py            # AST Symbol Indexer & Dependency Topology Graph (Phase 2)
│   ├── context.py            # Repository Context Builder & Prompt Synthesizer (Phase 3)
│   ├── hypothesis.py         # BugHypothesis schema, BugStatus, Confidence & Metrics (Phase 3)
│   ├── hypothesis_engine.py  # RuleBasedHypothesisEngine & LLMHypothesisEngine (Phase 3)
│   ├── test_generator.py     # AdversarialTest, TestSafetyValidator, DeterministicTestGenerator (Phase 4)
│   ├── sandbox.py            # BaseSandbox, DockerSandbox, SafeSubprocessSandbox (Phase 4)
│   ├── verification.py       # VerificationStatus, ExecutionResult, VerificationEvidence (Phase 4)
│   ├── verifier.py           # HypothesisVerifier & Research Metrics Evaluator (Phase 4)
│   ├── scanner.py            # Target cloning, directory walker, binary filter, extension map
│   ├── providers.py          # LLM integrations (MockProvider, GeminiProvider, OpenAIProvider)
│   ├── analyzer.py           # Multi-threaded orchestrator & verification pipeline integration
│   ├── reporter.py           # Formatting engines (ANSI Terminal, Markdown, JSON, Research Metrics)
│   └── cli.py                # Command-line interface with --topology, --no-verify, --sandbox-backend
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── cross_file_repo/  # Multi-file vulnerable repository fixture (auth, orders, db)
│   │   │   ├── auth_service.py
│   │   │   ├── order_service.py
│   │   │   └── db_gateway.py
│   │   └── safe_repo/        # Safe fixture for false-positive validation
│   │       ├── auth_service.py
│   │       ├── safe_order_service.py
│   │       └── db_gateway.py
│   ├── sample_vulnerable_code.py  # Intentional vulnerability test fixture
│   ├── test_scanner.py            # Scanner, heuristic, and orchestrator unit tests
│   ├── test_indexer.py            # AST symbol extraction, resolution, and topology tests
│   ├── test_hypothesis.py         # Hypothesis schema, cross-module reasoning, resilience tests
│   └── test_verification.py       # Adversarial generation, sandbox lifecycle, invariants, verification tests
├── pyproject.toml            # Package configuration & standard entrypoints
└── requirements.txt          # Zero required runtime dependencies
```

### Complete End-to-End Pipeline (Phase 4):
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
        │    - Formulates structured BugHypothesis instances
        │
        ▼
[Deduplication of Candidate Hypotheses]
        │
        ▼
[verifier.HypothesisVerifier] (Adversarial Verification Pipeline)
        │
        ├──► [test_generator.DeterministicTestGenerator]
        │         │
        │         ▼
        │    Synthesizes targeted AdversarialTest script
        │    Validated by TestSafetyValidator (blocks destructive calls)
        │
        ├──► [sandbox.BaseSandbox] (DockerSandbox or SafeSubprocessSandbox)
        │         │
        │         ▼
        │    Executes in isolated ephemeral environment:
        │    - Environment secrets scrubbed (OPENAI_API_KEY, GEMINI_API_KEY, tokens stripped)
        │    - Isolated Python invocation (python -I -s -B)
        │    - Timeout enforcement (default: 10s)
        │    - Captures stdout, stderr, exit code, duration
        │
        ├──► [Deterministic Verification Evaluation]
        │         │
        │         ├── Exit Code 0 ──► REPRODUCED ──► Promotes to [Confirmed Bug]
        │         ├── Exit Code 2 ──► FALSE_POSITIVE / NOT_REPRODUCED ──► Retains Likely/Potential
        │         ├── Exit Code 3 ──► INCONCLUSIVE (Setup/dependency constraint)
        │         └── Timeout     ──► INCONCLUSIVE (Execution threshold exceeded)
        │
        ▼
[reporter.TerminalReporter / MarkdownReporter / JSONReporter]
```

---

## 3. Verification States & Decision Model

RepoSentinel implements explicit verification states:

| Status | Definition | Transition Condition |
|---|---|---|
| `UNVERIFIED` | Initial state of a generated hypothesis. | Before adversarial test execution. |
| `REPRODUCED` | The adversarial test successfully reproduced the vulnerable behavior or crash. | Sandbox exits with code `0`, confirming deterministic reproduction. |
| `CONFIRMED` | Hypothesis promoted to verified status based on evidence. | Automatically promoted upon reaching `REPRODUCED`. |
| `NOT_REPRODUCED` | The test executed but the target did not exhibit vulnerable behavior. | Sandbox exits with code `2`. |
| `FALSE_POSITIVE` | Safe handling observed (e.g. grace check handled null input safely). | Sandbox exits with code `2` with `SAFE_HANDLING_OBSERVED`. |
| `INCONCLUSIVE` | The test could not conclude due to timeout or missing dependencies. | Sandbox exits with code `3` or timeout expiration. |

### Strict Confirmation Invariant:
An LLM or static rule can **never** mark a hypothesis as `Confirmed Bug`. Direct instantiation or JSON deserialization of `Confirmed Bug` without verified execution proof (`is_verified=True`) is immediately rejected or downgraded to `Likely Bug`. Only deterministic execution evidence can promote a finding to `Confirmed Bug`.

---

## 4. Sandbox Isolation Architecture

The execution sandbox ensures untrusted or generated test code never affects the host system:

1. **Docker Sandbox (`DockerSandbox`)**:
   - Containerized execution using `python:3.11-slim`.
   - Flags: `--network=none`, `--memory=256m`, `--cpus=1`.
   - Volume mounts only an ephemeral temporary directory, cleaned up upon test conclusion.
2. **Safe Subprocess Sandbox (`SafeSubprocessSandbox`)**:
   - Primary fallback when Docker is unavailable.
   - Copies repository files to an isolated `tempfile.mkdtemp` workspace.
   - Clears and scrubs all host environment variables (removes `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GH_TOKEN`, and any variable containing `SECRET`, `PASSWORD`, `AUTH`, `KEY`).
   - Invokes target via `sys.executable -I -s -B` (isolated mode, no user site packages, no bytecode cache).
   - Enforces execution timeouts and purges temporary directories in `finally` blocks.

---

## 5. Test Suite & Verification Status

Automated test execution: `python3 -m unittest discover tests`

- `test_adversarial_test_generation_null_assumption`: Validates reproduction script synthesis for cross-module null assumptions.
- `test_adversarial_test_generation_sql_injection`: Validates test script generation for SQL injection vulnerabilities.
- `test_test_safety_validator_rejects_dangerous_patterns`: Verifies rejection of destructive code (`shutil.rmtree('/')`, `rm -rf /`, `os.remove('/etc/passwd')`).
- `test_test_safety_validator_rejects_malformed_syntax`: Verifies rejection of invalid Python code.
- `test_test_safety_validator_rejects_empty_code`: Validates rejection of empty test code.
- `test_sandbox_lifecycle_and_output_capture`: Validates stdout/stderr capture, exit code handling, and ephemeral workspace cleanup.
- `test_sandbox_timeout_handling`: Validates timeout enforcement and status capture.
- `test_sandbox_scrubs_host_secrets`: Confirms host secrets and API keys are completely stripped from sandbox execution.
- `test_reproduction_on_vulnerable_fixture`: Proves end-to-end reproduction of real cross-module `TypeError` on vulnerable fixture and promotion to `Confirmed Bug`.
- `test_false_positive_differentiation`: Proves that safe code (`safe_order_service.py`) gracefully handles null tokens and is correctly classified as `FALSE_POSITIVE` rather than confirmed.
- `test_inconclusive_on_setup_failure`: Validates `INCONCLUSIVE` classification when target modules or dependencies fail to import.
- `test_research_metrics_calculation`: Validates aggregation of reproduction rate, false positive counts, and timing metrics.
- `test_end_to_end_agent_with_verification`: Tests full `RepoSentinelAgent` workflow with verification enabled.
- All 14 Phase 3 hypothesis and topology tests.

**Total**: `27/27 tests passing (100%) in 1.8s`.

---

## 6. Research Metrics Output

When scanned with verification enabled, RepoSentinel calculates empirical evaluation metrics:
- `tests_generated`: Total adversarial reproduction tests synthesized.
- `tests_executed`: Total tests executed inside the sandbox.
- `reproduced_count`: Number of confirmed, reproduced bugs.
- `not_reproduced_count`: Number of un-reproduced hypotheses.
- `false_positive_count`: Number of candidate bugs disproved by safe execution behavior.
- `inconclusive_count`: Number of tests restricted by setup or timeout constraints.
- `reproduction_rate`: Ratio of confirmed bugs to executed tests ($\frac{\text{reproduced}}{\text{executed}}$).
- `sandbox_backend`: Active execution backend (`docker` or `safe_subprocess`).
- `average_verification_seconds`: Mean execution time per test.

---

## 7. Current Limitations & Next Planned Phase

1. **Multi-Language Test Execution (Phase 5/6)**:
   - Phase 4 supports Python reproduction tests. Subsequent phases will extend deterministic drivers to TypeScript, Go, and Rust.
2. **Patch Synthesis (Phase 5)**:
   - Synthesizing unified diff patches (`.patch`) for confirmed bugs and re-verifying that the adversarial test passes after patching.

### Recommended Next Milestone: Phase 5 (Autonomous Patch Synthesis & Pull Request Generator)
- Implement an automated patch engine that takes confirmed bugs and produces unified diff fixes.
- Re-run verification tests against patched code to guarantee the vulnerability is eliminated without introducing regressions.

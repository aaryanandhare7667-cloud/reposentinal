# RepoSentinel Engineering Roadmap (TODO)

## Phase 1: MVP Foundation (Completed ✅)
- [x] Zero-dependency package architecture (`models`, `scanner`, `analyzer`, `providers`, `reporter`, `cli`)
- [x] Standalone CLI launcher (`bin/reposentinal`) with argument parsing and exit codes
- [x] Multi-language detection and noise directory exclusion (`.git`, `node_modules`, `venv`, lockfiles)
- [x] Remote GitHub repository ingestion with shallow clone and automatic cleanup
- [x] Offline heuristic analyzer (`MockProvider`) covering secrets, injection, swallowed exceptions, SSL flags
- [x] Gemini REST API and OpenAI/Ollama compatible provider implementations
- [x] Multi-threaded concurrent file analysis (`ThreadPoolExecutor`)
- [x] Multiple output reporters: ANSI Terminal dashboard, GitHub PR Markdown, structured JSON
- [x] Comprehensive test suite (`tests/test_scanner.py`) and vulnerability sample fixture (`tests/sample_vulnerable_code.py`)
- [x] Current state architecture assessment (`CURRENT_STATE.md`)

---

## Phase 2: Repository-Aware Symbol Index & Topology (Completed ✅)
- [x] Build AST-based symbol extractor for Python files (`reposentinal/indexer.py`)
  - [x] Extracted classes, functions, methods, parameters, docstrings, decorators, and line spans
  - [x] Tracked function and method call references
- [x] Construct file-level import and dependency graph (`DependencyGraph`)
  - [x] Absolute and relative import resolution
  - [x] Forward edges (`file -> imported files`) and reverse edges (`file -> dependent files`)
  - [x] External/stdlib dependency tracking
- [x] Integrated topology into `ScanSummary` and reporters (`TerminalReporter`, `MarkdownReporter`)
- [x] Added `--topology` CLI flag for visualizing codebase topology
- [x] Added dedicated unit tests in `tests/test_indexer.py` (6/6 tests passing)

---

## Phase 3: Repository-Aware Bug Hypothesis Generation (Completed ✅)
- [x] Designed and implemented structured `BugHypothesis` schema (`hypothesis_id`, `category`, `severity`, `confidence`, `status`, `affected_symbol`, `explanation`, `reasoning`, `related_symbols`, `suggested_test`)
- [x] Enforced strict status distinction (`Potential Bug`, `Likely Bug`, `Confirmed Bug`) with invariant preventing self-confirmation by LLMs
- [x] Implemented `RepositoryContextBuilder` synthesizing cross-file contracts, imported symbol signatures, and inbound caller references
- [x] Built modular `RuleBasedHypothesisEngine` (detects cross-module unchecked return assumptions, unvalidated flows, command/SQL injections, swallowed exceptions)
- [x] Built `LLMHypothesisEngine` supporting Gemini, OpenAI, DeepSeek, and local Ollama models with context enrichment
- [x] Added multi-file cross-module test fixture (`tests/fixtures/cross_file_repo/`)
- [x] Implemented research evaluation metrics (`HypothesisEvaluationMetrics`: cross-file ratio, confidence distribution, symbol mapping)
- [x] Added comprehensive test suite in `tests/test_hypothesis.py` (14/14 total tests passing)
- [x] Updated Terminal, Markdown, and JSON reporters with hypothesis dashboards and research metrics

---

## Phase 4: Adversarial Test Generation & Sandboxed Verification (Completed ✅)
- [x] Implemented `AdversarialTest` model and `DeterministicTestGenerator` synthesizing targeted reproduction scripts
  - [x] Unchecked return / null assumption tests
  - [x] SQL injection parameterization validation tests
  - [x] Command injection `shell=True` tests
  - [x] Insecure SSL `verify=False` configuration tests
  - [x] Swallowed exception tests
- [x] Built `TestSafetyValidator` to block dangerous or destructive system calls (`shutil.rmtree`, `rm -rf`, `os.remove`)
- [x] Built isolated execution sandbox layer (`reposentinal/sandbox.py`)
  - [x] `DockerSandbox` with network isolation (`--network=none`), memory limits (`--memory=256m`), and CPU limits (`--cpus=1`)
  - [x] `SafeSubprocessSandbox` fallback: ephemeral workspace copying, host secret scrubbing, isolated python flags (`-I -s -B`), and timeout enforcement
- [x] Implemented explicit verification states (`UNVERIFIED`, `REPRODUCED`, `NOT_REPRODUCED`, `INCONCLUSIVE`, `CONFIRMED`, `FALSE_POSITIVE`)
- [x] Built `HypothesisVerifier` executing tests and enforcing deterministic confirmation invariant
- [x] Differentiated true positives from false positives (safe rejection/handling observed)
- [x] Added empirical research metrics (`tests_generated`, `tests_executed`, `reproduced_count`, `confirmed_count`, `false_positive_count`, `reproduction_rate`, `average_verification_seconds`)
- [x] Added dedicated safe test fixture (`tests/fixtures/safe_repo/`)
- [x] Added comprehensive unit and integration test suite (`tests/test_verification.py`, 27/27 tests passing)
- [x] Added `--no-verify` and `--sandbox-backend` CLI flags

---

## Phase 5: Autonomous Patch Synthesis & Pull Request Generator (Next Up 🚀)
- [ ] Generate syntactically valid unified diff patches (`.patch`) for confirmed bugs
- [ ] Re-run verification tests against patched code in the sandbox to ensure vulnerability is resolved
- [ ] Verify zero regressions in existing test suite after patch application
- [ ] Automated PR comment generator and branch patch committer
- [ ] Automated GitHub Action workflow for CI/CD pull request scanning

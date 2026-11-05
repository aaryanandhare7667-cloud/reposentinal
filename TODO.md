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

## Phase 5: Automated Patch Generation & Patch Verification (Completed ✅)
- [x] Designed structured patch data models (`GeneratedPatch`, `PatchVerificationResult`, `PatchQualityMetrics`)
- [x] Built `PatchSafetyValidator` with AST verification, credential leak protection, and protected path checks
- [x] Built `IsolatedPatchWorkspace` for clean ephemeral patch application (user's host repository is 100% untouched)
- [x] Built `PatchApplier` applying patches in temporary workspaces with AST integrity verification
- [x] Built `DeterministicPatchGenerator` synthesizing targeted, minimal patches without full file rewrites
- [x] Built `PatchVerifier` implementing Dual-Phase Verification:
  - [x] Step A: Adversarial Re-Testing (asserts vulnerability is no longer reproduced)
  - [x] Step B: Functional Regression Testing (asserts legitimate inputs still execute successfully)
- [x] Built explicit patch verification states (`GENERATED`, `VALIDATION_FAILED`, `APPLY_FAILED`, `APPLIED`, `VULNERABILITY_FIXED`, `REGRESSION_DETECTED`, `VERIFICATION_FAILED`, `VERIFIED`, `INCONCLUSIVE`)
- [x] Detected regressions where security fixes break valid workflows (`REGRESSION_DETECTED`)
- [x] Added unified diff rendering in ANSI terminal and Markdown reports
- [x] Added `--no-patch` CLI flag
- [x] Added comprehensive test suite in `tests/test_patch.py` (39/39 total tests passing)

---

## Architecture Reorganization: Clean Modular `backend/` Package (Completed ✅)
- [x] Structured backend subpackages:
  - [x] `backend/models/`: Base data models, `BugHypothesis`, `GeneratedPatch`
  - [x] `backend/scanner/`: File scanner, target prep, and binary filtering
  - [x] `backend/analysis/`: AST indexer, topology graph, context builder, hypothesis engines, LLM providers
  - [x] `backend/verification/`: Sandboxes (Docker/SafeSubprocess), test generator, verifier
  - [x] `backend/patching/`: Patch verifier, patch generator, safety validator, isolated workspace, applier
  - [x] `backend/cli/`: CLI entrypoint, argument parsing, terminal & markdown reporters
- [x] Preserved 100% backward compatibility for all Phase 1-5 callers and tests via `reposentinal/*` bridges
- [x] Updated standalone CLI launcher `bin/reposentinal` to prefer `backend.cli` with fallback
- [x] Added dedicated architecture validation tests (`tests/test_backend_structure.py`, 46/46 total tests passing)
- [x] Maintained zero external runtime dependencies

---

## Phase 6: Developer Interactive Review & PR Bot (Next Up 🚀)
- [ ] Interactive terminal review prompt (`[y] Apply Patch | [n] Discard | [e] Edit Diff`)
- [ ] Automated GitHub Pull Request comment bot to post verified patch diffs directly onto GitHub PRs
- [ ] Optional branch patch committer with signed commits
- [ ] Automated GitHub Action workflow for CI/CD pull request scanning

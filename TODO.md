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

## Phase 2: Repository-Aware Symbol Index & Topology (Next Up 🚀)
- [ ] Build AST-based symbol extractor for Python and multi-language files (`reposentinal/indexer.py`)
- [ ] Construct file-level import and dependency graph
- [ ] Extract function signatures, class hierarchies, and exported APIs
- [ ] Add unit tests for symbol indexing and dependency mapping

---

## Phase 3: Attack Surface & Risk Prioritizer
- [ ] Implement risk-scoring heuristic for source files (e.g., auth, routes, db models, crypto)
- [ ] Sort scanned files based on risk score rather than filesystem order
- [ ] Allow targeted scans by vulnerability domain (e.g., `--focus security`, `--focus logic`)
- [ ] Add unit tests for risk prioritization

---

## Phase 4: Context-Enriched Cross-File Analysis
- [ ] Integrate repository topology into LLM prompts (inject caller/callee signatures, imported type definitions)
- [ ] Enable cross-file tainted dataflow tracing (source -> intermediate -> sink)
- [ ] Enhance Mock/Heuristic provider with inter-procedural pattern checking

---

## Phase 5: Autonomous Verification & False-Positive Mitigation
- [ ] Implement two-pass verification agent (Stage 1: Discovery, Stage 2: Adversarial Critique / Verification)
- [ ] Filter out non-exploitable findings, unreachable sinks, and internal test fixtures
- [ ] Output verification confidence scores (High Confidence, Needs Review)

---

## Phase 6: Autonomous Patch Synthesis & GitHub Integration
- [ ] Generate unified diff patches (`.patch`) for detected vulnerabilities
- [ ] Autonomous GitHub Action workflow for PR scanning
- [ ] Automated PR comment bot / automated pull request creator for verified patches

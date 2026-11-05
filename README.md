# 🛡️ RepoSentinel

> **Autonomous Bug Discovery & Sandboxed Verification Agent for GitHub Repositories**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-success.svg)](requirements.txt)
[![Tests Passing](https://img.shields.io/badge/tests-27%2F27%20passing-brightgreen.svg)](tests/)

RepoSentinel is an autonomous bug discovery and verification agent that inspects codebases, identifies critical vulnerabilities, unhandled cross-module edge cases, and logic bugs, synthesizes adversarial reproduction tests, and verifies findings in an isolated sandbox.

📖 **Documentation**: See [CURRENT_STATE.md](CURRENT_STATE.md) for the complete architectural assessment and [TODO.md](TODO.md) for the active engineering roadmap.

---

## 🌟 Key Features

- **Multi-Language Detection**: Scans Python, TypeScript, JavaScript, Go, Rust, Java, C/C++, Ruby, PHP, SQL, Shell, and more.
- **Repository-Aware Symbol Index & Topology**: AST-based symbol extraction (classes, functions, methods, parameters, docstrings) and automated inter-file dependency graph mapping (`--topology`).
- **Repository-Aware Bug Hypothesis Engine**: Discovers inter-module vulnerabilities, unchecked return assumptions, and cross-file data flows with concrete reproduction test scenarios.
- **Adversarial Test Generation (Phase 4)**: Automatically synthesizes executable reproduction tests targeting hypothesized vulnerabilities (null assumptions, SQL injection, command execution, insecure SSL, swallowed exceptions).
- **Isolated Sandboxed Verification (Phase 4)**: Executes tests safely inside Docker (`--network=none`, CPU/RAM limits) or a hardened ephemeral subprocess sandbox with host environment secret scrubbing.
- **Strict Confirmation Invariant**: Findings are never marked `Confirmed Bug` merely because an LLM claimed it. Confirmation requires deterministic runtime reproduction. Differentiates verified bugs from false positives (`[FALSE POSITIVE]`).
- **Empirical Research Metrics**: Measures reproduction rate, false positive prevention rate, cross-file interaction ratios, and test execution duration.
- **Dual Engine Architecture**:
  - **Static Heuristic Engine**: Zero-network offline heuristics to catch command injections, hardcoded secrets, SQL injection formatting, swallowed exceptions, and unclosed resources.
  - **LLM Agent Engine**: Deep semantic reasoning powered by Google Gemini, OpenAI, DeepSeek, or local models via Ollama enriched with cross-file repository context.
- **Zero Required External Dependencies**: Engineered on the Python standard library—runs anywhere Python 3.9+ is installed without `pip install` hurdles.
- **Remote & Local Ingestion**: Scan any local project or pass a remote GitHub repository URL directly (shallow clones and cleans up automatically).
- **Multiple Output Formats**:
  - 🎨 **Terminal Dashboard**: Colored cards with severity badges, status, confidence, cross-file reasoning, test scenarios, and research metrics.
  - 📝 **Markdown Report**: Ready to post as a GitHub Issue or Pull Request comment.
  - 📊 **JSON Export**: Structured output designed for security pipelines, CI/CD, and research benchmarking.

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/aaryanandhare7667-cloud/reposentinal.git
cd reposentinal
```

### 2. Run Instant Scan with Verification (Default)

Scan the local project or fixture with automated sandboxed verification:

```bash
python3 bin/reposentinal tests/fixtures/cross_file_repo/ --topology
```

Disable verification if you only want rapid static hypothesis generation:

```bash
python3 bin/reposentinal tests/fixtures/cross_file_repo/ --no-verify
```

### 3. Scan with LLMs

#### Using Google Gemini:
```bash
export GEMINI_API_KEY="your-gemini-api-key"
python3 bin/reposentinal . --provider gemini
```

#### Using OpenAI or DeepSeek:
```bash
export OPENAI_API_KEY="your-openai-api-key"
python3 bin/reposentinal . --provider openai --model gpt-4o-mini
```

#### Using Local LLMs via Ollama:
```bash
python3 bin/reposentinal . --provider ollama --model llama3 --base-url http://localhost:11434/v1
```

### 4. Scan a Remote GitHub Repository Directly

RepoSentinel will automatically clone the repository shallowly, scan it, and clean up temporary files:

```bash
python3 bin/reposentinal https://github.com/pallets/flask --max-files 20
```

---

## 📋 CLI Reference

```
usage: reposentinal [-h] [--provider {mock,gemini,openai,ollama}]
                    [--api-key API_KEY] [--model MODEL] [--base-url BASE_URL]
                    [--format {terminal,markdown,json,all}] [--output OUTPUT]
                    [--max-files MAX_FILES] [--workers WORKERS] [--dry-run]
                    [--fail-on-bugs] [--topology] [--no-verify]
                    [--sandbox-backend {auto,docker,subprocess}]
                    [target]

Options:
  target                Local directory path, file path, or GitHub repository URL (default: .)
  --provider            LLM provider: mock, gemini, openai, ollama (auto-detected if keys are set)
  --api-key             API key (or set GEMINI_API_KEY / OPENAI_API_KEY environment variables)
  --model               Model name (e.g. gemini-1.5-flash, gpt-4o-mini, llama3)
  --base-url            Custom base URL for OpenAI-compatible APIs or Ollama
  --format              Output format: terminal, markdown, json, all (default: terminal)
  --output, -o          File path to save Markdown or JSON report
  --max-files           Maximum source files to scan (default: 50)
  --workers             Number of concurrent worker threads (default: 4)
  --dry-run             Force offline mock/heuristic mode without sending external API requests
  --fail-on-bugs        Exit with non-zero code if CRITICAL or HIGH findings are found (CI/CD)
  --topology            Display detailed repository symbol index and dependency topology graph
  --no-verify           Disable adversarial test generation and sandboxed verification
  --sandbox-backend     Sandbox backend for executing generated tests: auto, docker, subprocess (default: auto)
```

---

## 🧪 Verification Example Output

```
======================================================================
   🛡️  REPO SENTINEL  |  Autonomous Bug Discovery Agent for GitHub   
======================================================================

Target:         tests/fixtures/cross_file_repo/
Provider:       MockProvider
Files Scanned:  3 files (32 lines of code)
Duration:       0.20s
Topology:       4 symbols (1 classes, 2 functions, 1 methods) | 2 inter-file dependencies

--- Repository-Aware Bug Hypotheses (2) ---

1.  CRITICAL  [Confirmed Bug] (High Conf) SQL Injection via Dynamic String Interpolation
   Location:    order_service.py:12 [Symbol: process_order_checkout]  (Potential Security Vulnerability)
   Explanation: Dynamic formatting of variables into SQL statement bypasses query parameterization.
   Reasoning:   Query string interpolates variables directly; untrusted input can alter SQL abstract syntax tree.
   Code:        `query = f"INSERT INTO orders (id, user_id, amount) VALUES ('{order_id}', {user_id}, {amount})"`
   Test Case:   Supply username containing single quote ("admin' OR '1'='1") and observe query syntax bypass.
   Remediation: Use parameterized queries: cursor.execute('SELECT ... WHERE u = %s', (val,))

2. [HIGH] [Confirmed Bug] (High Conf) Incorrect Assumption: Unchecked Return Value from `verify_jwt_token`
   Location:    order_service.py:6-9 [Symbol: process_order_checkout]  (Incorrect Assumptions)
   Explanation: Variable `user` is assigned from cross-module function `verify_jwt_token` (from `auth_service.py`) and dereferenced without checking if it is None.
   Reasoning:   Cross-module dependency analysis: `auth_service.py` defines `verify_jwt_token`. Its contract/docstring indicates it can return None on failure. `order_service.py` directly accesses properties on `user` without a null guard.
   Related:     auth_service.py:verify_jwt_token
   Code:        `user = verify_jwt_token(token)`
   Test Case:   Mock or trigger `verify_jwt_token` to return None and execute `process_order_checkout`; assert that TypeError or AttributeError occurs instead of handled failure.
   Remediation: Add validation: `if user is None: raise ...` before accessing properties.

--- Adversarial Sandboxed Verification Evidence (2) ---

1. [REPRODUCED] Test TEST-HYP-CROSS-NULL-6 -> Target HYP-CROSS-NULL-6 (safe_subprocess, 0.10s)
   Reproduction: VULNERABILITY_REPRODUCED: TypeError: 'NoneType' object is not subscriptable
   Notes:        Vulnerability reproduced deterministically: VULNERABILITY_REPRODUCED: TypeError: 'NoneType' object is not subscriptable

2. [REPRODUCED] Test TEST-HYP-SEC-SQL-12 -> Target HYP-SEC-SQL-12 (safe_subprocess, 0.10s)
   Reproduction: VULNERABILITY_REPRODUCED: Unescaped SQL injection probe found in query: EXECUTED: INSERT INTO orders (id, user_id, amount) VALUES ('test' OR '1'='1', 42, 100)
   Notes:        Vulnerability reproduced deterministically: VULNERABILITY_REPRODUCED: Unescaped SQL injection probe found in query: EXECUTED: INSERT INTO orders (id, user_id, amount) VALUES ('test' OR '1'='1', 42, 100)

----------------- Scan Summary Breakdown -----------------
   CRITICAL  : 2
   HIGH      : 1
   MEDIUM    : 0
   LOW       : 0
   STATUS    : Confirmed=2 | Likely=0 | Potential=0
   RESEARCH  : Cross-File Interactions=1 (50%) | Symbol Mapped=2
   VERIFIED  : Confirmed=2 | Reproduced=2 | False Positives=0 | Inconclusive=0
   SANDBOX   : Backend=safe_subprocess | Repro Rate=100% | Avg Duration=0.099s
   TOTAL     : 2
----------------------------------------------------------
```

---

## 🧪 Automated Testing

RepoSentinel includes an automated regression and verification test suite:

```bash
python3 -m unittest discover tests
```

Tests run in standard Python with zero mock libraries or external dependencies:
- Scanner and heuristic unit tests (`tests/test_scanner.py`)
- Symbol index and AST topology unit tests (`tests/test_indexer.py`)
- Hypothesis schema, reasoning, and resilience tests (`tests/test_hypothesis.py`)
- Adversarial test generation, sandbox lifecycle, invariants, and verification tests (`tests/test_verification.py`)

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

# 🛡️ RepoSentinel

> **Autonomous Bug Discovery, Sandboxed Verification & Patch Agent for GitHub Repositories**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-success.svg)](requirements.txt)
[![Tests Passing](https://img.shields.io/badge/tests-39%2F39%20passing-brightgreen.svg)](tests/)

RepoSentinel is an autonomous bug discovery, adversarial verification, and automated patch remediation agent. It inspects repositories, identifies critical vulnerabilities and cross-module edge cases, generates reproduction tests, verifies bugs in an isolated sandbox, and synthesizes regression-tested unified diff patches.

📖 **Documentation**: See [CURRENT_STATE.md](CURRENT_STATE.md) for the complete architectural assessment and [TODO.md](TODO.md) for the active engineering roadmap.

---

## 🌟 Key Features

- **Multi-Language Detection**: Scans Python, TypeScript, JavaScript, Go, Rust, Java, C/C++, Ruby, PHP, SQL, Shell, and more.
- **Repository-Aware Symbol Index & Topology**: AST-based symbol extraction (classes, functions, methods, parameters, docstrings) and automated inter-file dependency graph mapping (`--topology`).
- **Repository-Aware Bug Hypothesis Engine**: Discovers inter-module vulnerabilities, unchecked return assumptions, and cross-file data flows with concrete reproduction test scenarios.
- **Adversarial Test Generation & Sandboxed Verification (Phase 4)**: Automatically synthesizes executable reproduction tests and executes them inside an isolated sandbox (`DockerSandbox` or `SafeSubprocessSandbox` with host secret scrubbing).
- **Automated Candidate Patch Generation (Phase 5)**: Synthesizes minimal, targeted code fixes for confirmed bugs without full-file rewrites.
- **Defensive Patch Safety Validator (Phase 5)**: AST syntax check, blocks destructive commands, prevents credential leaks, and protects CI/CD configurations.
- **Isolated Workspace Application (Phase 5)**: Applies candidate patches exclusively within an isolated ephemeral temporary workspace. **The user's host repository is NEVER modified.**
- **Dual-Phase Patch Verification (Phase 5)**:
  - **Step A: Adversarial Re-Testing**: Confirms the vulnerability is no longer reproducible.
  - **Step B: Functional Regression Testing**: Confirms legitimate inputs and workflows still execute successfully.
- **Strict Invariants**: Findings are never marked `Confirmed Bug` and patches are never marked `VERIFIED` based on LLM claims alone. Runtime reproduction and regression testing are strictly required.
- **Zero Required External Dependencies**: Engineered on the standard library—runs anywhere Python 3.9+ is installed without `pip install` hurdles.
- **Multiple Output Formats**:
  - 🎨 **Terminal Dashboard**: Colored cards with severity badges, verified status, reproduction traces, research metrics, and unified diffs.
  - 📝 **Markdown Report**: Ready to post as a GitHub Issue or Pull Request comment.
  - 📊 **JSON Export**: Structured output designed for security pipelines, CI/CD, and research benchmarking.

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/aaryanandhare7667-cloud/reposentinal.git
cd reposentinal
```

### 2. Run Instant Scan with Verification & Patch Generation (Default)

Scan the local project or fixture with automated verification and patch synthesis:

```bash
python3 bin/reposentinal tests/fixtures/cross_file_repo/ --topology
```

Options:
- `--no-verify`: Disable adversarial test generation and sandboxed verification.
- `--no-patch`: Disable automated patch generation (runs verification only).
- `--sandbox-backend {auto,docker,subprocess}`: Select preferred sandbox backend.

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
                    [--no-patch]
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
  --no-patch            Disable automated candidate patch generation and verification for confirmed bugs
```

---

## 🧪 Live Verification & Patch Output

```
======================================================================
   🛡️  REPO SENTINEL  |  Autonomous Bug Discovery Agent for GitHub   
======================================================================

Target:         tests/fixtures/cross_file_repo/
Provider:       MockProvider
Files Scanned:  3 files (32 lines of code)
Duration:       0.48s
Topology:       4 symbols (1 classes, 2 functions, 1 methods) | 2 inter-file dependencies

--- Repository-Aware Bug Hypotheses (2) ---

1.  CRITICAL  [Confirmed Bug] (High Conf) SQL Injection via Dynamic String Interpolation
2. [HIGH] [Confirmed Bug] (High Conf) Incorrect Assumption: Unchecked Return Value from `verify_jwt_token`

--- Adversarial Sandboxed Verification Evidence (2) ---

1. [REPRODUCED] Test TEST-HYP-CROSS-NULL-6 -> Target HYP-CROSS-NULL-6 (safe_subprocess, 0.09s)
   Reproduction: VULNERABILITY_REPRODUCED: TypeError: 'NoneType' object is not subscriptable

2. [REPRODUCED] Test TEST-HYP-SEC-SQL-12 -> Target HYP-SEC-SQL-12 (safe_subprocess, 0.10s)
   Reproduction: VULNERABILITY_REPRODUCED: Unescaped SQL injection probe found in query: EXECUTED...

--- Automated Candidate Patches & Verification (2) ---

1. [PATCH VERIFIED] PATCH-HYP-CROSS-NULL-6 -> Target: order_service.py (process_order_checkout)
   Objective:   Add null check after verify_jwt_token call to prevent unhandled TypeError
   Rationale:   The dependency `verify_jwt_token` can return None on invalid or expired authentication tokens. Adding an explicit guard returns a safe 401 response and prevents unhandled TypeError exceptions.
   Verification: Vulnerability Fixed: YES | Regression Tests: PASS (0.14s)
   Unified Diff:
     --- a/order_service.py
     +++ b/order_service.py
     @@ -4,6 +4,8 @@
      def process_order_checkout(token: str, order_id: str, amount: float):
          # 1. Cross-module bug: assumes verify_jwt_token always returns dict
          user = verify_jwt_token(token)
     +    if user is None:
     +        return {"error": "Unauthorized: invalid or missing authentication token", "status": 401}
          user_role = user["role"]
          user_id = user["user_id"]

2. [PATCH VERIFIED] PATCH-HYP-SEC-SQL-12 -> Target: order_service.py (process_order_checkout)
   Objective:   Enforce input parameter validation before SQL statement formatting
   Rationale:   Unescaped dynamic string interpolation into SQL commands allows query manipulation. Validating inputs against dangerous SQL punctuation rejects injection attempts prior to execution.
   Verification: Vulnerability Fixed: YES | Regression Tests: PASS (0.14s)
   Unified Diff:
     --- a/order_service.py
     +++ b/order_service.py
     @@ -9,5 +9,8 @@
      
          # 2. SQL injection
          gateway = DatabaseGateway()
     +    # Enforce strict input validation to prevent SQL injection bypass
     +    if any(c in str(order_id) for c in ("'", '"', ';', ' ')):
     +        return {"error": "Invalid order_id format", "status": 400}
          query = f"INSERT INTO orders (id, user_id, amount) VALUES ('{order_id}', {user_id}, {amount})"
          return gateway.execute_raw_sql(query)

----------------- Scan Summary Breakdown -----------------
   CRITICAL  : 2
   HIGH      : 1
   STATUS    : Confirmed=2 | Likely=0 | Potential=0
   RESEARCH  : Cross-File Interactions=1 (50%) | Symbol Mapped=2
   VERIFIED  : Confirmed=2 | Reproduced=2 | False Positives=0 | Inconclusive=0
   SANDBOX   : Backend=safe_subprocess | Repro Rate=100% | Avg Duration=0.098s
   PATCHES   : Verified=2 | Generated=2 | Regressions=0 | Fix Rate=100%
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
- Adversarial test generation, sandbox lifecycle, invariants tests (`tests/test_verification.py`)
- Patch generation, workspace isolation, dual-phase verification tests (`tests/test_patch.py`)

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

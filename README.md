# 🛡️ RepoSentinel

> **Autonomous Bug & Vulnerability Discovery Agent for GitHub Repositories**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-success.svg)](requirements.txt)

RepoSentinel is an autonomous pair-programming and security agent that inspects codebases, identifies critical vulnerabilities, unhandled edge cases, logic bugs, and resource leaks, and generates actionable remediation guidance with code fixes.

📖 **Documentation**: See [CURRENT_STATE.md](CURRENT_STATE.md) for the architectural assessment and [TODO.md](TODO.md) for the active engineering roadmap.

---

## 🌟 Key Features

- **Multi-Language Detection**: Scans Python, TypeScript, JavaScript, Go, Rust, Java, C/C++, Ruby, PHP, SQL, Shell, and more.
- **Repository-Aware Symbol Index & Topology**: AST-based symbol extraction (classes, functions, methods, parameters, docstrings) and automated inter-file dependency graph mapping (`--topology`).
- **Dual Engine Architecture**:
  - **Static Heuristic Engine**: Zero-network offline heuristics to catch command injections, hardcoded secrets, SQL injection formatting, swallowed exceptions, and unclosed resources.
  - **LLM Agent Engine**: Deep semantic reasoning powered by Google Gemini, OpenAI, DeepSeek, or local models via Ollama.
- **Zero Required External Dependencies**: Engineered on the Python standard library—runs anywhere Python 3.9+ is installed without `pip install` hurdles.
- **Remote & Local Ingestion**: Scan any local project or pass a remote GitHub repository URL directly (shallow clones and cleans up automatically).
- **Multiple Output Formats**:
  - 🎨 **Terminal Dashboard**: Colored cards with severity badges, file locations, line-level code previews, and topology statistics.
  - 📝 **Markdown Report**: Ready to post as a GitHub Issue or Pull Request comment.
  - 📊 **JSON Export**: Structured output designed for security pipelines and SIEM/dashboard ingestion.
- **CI/CD Integration**: Supports `--fail-on-bugs` flag to gate pull requests if `CRITICAL` or `HIGH` vulnerabilities are uncovered.

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/aaryanandhare7667-cloud/reposentinal.git
cd reposentinal
```

### 2. Run Instant Scan (Offline Heuristic Mode)

Scan the local project or any folder immediately with zero configuration:

```bash
python3 bin/reposentinal .
```

Scan a single file:

```bash
python3 bin/reposentinal tests/sample_vulnerable_code.py
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
                    [--fail-on-bugs]
                    [target]

Options:
  target                Local directory path, file path, or GitHub repository URL (default: .)
  --provider            LLM provider: mock, gemini, openai, ollama (auto-detected if keys are set)
  --api-key             API key (or set GEMINI_API_KEY / OPENAI_API_KEY environment variables)
  --model               Model name (e.g. gemini-1.5-flash, gpt-4o-mini, llama3)
  --base-url            Custom endpoint URL (useful for Ollama / vLLM / local proxies)
  --format              Output format: terminal, markdown, json, all (default: terminal)
  -o, --output          File destination to save Markdown or JSON report
  --max-files           Maximum source files to scan (default: 50)
  --workers             Number of concurrent worker threads (default: 4)
  --dry-run             Force offline heuristic analyzer without querying external APIs
  --fail-on-bugs        Return exit code 1 if CRITICAL or HIGH findings exist (for CI pipelines)
  --topology            Display detailed repository symbol index and dependency topology graph
```

---

## 🏗️ Architecture

```
                 +-----------------------+
                 | Target (Local/GitHub) |
                 +-----------+-----------+
                             |
                             v
                 +-----------------------+
                 |   Repository Scanner  | (Filter noise, ignore binaries/lockfiles)
                 +-----------+-----------+
                             |
                             v
                 +-----------------------+
                 | AST Symbol Indexer    | (Classes, Functions, Methods, Calls,
                 | & Topology Generator  |  and Inter-file Dependency Graph)
                 +-----------+-----------+
                             |
                             v
                 +-----------------------+
                 |   RepoSentinel Agent  | (Parallel ThreadPool Executor)
                 +-----------+-----------+
                             |
            +----------------+----------------+
            |                                 |
            v                                 v
+-----------------------+         +-----------------------+
| Static Heuristic      |         | LLM Semantic Engine   |
| Pattern Engine        |         | (Gemini / OpenAI /    |
| (Zero Network)        |         |  Ollama / DeepSeek)   |
+-----------+-----------+         +-----------+-----------+
            |                                 |
            +----------------+----------------+
                             |
                             v
                 +-----------------------+
                 | Deduplication & Score |
                 +-----------+-----------+
                             |
         +-------------------+-------------------+
         |                   |                   |
         v                   v                   v
+-----------------+ +-----------------+ +-----------------+
| ANSI Terminal   | | Markdown Report | | JSON Export     |
| Dashboard       | | (PR / Issue)    | | (CI / SIEM)     |
+-----------------+ +-----------------+ +-----------------+
```

---

## 🧪 Testing

Run the included test suite with standard Python `unittest`:

```bash
python3 -m unittest discover tests
```

---

## 🗺️ Roadmap

- [x] Initial Proof of Concept CLI (Zero-dependency core)
- [x] Static Heuristic Pattern Analyzer
- [x] Multi-LLM provider support (Gemini, OpenAI, Ollama)
- [x] Markdown and JSON report generators
- [x] AST-based Symbol Indexer & Dependency Topology (`--topology`)
- [ ] Attack Surface & Risk-Based File Prioritizer (Phase 3)
- [ ] Context-Enriched Cross-File Prompting (Phase 4)
- [ ] Two-Stage Autonomous Verification Agent (Phase 5)
- [ ] Automated Unified Diff Patch / PR Creator (Phase 6)
- [ ] GitHub Action workflow for automated PR reviews

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

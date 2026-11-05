import argparse
import os
import shutil
import sys
from pathlib import Path

from reposentinal.analyzer import RepoSentinelAgent
from reposentinal.models import Severity
from reposentinal.providers import get_provider
from reposentinal.reporter import TerminalReporter, MarkdownReporter, JSONReporter
from reposentinal.scanner import prepare_target, scan_repository
from reposentinal.indexer import build_repository_index
from reposentinal.hypothesis_engine import RuleBasedHypothesisEngine, LLMHypothesisEngine


def parse_args():
    parser = argparse.ArgumentParser(
        prog="reposentinal",
        description="🛡️ RepoSentinel: Autonomous Bug & Vulnerability Discovery Agent for Repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  reposentinal .                                # Scan current directory with offline heuristic agent
  reposentinal /path/to/project --dry-run       # Run mock scan on local project
  reposentinal https://github.com/user/repo     # Clone and scan a remote GitHub repository
  reposentinal . --provider gemini --api-key $KEY --format markdown --output report.md
  reposentinal . --provider ollama --model llama3 --base-url http://localhost:11434/v1
        """,
    )

    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Local directory path, file path, or GitHub repository URL (default: .)",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "gemini", "openai", "ollama"],
        default=None,
        help="LLM provider (default: auto-detects from environment keys, or 'mock')",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for Gemini or OpenAI (can also use GEMINI_API_KEY / OPENAI_API_KEY env vars)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model identifier (e.g., gemini-1.5-flash, gpt-4o-mini, llama3)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Custom base URL for OpenAI-compatible APIs or Ollama (e.g., http://localhost:11434/v1)",
    )
    parser.add_argument(
        "--format",
        choices=["terminal", "markdown", "json", "all"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="File path to save Markdown or JSON report",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=50,
        help="Maximum source files to scan (default: 50)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of concurrent worker threads (default: 4)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force offline mock/heuristic mode without sending requests to external LLMs",
    )
    parser.add_argument(
        "--fail-on-bugs",
        action="store_true",
        help="Exit with non-zero exit code if CRITICAL or HIGH severity bugs are found (useful for CI/CD)",
    )
    parser.add_argument(
        "--topology",
        action="store_true",
        help="Display detailed repository symbol index and dependency topology graph",
    )

    return parser.parse_args()


def resolve_provider_config(args):
    """Detect and select best provider based on args and environment."""
    if args.dry_run:
        return "mock", None, args.model, args.base_url

    provider_name = args.provider
    api_key = args.api_key

    # Check environment variables if not specified
    if not provider_name:
        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            provider_name = "gemini"
            api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        elif os.environ.get("OPENAI_API_KEY"):
            provider_name = "openai"
            api_key = api_key or os.environ.get("OPENAI_API_KEY")
        else:
            provider_name = "mock"

    if provider_name == "gemini" and not api_key:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if provider_name in ("openai", "ollama") and not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    return provider_name, api_key, args.model, args.base_url


def main():
    args = parse_args()

    provider_name, api_key, model, base_url = resolve_provider_config(args)
    provider = get_provider(
        name=provider_name,
        api_key=api_key,
        model=model,
        base_url=base_url,
    )

    target_str = args.target
    cleanup_dir = None

    try:
        print(f"📦 Resolving target: {target_str}")
        target_path, cleanup_dir = prepare_target(target_str)

        print(f"🔎 Scanning repository files (max {args.max_files})...")
        files = scan_repository(target_path, max_files=args.max_files)
        print(f"✅ Discovered {len(files)} source files to analyze.")

        if not files:
            print("⚠️ No supported source files found to scan.")
            return

        def on_progress(file_ctx, current, total):
            pct = int((current / total) * 100)
            sys.stdout.write(f"\r🤖 Analyzing [{current}/{total}] ({pct}%) -> {file_ctx.rel_path[:40]:<40}")
            sys.stdout.flush()

        if provider_name == "mock" or args.dry_run:
            hyp_engine = RuleBasedHypothesisEngine()
        else:
            hyp_engine = LLMHypothesisEngine(
                provider_name=provider_name,
                api_key=api_key,
                model=model,
                base_url=base_url,
            )

        print(f"🚀 Launching Sentinel Agent with {type(provider).__name__} ({args.workers} workers)...")
        agent = RepoSentinelAgent(
            provider=provider,
            max_workers=args.workers,
            on_file_scanned=on_progress,
            hypothesis_engine=hyp_engine,
        )

        summary = agent.analyze(target_name=target_str, files=files)
        # Clear progress line
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

        # Render outputs
        if args.format in ("terminal", "all"):
            TerminalReporter.render(summary)

        if args.topology:
            repo_index = build_repository_index(files)
            print("🕸️  Repository Dependency Graph & Symbol Map:")
            for node in sorted(repo_index.graph.nodes):
                deps = repo_index.graph.edges.get(node, set())
                exts = repo_index.graph.external_dependencies.get(node, set())
                file_syms = repo_index.get_file_symbols(node)
                classes = [s.name for s in file_syms if s.kind == "CLASS"]
                functions = [s.name for s in file_syms if s.kind == "FUNCTION"]
                print(f"  📄 {node}")
                if classes:
                    print(f"     ├── Classes: {', '.join(classes)}")
                if functions:
                    print(f"     ├── Functions: {', '.join(functions)}")
                if deps:
                    print(f"     ├── Internal Imports: {', '.join(sorted(deps))}")
                if exts:
                    print(f"     └── External Deps: {', '.join(sorted(exts))}")
            print()

        if args.output:
            out_path = Path(args.output).resolve()
            out_ext = out_path.suffix.lower()

            if out_ext == ".json" or args.format == "json":
                content = JSONReporter.render(summary)
            else:
                content = MarkdownReporter.render(summary)

            out_path.write_text(content, encoding="utf-8")
            print(f"📄 Report written to: {out_path}")
        elif args.format == "markdown":
            print(MarkdownReporter.render(summary))
        elif args.format == "json":
            print(JSONReporter.render(summary))

        if args.fail_on_bugs and (summary.critical_count > 0 or summary.high_count > 0):
            print("🚨 Exiting with error code 1 due to critical/high findings (--fail-on-bugs enabled).")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nScan aborted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error during execution: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if cleanup_dir and os.path.exists(cleanup_dir):
            shutil.rmtree(cleanup_dir, ignore_errors=True)


if __name__ == "__main__":
    main()

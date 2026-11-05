import json
from typing import Dict
from reposentinal.models import ScanSummary, Severity, BugFinding

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BG_RED = "\033[41m"
BG_YELLOW = "\033[43m"


def get_severity_badge(severity: Severity) -> str:
    if severity == Severity.CRITICAL:
        return f"{BG_RED}{WHITE}{BOLD} CRITICAL {RESET}"
    elif severity == Severity.HIGH:
        return f"{RED}{BOLD}[HIGH]{RESET}"
    elif severity == Severity.MEDIUM:
        return f"{YELLOW}{BOLD}[MEDIUM]{RESET}"
    elif severity == Severity.LOW:
        return f"{CYAN}[LOW]{RESET}"
    else:
        return f"{BLUE}[INFO]{RESET}"


class TerminalReporter:
    @staticmethod
    def print_banner():
        print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
        print(f"{BOLD}{WHITE}   🛡️  REPO SENTINEL  |  Autonomous Bug Discovery Agent for GitHub   {RESET}")
        print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

    @staticmethod
    def render(summary: ScanSummary):
        TerminalReporter.print_banner()

        print(f"{BOLD}Target:{RESET}         {summary.target}")
        print(f"{BOLD}Provider:{RESET}       {summary.provider_used}")
        print(f"{BOLD}Files Scanned:{RESET}  {summary.scanned_files} files ({summary.total_lines:,} lines of code)")
        print(f"{BOLD}Duration:{RESET}       {summary.duration_seconds:.2f}s")
        if summary.topology_summary:
            top = summary.topology_summary
            print(f"{BOLD}Topology:{RESET}       {top.get('total_symbols', 0)} symbols ({top.get('classes_count', 0)} classes, {top.get('functions_count', 0)} functions, {top.get('methods_count', 0)} methods) | {top.get('internal_edges_count', 0)} inter-file dependencies")
        print()

        if not summary.findings:
            print(f"{GREEN}{BOLD}✨ All clear! No bugs or security flaws identified.{RESET}\n")
            return

        print(f"{BOLD}{MAGENTA}--- Discovered Issues ({len(summary.findings)}) ---{RESET}\n")

        for idx, finding in enumerate(summary.findings, start=1):
            badge = get_severity_badge(finding.severity)
            loc = f"{finding.file_path}:{finding.line_start}"
            if finding.line_end > finding.line_start:
                loc += f"-{finding.line_end}"

            print(f"{BOLD}{idx}. {badge} {WHITE}{finding.title}{RESET}")
            print(f"   {DIM}Location:{RESET}    {CYAN}{loc}{RESET}  ({DIM}{finding.category}{RESET})")
            print(f"   {DIM}Description:{RESET} {finding.description}")

            if finding.code_snippet:
                snippet_preview = finding.code_snippet.strip()
                if len(snippet_preview) > 120:
                    snippet_preview = snippet_preview[:117] + "..."
                print(f"   {DIM}Code:{RESET}        {YELLOW}`{snippet_preview}`{RESET}")

            if finding.remediation:
                print(f"   {DIM}Remediation:{RESET} {GREEN}{finding.remediation}{RESET}")

            print()

        # Summary Breakdown
        print(f"{BOLD}----------------- Scan Summary Breakdown -----------------{RESET}")
        print(f"  {BG_RED}{WHITE} CRITICAL {RESET} : {summary.critical_count}")
        print(f"  {RED}{BOLD} HIGH     {RESET} : {summary.high_count}")
        print(f"  {YELLOW}{BOLD} MEDIUM   {RESET} : {summary.medium_count}")
        print(f"  {CYAN} LOW      {RESET} : {summary.low_count}")
        print(f"  {BOLD} TOTAL    {RESET} : {len(summary.findings)}")
        print(f"{BOLD}----------------------------------------------------------{RESET}\n")


class MarkdownReporter:
    @staticmethod
    def render(summary: ScanSummary) -> str:
        md = []
        md.append("# 🛡️ RepoSentinel Bug Discovery Report\n")
        md.append(f"- **Target**: `{summary.target}`")
        md.append(f"- **Provider**: `{summary.provider_used}`")
        md.append(f"- **Files Scanned**: {summary.scanned_files} ({summary.total_lines:,} lines)")
        md.append(f"- **Duration**: {summary.duration_seconds:.2f}s")
        if summary.topology_summary:
            top = summary.topology_summary
            md.append(f"- **Codebase Topology**: {top.get('total_symbols', 0)} symbols ({top.get('classes_count', 0)} classes, {top.get('functions_count', 0)} functions, {top.get('methods_count', 0)} methods) | {top.get('internal_edges_count', 0)} internal dependencies")
        md.append("")

        md.append("## 📊 Summary\n")
        md.append("| Severity | Count |")
        md.append("|---|---|")
        md.append(f"| 🚨 Critical | {summary.critical_count} |")
        md.append(f"| 🔴 High | {summary.high_count} |")
        md.append(f"| 🟡 Medium | {summary.medium_count} |")
        md.append(f"| 🔵 Low | {summary.low_count} |")
        md.append(f"| **Total** | **{len(summary.findings)}** |\n")

        if not summary.findings:
            md.append("✅ **No bugs or security flaws were found.**\n")
            return "\n".join(md)

        md.append("## 🔍 Discovered Issues\n")
        for idx, f in enumerate(summary.findings, start=1):
            sev_emoji = {
                Severity.CRITICAL: "🚨 CRITICAL",
                Severity.HIGH: "🔴 HIGH",
                Severity.MEDIUM: "🟡 MEDIUM",
                Severity.LOW: "🔵 LOW",
                Severity.INFO: "ℹ️ INFO",
            }.get(f.severity, "⚠️")

            loc = f"{f.file_path}#L{f.line_start}"
            if f.line_end > f.line_start:
                loc += f"-L{f.line_end}"

            md.append(f"### {idx}. [{sev_emoji}] {f.title}\n")
            md.append(f"- **File**: `{loc}`")
            md.append(f"- **Category**: `{f.category}`")
            md.append(f"\n**Description:**\n{f.description}\n")

            if f.code_snippet:
                md.append(f"```\n{f.code_snippet}\n```\n")

            if f.remediation:
                md.append(f"**Suggested Remediation:**\n{f.remediation}\n")

            md.append("---\n")

        md.append("\n*Generated autonomously by [RepoSentinel](https://github.com/aaryanandhare7667-cloud/reposentinal)*\n")
        return "\n".join(md)


class JSONReporter:
    @staticmethod
    def render(summary: ScanSummary) -> str:
        return json.dumps(summary.to_dict(), indent=2)

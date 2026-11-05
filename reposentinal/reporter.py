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
def get_status_badge(status) -> str:
    status_val = status.value if hasattr(status, "value") else str(status)
    if status_val == "Confirmed Bug":
        return f"{GREEN}{BOLD}[Confirmed Bug]{RESET}"
    elif status_val == "Likely Bug":
        return f"{MAGENTA}{BOLD}[Likely Bug]{RESET}"
    else:
        return f"{BLUE}[Potential Bug]{RESET}"


def get_confidence_badge(conf) -> str:
    conf_val = conf.value if hasattr(conf, "value") else str(conf)
    if conf_val == "HIGH":
        return f"{GREEN}(High Conf){RESET}"
    elif conf_val == "MEDIUM":
        return f"{YELLOW}(Med Conf){RESET}"
    else:
        return f"{DIM}(Low Conf){RESET}"


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

        # If hypotheses are available, render hypotheses
        if summary.hypotheses:
            print(f"{BOLD}{MAGENTA}--- Repository-Aware Bug Hypotheses ({len(summary.hypotheses)}) ---{RESET}\n")
            for idx, hyp in enumerate(summary.hypotheses, start=1):
                sev_badge = get_severity_badge(hyp.severity)
                status_badge = get_status_badge(hyp.status)
                conf_badge = get_confidence_badge(hyp.confidence)

                loc = f"{hyp.affected_file}:{hyp.line_start}"
                if hyp.line_end > hyp.line_start:
                    loc += f"-{hyp.line_end}"

                sym_info = f" [Symbol: {CYAN}{hyp.affected_symbol}{RESET}]" if hyp.affected_symbol else ""

                print(f"{BOLD}{idx}. {sev_badge} {status_badge} {conf_badge} {WHITE}{hyp.title}{RESET}")
                print(f"   {DIM}Location:{RESET}    {CYAN}{loc}{RESET}{sym_info}  ({DIM}{hyp.category}{RESET})")
                print(f"   {DIM}Explanation:{RESET} {hyp.explanation}")

                if hyp.reasoning:
                    print(f"   {DIM}Reasoning:{RESET}   {YELLOW}{hyp.reasoning}{RESET}")

                if hyp.related_symbols:
                    print(f"   {DIM}Related:{RESET}     {', '.join(hyp.related_symbols)}")

                if hyp.code_snippet:
                    snippet_preview = hyp.code_snippet.strip()
                    if len(snippet_preview) > 120:
                        snippet_preview = snippet_preview[:117] + "..."
                    print(f"   {DIM}Code:{RESET}        `{snippet_preview}`")

                if hyp.suggested_test:
                    print(f"   {DIM}Test Case:{RESET}   {CYAN}{hyp.suggested_test}{RESET}")

                if hyp.remediation:
                    print(f"   {DIM}Remediation:{RESET} {GREEN}{hyp.remediation}{RESET}")

                print()

        elif summary.findings:
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
        else:
            print(f"{GREEN}{BOLD}✨ All clear! No bugs or security flaws identified.{RESET}\n")
            return

        # Summary Breakdown
        print(f"{BOLD}----------------- Scan Summary Breakdown -----------------{RESET}")
        print(f"  {BG_RED}{WHITE} CRITICAL {RESET} : {summary.critical_count}")
        print(f"  {RED}{BOLD} HIGH     {RESET} : {summary.high_count}")
        print(f"  {YELLOW}{BOLD} MEDIUM   {RESET} : {summary.medium_count}")
        print(f"  {CYAN} LOW      {RESET} : {summary.low_count}")
        if summary.metrics:
            m = summary.metrics
            print(f"  {BOLD} STATUS   {RESET} : Likely={m.get('by_status', {}).get('Likely Bug', 0)} | Potential={m.get('by_status', {}).get('Potential Bug', 0)} | Confirmed={m.get('by_status', {}).get('Confirmed Bug', 0)}")
            print(f"  {BOLD} RESEARCH {RESET} : Cross-File Interactions={m.get('cross_file_count', 0)} ({int(m.get('cross_file_ratio', 0)*100)}%) | Symbol Mapped={m.get('symbol_mapped_count', 0)}")
        print(f"  {BOLD} TOTAL    {RESET} : {len(summary.hypotheses or summary.findings)}")
        print(f"{BOLD}----------------------------------------------------------{RESET}\n")


class MarkdownReporter:
    @staticmethod
    def render(summary: ScanSummary) -> str:
        md = []
        md.append("# 🛡️ RepoSentinel Bug Discovery & Hypothesis Report\n")
        md.append(f"- **Target**: `{summary.target}`")
        md.append(f"- **Provider**: `{summary.provider_used}`")
        md.append(f"- **Files Scanned**: {summary.scanned_files} ({summary.total_lines:,} lines)")
        md.append(f"- **Duration**: {summary.duration_seconds:.2f}s")
        if summary.topology_summary:
            top = summary.topology_summary
            md.append(f"- **Codebase Topology**: {top.get('total_symbols', 0)} symbols ({top.get('classes_count', 0)} classes, {top.get('functions_count', 0)} functions, {top.get('methods_count', 0)} methods) | {top.get('internal_edges_count', 0)} internal dependencies")
        md.append("")

        md.append("## 📊 Summary\n")
        md.append("| Metric | Count |")
        md.append("|---|---|")
        md.append(f"| 🚨 Critical | {summary.critical_count} |")
        md.append(f"| 🔴 High | {summary.high_count} |")
        md.append(f"| 🟡 Medium | {summary.medium_count} |")
        md.append(f"| 🔵 Low | {summary.low_count} |")

        if summary.metrics:
            m = summary.metrics
            md.append(f"| 🔍 Likely Bugs | {m.get('by_status', {}).get('Likely Bug', 0)} |")
            md.append(f"| 💡 Potential Bugs | {m.get('by_status', {}).get('Potential Bug', 0)} |")
            md.append(f"| 🌐 Cross-Module Interactions | {m.get('cross_file_count', 0)} |")

        items_count = len(summary.hypotheses or summary.findings)
        md.append(f"| **Total Hypotheses** | **{items_count}** |\n")

        if not items_count:
            md.append("✅ **No bugs or security flaws were found.**\n")
            return "\n".join(md)

        if summary.hypotheses:
            md.append("## 🔍 Repository-Aware Bug Hypotheses\n")
            for idx, hyp in enumerate(summary.hypotheses, start=1):
                sev_emoji = {
                    Severity.CRITICAL: "🚨 CRITICAL",
                    Severity.HIGH: "🔴 HIGH",
                    Severity.MEDIUM: "🟡 MEDIUM",
                    Severity.LOW: "🔵 LOW",
                    Severity.INFO: "ℹ️ INFO",
                }.get(hyp.severity, "⚠️")

                loc = f"{hyp.affected_file}#L{hyp.line_start}"
                if hyp.line_end > hyp.line_start:
                    loc += f"-L{hyp.line_end}"

                sym_str = f" (`{hyp.affected_symbol}`)" if hyp.affected_symbol else ""
                status_str = f"**[{hyp.status.value}]**" if hasattr(hyp.status, "value") else f"**[{hyp.status}]**"
                conf_str = f"(Confidence: {hyp.confidence.value})" if hasattr(hyp.confidence, "value") else ""

                md.append(f"### {idx}. [{sev_emoji}] {status_str} {hyp.title} {conf_str}\n")
                md.append(f"- **Location**: `{loc}`{sym_str}")
                md.append(f"- **Category**: `{hyp.category}`")
                md.append(f"\n**Explanation:**\n{hyp.explanation}\n")

                if hyp.reasoning:
                    md.append(f"**Cross-Module Evidence & Reasoning:**\n{hyp.reasoning}\n")

                if hyp.related_symbols:
                    md.append(f"**Related Symbols:** {', '.join([f'`{s}`' for s in hyp.related_symbols])}\n")

                if hyp.code_snippet:
                    md.append(f"```python\n{hyp.code_snippet}\n```\n")

                if hyp.suggested_test:
                    md.append(f"**🧪 Suggested Way to Test Hypothesis:**\n{hyp.suggested_test}\n")

                if hyp.remediation:
                    md.append(f"**Suggested Remediation:**\n{hyp.remediation}\n")

                md.append("---\n")
        else:
            md.append("## 🔍 Discovered Issues\n")
            for idx, f in enumerate(summary.findings, start=1):
                loc = f"{f.file_path}#L{f.line_start}"
                if f.line_end > f.line_start:
                    loc += f"-L{f.line_end}"
                md.append(f"### {idx}. [{f.severity.value}] {f.title}\n")
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

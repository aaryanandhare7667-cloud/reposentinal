import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Optional
from reposentinal.models import BugFinding, FileContext, ScanSummary, Severity
from reposentinal.providers import BaseLLMProvider
from reposentinal.indexer import build_repository_index, SymbolKind

SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


class RepoSentinelAgent:
    """
    Core bug discovery orchestrator.
    Manages concurrency, file dispatching, deduplication, and result aggregation.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        max_workers: int = 4,
        on_file_scanned: Optional[Callable[[FileContext, int, int], None]] = None,
    ):
        self.provider = provider
        self.max_workers = max_workers
        self.on_file_scanned = on_file_scanned

    def analyze(self, target_name: str, files: List[FileContext]) -> ScanSummary:
        start_time = time.time()
        all_findings: List[BugFinding] = []
        total_lines = sum(f.line_count for f in files)

        if not files:
            return ScanSummary(
                target=target_name,
                scanned_files=0,
                total_lines=0,
                findings=[],
                duration_seconds=0.0,
                provider_used=type(self.provider).__name__,
            )

        completed_count = 0
        total_files = len(files)

        with ThreadPoolExecutor(max_workers=min(self.max_workers, total_files)) as executor:
            future_to_file = {
                executor.submit(self.provider.analyze_file, file_ctx): file_ctx
                for file_ctx in files
            }

            for future in as_completed(future_to_file):
                file_ctx = future_to_file[future]
                completed_count += 1
                try:
                    findings = future.result()
                    all_findings.extend(findings)
                except Exception:
                    pass

                if self.on_file_scanned:
                    self.on_file_scanned(file_ctx, completed_count, total_files)

        # Deduplicate findings
        unique_findings: List[BugFinding] = []
        seen_keys = set()
        for f in all_findings:
            key = (f.file_path, f.line_start, f.title.strip().lower())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_findings.append(f)

        # Sort by severity
        unique_findings.sort(key=lambda x: SEVERITY_ORDER.get(x.severity, 99))

        # Build repository symbol index and dependency topology
        repo_index = build_repository_index(files)
        topology_summary = {
            "total_symbols": len(repo_index.symbols),
            "classes_count": sum(1 for s in repo_index.symbols if s.kind == SymbolKind.CLASS),
            "functions_count": sum(1 for s in repo_index.symbols if s.kind == SymbolKind.FUNCTION),
            "methods_count": sum(1 for s in repo_index.symbols if s.kind == SymbolKind.METHOD),
            "internal_edges_count": sum(len(v) for v in repo_index.graph.edges.values()),
            "external_dependencies_count": sum(len(v) for v in repo_index.graph.external_dependencies.values()),
        }

        duration = time.time() - start_time
        return ScanSummary(
            target=target_name,
            scanned_files=len(files),
            total_lines=total_lines,
            findings=unique_findings,
            duration_seconds=duration,
            provider_used=type(self.provider).__name__,
            topology_summary=topology_summary,
        )

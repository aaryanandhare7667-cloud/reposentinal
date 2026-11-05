import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any, Tuple
from backend.models.models import BugFinding, FileContext, ScanSummary, Severity
from backend.analysis.providers import BaseLLMProvider
from backend.analysis.indexer import build_repository_index, SymbolKind
from backend.analysis.context import RepositoryContextBuilder
from backend.models.hypothesis import BugHypothesis, HypothesisEvaluationMetrics, Confidence
from backend.analysis.hypothesis_engine import BaseHypothesisEngine, RuleBasedHypothesisEngine
from backend.verification.verifier import HypothesisVerifier
from backend.patching.patch_verifier import PatchVerifier

SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}

CONFIDENCE_ORDER = {
    Confidence.HIGH: 0,
    Confidence.MEDIUM: 1,
    Confidence.LOW: 2,
}


class RepoSentinelAgent:
    """
    Core bug discovery orchestrator.
    Manages concurrency, repository context synthesis, bug hypothesis generation,
    adversarial test generation, sandboxed verification, patch generation, patch verification,
    deduplication, and research evaluation metrics.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        max_workers: int = 4,
        on_file_scanned: Optional[Callable[[FileContext, int, int], None]] = None,
        hypothesis_engine: Optional[BaseHypothesisEngine] = None,
        verifier: Optional[HypothesisVerifier] = None,
        verify: bool = False,
        patch_verifier: Optional[PatchVerifier] = None,
        patch: bool = False,
        target_root_dir: Optional[Path] = None,
    ):
        self.provider = provider
        self.max_workers = max_workers
        self.on_file_scanned = on_file_scanned
        self.hypothesis_engine = hypothesis_engine or RuleBasedHypothesisEngine()
        self.verifier = verifier or HypothesisVerifier()
        self.verify = verify
        self.patch_verifier = patch_verifier or PatchVerifier()
        self.patch = patch
        self.target_root_dir = target_root_dir

    def analyze(
        self,
        target_name: str,
        files: List[FileContext],
        root_dir: Optional[Path] = None,
    ) -> ScanSummary:
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

        # 1. Build repository symbol index and dependency topology first
        repo_index = build_repository_index(files)
        context_builder = RepositoryContextBuilder(repo_index)

        all_hypotheses: List[BugHypothesis] = []

        def _scan_worker(file_ctx: FileContext):
            context = context_builder.build_context(file_ctx)
            findings = self.provider.analyze_file(file_ctx)
            try:
                hypotheses = self.hypothesis_engine.generate_hypotheses(file_ctx, context)
            except Exception:
                hypotheses = []
            return findings, hypotheses

        with ThreadPoolExecutor(max_workers=min(self.max_workers, total_files)) as executor:
            future_to_file = {
                executor.submit(_scan_worker, file_ctx): file_ctx
                for file_ctx in files
            }

            for future in as_completed(future_to_file):
                file_ctx = future_to_file[future]
                completed_count += 1
                try:
                    f_list, h_list = future.result()
                    all_findings.extend(f_list)
                    all_hypotheses.extend(h_list)
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

        # Deduplicate hypotheses
        unique_hypotheses: List[BugHypothesis] = []
        seen_hyp_keys = set()
        for h in all_hypotheses:
            key = (h.affected_file, h.line_start, h.title.strip().lower())
            if key not in seen_hyp_keys:
                seen_hyp_keys.add(key)
                unique_hypotheses.append(h)

        # Execute adversarial sandboxed verification if enabled
        evidence_list = []
        verification_metrics = None
        eff_root = root_dir or self.target_root_dir
        if not eff_root:
            if Path(target_name).exists() and Path(target_name).is_dir():
                eff_root = Path(target_name).resolve()
            elif files:
                eff_root = Path(files[0].abs_path).parent.resolve()
            else:
                eff_root = Path(".").resolve()
        else:
            eff_root = Path(eff_root).resolve()

        if self.verify and unique_hypotheses:
            unique_hypotheses, evidence_list, verification_metrics = self.verifier.verify_all(
                unique_hypotheses, eff_root
            )

        # Execute automated patch generation & verification if enabled
        patches = []
        patch_results = []
        patch_metrics = None
        if self.patch and unique_hypotheses and evidence_list:
            patches, patch_results, patch_metrics = self.patch_verifier.verify_all_patches(
                unique_hypotheses, evidence_list, eff_root
            )

        # Ensure every hypothesis has a corresponding BugFinding for backwards compatibility
        for h in unique_hypotheses:
            key = (h.affected_file, h.line_start, h.title.strip().lower())
            if key not in seen_keys:
                seen_keys.add(key)
                unique_findings.append(
                    BugFinding(
                        file_path=h.affected_file,
                        line_start=h.line_start,
                        line_end=h.line_end,
                        title=f"[{h.status.value}] {h.title}",
                        category=h.category,
                        severity=h.severity,
                        description=f"{h.explanation}\n\nEvidence & Reasoning:\n{h.reasoning}",
                        remediation=f"{h.remediation}\n\nSuggested Test:\n{h.suggested_test}",
                        code_snippet=h.code_snippet,
                    )
                )

        # Sort findings and hypotheses by severity and confidence
        unique_findings.sort(key=lambda x: SEVERITY_ORDER.get(x.severity, 99))
        unique_hypotheses.sort(
            key=lambda h: (SEVERITY_ORDER.get(h.severity, 99), CONFIDENCE_ORDER.get(h.confidence, 99))
        )

        metrics = HypothesisEvaluationMetrics.calculate(unique_hypotheses)

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
            hypotheses=unique_hypotheses,
            metrics=metrics.to_dict(),
            verification_evidence=evidence_list,
            verification_metrics=verification_metrics,
            patches=patches,
            patch_results=patch_results,
            patch_metrics=patch_metrics,
        )

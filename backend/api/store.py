import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from backend.models.models import ScanSummary
from backend.models.hypothesis import BugHypothesis, BugStatus
from backend.models.patch_models import (
    GeneratedPatch,
    PatchVerificationResult,
    PatchVerificationStatus,
)
from backend.verification.verification import VerificationEvidence
from backend.verification.test_generator import AdversarialTest


class ScanRecord:
    """Represents a single scan execution job and all its generated artifacts."""

    def __init__(
        self,
        scan_id: str,
        target_path: str,
        provider: str = "mock",
        sandbox_backend: str = "subprocess",
        max_files: int = 50,
        verify: bool = True,
        patch: bool = True,
    ):
        self.scan_id = scan_id
        self.target_path = target_path
        self.provider = provider
        self.sandbox_backend = sandbox_backend
        self.max_files = max_files
        self.verify = verify
        self.patch = patch
        self.status = "QUEUED"  # QUEUED, RUNNING, COMPLETED, FAILED
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.completed_at: Optional[str] = None
        self.duration_seconds: float = 0.0
        self.progress: Dict[str, Any] = {
            "current": 0,
            "total": 0,
            "currentFile": "",
            "status": "QUEUED",
        }
        self.summary: Optional[ScanSummary] = None
        self.error: Optional[str] = None
        self.adversarial_tests: Dict[str, AdversarialTest] = {}
        self.target_root_dir: Optional[Path] = None

    def update_progress(self, current: int, total: int, current_file: str):
        self.status = "RUNNING"
        self.progress = {
            "current": current,
            "total": total,
            "currentFile": current_file,
            "status": "RUNNING",
        }

    def complete(
        self,
        summary: ScanSummary,
        adversarial_tests: Optional[Dict[str, AdversarialTest]] = None,
        target_root_dir: Optional[Path] = None,
    ):
        self.status = "COMPLETED"
        self.summary = summary
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.duration_seconds = summary.duration_seconds
        self.progress["status"] = "COMPLETED"
        if adversarial_tests:
            self.adversarial_tests.update(adversarial_tests)
        if target_root_dir:
            self.target_root_dir = target_root_dir

    def fail(self, error_message: str):
        self.status = "FAILED"
        self.error = error_message
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.progress["status"] = "FAILED"

    def to_summary_dict(self) -> Dict[str, Any]:
        """Compact summary representation for GET /api/scans."""
        modules_scanned = 0
        hyp_count = 0
        confirmed_count = 0
        verified_patches_count = 0
        duration_ms = int(self.duration_seconds * 1000)

        if self.summary:
            modules_scanned = self.summary.scanned_files
            hyp_count = len(self.summary.hypotheses)
            confirmed_count = sum(
                1 for h in self.summary.hypotheses if h.status == BugStatus.CONFIRMED
            )
            verified_patches_count = sum(
                1
                for r in self.summary.patch_results
                if r.status == PatchVerificationStatus.VERIFIED
            )

        return {
            "id": self.scan_id,
            "targetRepo": self.target_path,
            "status": self.status,
            "durationMs": duration_ms,
            "modulesScanned": modules_scanned,
            "hypothesesCount": hyp_count,
            "confirmedFindingsCount": confirmed_count,
            "verifiedPatchesCount": verified_patches_count,
            "createdAt": self.created_at,
            "completedAt": self.completed_at,
            "progress": self.progress,
            "error": self.error,
        }

    def to_detail_dict(self) -> Dict[str, Any]:
        """Full scan detail representation for GET /api/scans/:id."""
        data = self.to_summary_dict()
        data["provider"] = self.provider
        data["sandboxBackend"] = self.sandbox_backend

        if self.summary:
            data.update(self.summary.to_dict())
            data["id"] = self.scan_id
            data["targetRepo"] = self.target_path
            data["status"] = self.status
            data["progress"] = self.progress
            data["createdAt"] = self.created_at
            data["completedAt"] = self.completed_at
            data["error"] = self.error
            data["scannedFiles"] = self.summary.scanned_files
            data["totalLines"] = self.summary.total_lines
            data["durationSeconds"] = round(self.summary.duration_seconds, 2)
        else:
            data["findings"] = []
            data["hypotheses"] = []
            data["verificationEvidence"] = []
            data["patches"] = []
            data["patchResults"] = []
            data["counts"] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0, "total": 0}

        return data


class ScanStore:
    """
    Thread-safe in-memory store for scans and their analytical artifacts.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._scans: Dict[str, ScanRecord] = {}

    def create_scan(
        self,
        target_path: str,
        provider: str = "mock",
        sandbox_backend: str = "subprocess",
        max_files: int = 50,
        verify: bool = True,
        patch: bool = True,
    ) -> ScanRecord:
        with self._lock:
            # Deterministic scan ID format: SCAN-YYYYMMDD-HHMMSS-XXXX
            now_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            scan_id = f"SCAN-{now_str}-{len(self._scans) + 1:03d}"
            record = ScanRecord(
                scan_id=scan_id,
                target_path=target_path,
                provider=provider,
                sandbox_backend=sandbox_backend,
                max_files=max_files,
                verify=verify,
                patch=patch,
            )
            self._scans[scan_id] = record
            return record

    def get_scan(self, scan_id: str) -> Optional[ScanRecord]:
        with self._lock:
            return self._scans.get(scan_id)

    def list_scans(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            # Sort newest first
            sorted_records = sorted(
                self._scans.values(),
                key=lambda s: s.created_at,
                reverse=True,
            )
            return [s.to_summary_dict() for s in sorted_records[:limit]]

    def get_latest_scan(self) -> Optional[ScanRecord]:
        with self._lock:
            if not self._scans:
                return None
            return sorted(
                self._scans.values(),
                key=lambda s: s.created_at,
                reverse=True,
            )[0]

    def update_progress(self, scan_id: str, current: int, total: int, current_file: str):
        with self._lock:
            scan = self._scans.get(scan_id)
            if scan:
                scan.update_progress(current, total, current_file)

    def complete_scan(
        self,
        scan_id: str,
        summary: ScanSummary,
        adversarial_tests: Optional[Dict[str, AdversarialTest]] = None,
        target_root_dir: Optional[Path] = None,
    ):
        with self._lock:
            scan = self._scans.get(scan_id)
            if scan:
                scan.complete(summary, adversarial_tests, target_root_dir)

    def fail_scan(self, scan_id: str, error_message: str):
        with self._lock:
            scan = self._scans.get(scan_id)
            if scan:
                scan.fail(error_message)

    def get_findings(
        self,
        scan_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Flatten findings/hypotheses across stored scans matching filters."""
        with self._lock:
            scans_to_check = (
                [self._scans[scan_id]]
                if scan_id and scan_id in self._scans
                else list(self._scans.values())
            )

            all_findings: List[Dict[str, Any]] = []

            for scan in scans_to_check:
                if not scan.summary:
                    continue

                # Map verification evidence by hypothesis_id
                evidence_by_hyp = {
                    e.hypothesis_id: e for e in scan.summary.verification_evidence
                }
                # Map patches by hypothesis_id
                patches_by_hyp = {
                    p.hypothesis_id: p for p in scan.summary.patches
                }

                for hyp in scan.summary.hypotheses:
                    # Apply severity filter
                    if severity and hyp.severity.value.upper() != severity.upper():
                        continue

                    # Apply status filter (e.g. CONFIRMED, LIKELY, POTENTIAL)
                    if status:
                        hyp_stat = hyp.status.value.upper()
                        filter_stat = status.upper()
                        if filter_stat not in hyp_stat:
                            continue

                    evidence = evidence_by_hyp.get(hyp.hypothesis_id)
                    patch = patches_by_hyp.get(hyp.hypothesis_id)

                    finding_dict = {
                        "id": hyp.hypothesis_id,
                        "scanId": scan.scan_id,
                        "file": hyp.affected_file,
                        "lineStart": hyp.line_start,
                        "lineEnd": hyp.line_end,
                        "symbol": hyp.affected_symbol or "",
                        "title": hyp.title,
                        "severity": hyp.severity.value,
                        "status": hyp.status.value,
                        "category": hyp.category,
                        "confidence": hyp.confidence.value,
                        "description": hyp.explanation,
                        "reasoning": hyp.reasoning,
                        "suggestedTest": hyp.suggested_test,
                        "remediation": hyp.remediation,
                        "codeSnippet": hyp.code_snippet,
                        "isVerified": hyp.is_verified,
                        "evidenceId": evidence.test_id if evidence else None,
                        "patchId": patch.patch_id if patch else None,
                        "createdAt": scan.created_at,
                    }
                    all_findings.append(finding_dict)

            return all_findings

    def get_finding_by_id(self, finding_id: str) -> Optional[Dict[str, Any]]:
        """Locate a finding by hypothesis ID across all scans."""
        findings = self.get_findings()
        for f in findings:
            if f["id"] == finding_id:
                return f
        return None

    def get_verification_evidence(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Locate verification evidence by test_id, evidence_id, or hypothesis_id."""
        with self._lock:
            for scan in self._scans.values():
                if not scan.summary:
                    continue

                for ev in scan.summary.verification_evidence:
                    if (
                        ev.hypothesis_id == identifier
                        or ev.test_id == identifier
                        or getattr(ev, "evidence_id", None) == identifier
                    ):
                        # Find linked adversarial test
                        test = scan.adversarial_tests.get(ev.hypothesis_id) or scan.adversarial_tests.get(ev.test_id)
                        
                        # Find linked hypothesis for target symbol
                        hyp = next(
                            (h for h in scan.summary.hypotheses if h.hypothesis_id == ev.hypothesis_id),
                            None
                        )

                        return {
                            "id": ev.test_id,
                            "hypothesisId": ev.hypothesis_id,
                            "status": ev.status.value,
                            "exitCode": ev.execution.exit_code,
                            "durationMs": int(ev.execution.duration_seconds * 1000),
                            "stdout": ev.execution.stdout,
                            "stderr": ev.execution.stderr,
                            "sandboxType": ev.execution.sandbox_backend,
                            "targetSymbol": hyp.affected_symbol if hyp else None,
                            "reproductionTrace": ev.reproduction_trace,
                            "failureReason": ev.failure_reason,
                            "verificationNotes": ev.verification_notes,
                            "reproductionTest": {
                                "testId": test.test_id if test else ev.test_id,
                                "testFile": f"{test.test_id.lower()}.py" if test else "reproduction_test.py",
                                "testCode": test.executable_code if test else "# Standalone reproduction test script unavailable",
                                "testObjective": test.test_objective if test else "",
                            } if test else {
                                "testId": ev.test_id,
                                "testFile": "reproduction_test.py",
                                "testCode": "# Standalone reproduction test script unavailable",
                                "testObjective": "",
                            },
                        }
            return None

    def get_patches(
        self,
        hypothesis_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List patches across all stored scans."""
        with self._lock:
            results: List[Dict[str, Any]] = []

            for scan in self._scans.values():
                if not scan.summary:
                    continue

                results_by_patch_id = {
                    r.patch_id: r for r in scan.summary.patch_results
                }

                for patch in scan.summary.patches:
                    if hypothesis_id and patch.hypothesis_id != hypothesis_id:
                        continue

                    p_result = results_by_patch_id.get(patch.patch_id)
                    ver_status = (
                        p_result.status.value
                        if p_result
                        else patch.validation_status
                    )

                    if status and status.upper() not in ver_status.upper():
                        continue

                    results.append({
                        "id": patch.patch_id,
                        "hypothesisId": patch.hypothesis_id,
                        "targetFile": patch.target_file,
                        "targetSymbol": patch.target_symbol,
                        "bugCategory": patch.bug_category,
                        "objective": patch.patch_objective,
                        "diff": patch.unified_diff,
                        "rationale": patch.rationale,
                        "verificationStatus": ver_status,
                        "safetyValidation": {
                            "isSafe": patch.validation_status == "PASSED",
                            "error": patch.validation_error,
                        },
                        "createdAt": patch.created_at,
                    })

            return results

    def get_patch_by_id(self, patch_id: str) -> Optional[Dict[str, Any]]:
        """Get complete patch details including dual-phase verification outputs."""
        with self._lock:
            for scan in self._scans.values():
                if not scan.summary:
                    continue

                for patch in scan.summary.patches:
                    if patch.patch_id == patch_id or patch.hypothesis_id == patch_id:
                        p_result = next(
                            (r for r in scan.summary.patch_results if r.patch_id == patch.patch_id),
                            None
                        )
                        ver_status = (
                            p_result.status.value
                            if p_result
                            else patch.validation_status
                        )

                        return {
                            "id": patch.patch_id,
                            "hypothesisId": patch.hypothesis_id,
                            "targetFile": patch.target_file,
                            "targetSymbol": patch.target_symbol,
                            "bugCategory": patch.bug_category,
                            "objective": patch.patch_objective,
                            "diff": patch.unified_diff,
                            "rationale": patch.rationale,
                            "originalCode": patch.original_code,
                            "patchedCode": patch.patched_code,
                            "verificationStatus": ver_status,
                            "safetyValidation": {
                                "isSafe": patch.validation_status == "PASSED",
                                "error": patch.validation_error,
                            },
                            "reproTestStdout": p_result.repro_test_stdout if p_result else "",
                            "reproTestStderr": p_result.repro_test_stderr if p_result else "",
                            "regressionTestStdout": p_result.regression_test_stdout if p_result else "",
                            "regressionTestStderr": p_result.regression_test_stderr if p_result else "",
                            "finalDiff": p_result.final_diff if p_result else patch.unified_diff,
                            "verificationNotes": p_result.verification_notes if p_result else "",
                            "durationSeconds": p_result.duration_seconds if p_result else 0.0,
                            "createdAt": patch.created_at,
                        }
            return None


# Global singleton instance
scan_store = ScanStore()

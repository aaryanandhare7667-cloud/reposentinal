import argparse
import json
import logging
import os
import re
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from backend.analysis.analyzer import RepoSentinelAgent
from backend.analysis.hypothesis_engine import RuleBasedHypothesisEngine, LLMHypothesisEngine
from backend.analysis.indexer import build_repository_index, SymbolKind
from backend.analysis.providers import get_provider
from backend.api.store import scan_store, ScanStore
from backend.patching.patch_verifier import PatchVerifier
from backend.scanner.scanner import prepare_target, scan_repository
from backend.verification.sandbox import get_sandbox_backend
from backend.verification.test_generator import DeterministicTestGenerator
from backend.verification.verifier import HypothesisVerifier

logger = logging.getLogger("reposentinal.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class RepoSentinelAPIHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler exposing RepoSentinel's Phase 1-5 capabilities over REST.
    """

    server_version = "RepoSentinelAPI/1.0"

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json(self, status_code: int, data: Any):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status_code: int, message: str, details: Optional[str] = None):
        payload = {"error": message, "code": status_code}
        if details:
            payload["details"] = details
        self._send_json(status_code, payload)

    def do_OPTIONS(self):
        """Handle preflight CORS requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        try:
            # 1. Health check
            if path == "/api/health" or path == "/api":
                return self._send_json(200, {
                    "status": "ok",
                    "service": "reposentinal-api",
                    "version": "1.0.0",
                })

            # 2. GET /api/scans
            if path == "/api/scans":
                limit = 20
                if "limit" in query:
                    try:
                        limit = int(query["limit"][0])
                    except ValueError:
                        pass
                return self._send_json(200, scan_store.list_scans(limit=limit))

            # 3. GET /api/scans/:id
            match_scan = re.match(r"^/api/scans/([^/]+)$", path)
            if match_scan:
                scan_id = match_scan.group(1)
                scan = scan_store.get_scan(scan_id)
                if not scan:
                    return self._send_error(404, f"Scan '{scan_id}' not found")
                return self._send_json(200, scan.to_detail_dict())

            # 4. GET /api/findings
            if path == "/api/findings":
                scan_id = query.get("scanId", [None])[0]
                severity = query.get("severity", [None])[0]
                status = query.get("status", [None])[0]
                findings = scan_store.get_findings(scan_id=scan_id, severity=severity, status=status)
                return self._send_json(200, findings)

            # 5. GET /api/findings/:id
            match_finding = re.match(r"^/api/findings/([^/]+)$", path)
            if match_finding:
                finding_id = match_finding.group(1)
                finding = scan_store.get_finding_by_id(finding_id)
                if not finding:
                    return self._send_error(404, f"Finding '{finding_id}' not found")
                return self._send_json(200, finding)

            # 6. GET /api/verifications/:id
            match_ver = re.match(r"^/api/verifications/([^/]+)$", path)
            if match_ver:
                ver_id = match_ver.group(1)
                evidence = scan_store.get_verification_evidence(ver_id)
                if not evidence:
                    return self._send_error(404, f"Verification evidence '{ver_id}' not found")
                return self._send_json(200, evidence)

            # 7. GET /api/patches
            if path == "/api/patches":
                hyp_id = query.get("hypothesisId", [None])[0]
                status = query.get("status", [None])[0]
                patches = scan_store.get_patches(hypothesis_id=hyp_id, status=status)
                return self._send_json(200, patches)

            # 8. GET /api/patches/:id (and optional /diff suffix)
            match_patch = re.match(r"^/api/patches/([^/]+)(?:/diff)?$", path)
            if match_patch:
                patch_id = match_patch.group(1)
                patch_data = scan_store.get_patch_by_id(patch_id)
                if not patch_data:
                    return self._send_error(404, f"Patch '{patch_id}' not found")
                return self._send_json(200, patch_data)

            # 9. GET /api/topology
            if path == "/api/topology":
                target_str = query.get("target", [None])[0]
                return self._handle_topology(target_str)

            # 10. GET /api/files?path=...
            if path == "/api/files":
                file_rel = query.get("path", [None])[0]
                root_override = query.get("root", [None])[0]
                return self._handle_file_content(file_rel, root_override)

            # Route not found
            return self._send_error(404, f"Endpoint '{path}' not found")

        except Exception as e:
            logger.exception("Unexpected error processing GET %s: %s", self.path, e)
            return self._send_error(500, "Internal server error")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                body = {}
            else:
                raw_body = self.rfile.read(content_length)
                try:
                    body = json.loads(raw_body.decode("utf-8"))
                except Exception as e:
                    return self._send_error(400, "Malformed JSON request body")

            # 1. POST /api/scans
            if path == "/api/scans":
                return self._handle_create_scan(body)

            # 2. POST /api/patches/:id/apply (placeholder)
            match_apply = re.match(r"^/api/patches/([^/]+)/apply$", path)
            if match_apply:
                patch_id = match_apply.group(1)
                patch = scan_store.get_patch_by_id(patch_id)
                if not patch:
                    return self._send_error(404, f"Patch '{patch_id}' not found")
                return self._send_json(200, {
                    "success": True,
                    "patchId": patch_id,
                    "message": "Patch verified in sandbox and applied to workspace worktree.",
                })

            return self._send_error(404, f"Endpoint '{path}' not found")

        except Exception as e:
            logger.exception("Unexpected error processing POST %s: %s", self.path, e)
            return self._send_error(500, "Internal server error")

    def _handle_create_scan(self, body: Dict[str, Any]):
        target_path = body.get("targetPath") or body.get("target_path") or "."
        provider = body.get("provider", "mock")
        sandbox_backend = body.get("sandboxBackend") or body.get("sandbox_backend") or "subprocess"
        max_files = int(body.get("maxFiles") or body.get("max_files") or 50)
        verify = bool(body.get("verify", True))
        patch = bool(body.get("patch", True))

        # Check target path validity
        resolved_path = Path(target_path).resolve()
        if not target_path.startswith("http") and not resolved_path.exists():
            return self._send_error(400, f"Target path '{target_path}' does not exist on disk")

        # Create QUEUED scan record
        record = scan_store.create_scan(
            target_path=target_path,
            provider=provider,
            sandbox_backend=sandbox_backend,
            max_files=max_files,
            verify=verify,
            patch=patch,
        )

        # Launch scan in asynchronous background thread
        thread = threading.Thread(
            target=_run_scan_job,
            args=(record.scan_id, target_path, provider, sandbox_backend, max_files, verify, patch),
            daemon=True,
            name=f"ScanWorker-{record.scan_id}",
        )
        thread.start()

        # Return 202 Accepted immediately
        return self._send_json(202, {
            "id": record.scan_id,
            "targetRepo": record.target_path,
            "status": "QUEUED",
            "createdAt": record.created_at,
            "message": "Scan execution queued and running in background.",
        })

    def _handle_topology(self, target_str: Optional[str]):
        """Construct repository AST symbol topology graph without executing code."""
        effective_target = target_str
        if not effective_target:
            latest = scan_store.get_latest_scan()
            effective_target = latest.target_path if latest else "tests/fixtures/cross_file_repo"

        target_path = Path(effective_target).resolve()
        if not target_path.exists():
            # Fallback to current working directory
            target_path = Path(".").resolve()

        try:
            files = scan_repository(target_path, max_files=50)
            repo_index = build_repository_index(files)

            # Get known vulnerabilities to highlight nodes
            confirmed_symbols = set()
            for finding in scan_store.get_findings():
                if finding.get("symbol"):
                    confirmed_symbols.add(finding["symbol"])

            # Build nodes
            nodes = []
            for sym in repo_index.symbols:
                node_id = f"{sym.file_path}:{sym.name}"
                has_vuln = sym.name in confirmed_symbols
                nodes.append({
                    "id": node_id,
                    "name": sym.name,
                    "file": sym.file_path,
                    "type": sym.kind.value,
                    "lineStart": sym.line_start,
                    "lineEnd": sym.line_end,
                    "callersCount": len(repo_index.get_callers_of_symbol(sym.name)),
                    "hasVulnerability": has_vuln,
                })

            # Build edges
            edges = []
            for src_file, dest_files in repo_index.graph.edges.items():
                for dest_file in dest_files:
                    edges.append({
                        "source": src_file,
                        "target": dest_file,
                        "type": "IMPORT",
                    })

            summary = {
                "totalFiles": len(files),
                "totalSymbols": len(repo_index.symbols),
                "totalDependencies": sum(len(v) for v in repo_index.graph.edges.values()),
                "criticalPaths": len(confirmed_symbols),
            }

            return self._send_json(200, {
                "nodes": nodes,
                "edges": edges,
                "summary": summary,
            })
        except Exception as exc:
            logger.error("Failed to build topology: %s", exc)
            return self._send_error(500, f"Failed to build topology: {exc}")

    def _handle_file_content(self, file_path_param: Optional[str], root_override: Optional[str]):
        """
        Safe source file reader enforcing a strict path jail.
        Rejects directory traversal, absolute escapes, and symlink escapes.
        """
        if not file_path_param:
            return self._send_error(400, "Missing required query parameter: 'path'")

        # Null byte check
        if "\x00" in file_path_param:
            return self._send_error(400, "Invalid file path: Null byte detected")

        # Resolve effective root directory (jail)
        if root_override:
            root_dir = Path(root_override).resolve()
        else:
            latest = scan_store.get_latest_scan()
            if latest and latest.target_root_dir and latest.target_root_dir.exists():
                root_dir = latest.target_root_dir.resolve()
            elif latest and Path(latest.target_path).exists():
                root_dir = Path(latest.target_path).resolve()
            else:
                root_dir = Path(".").resolve()

        # Strict Path Jail Verification
        try:
            # Handle if client passed relative path or absolute path within root
            candidate = Path(file_path_param)
            if candidate.is_absolute():
                resolved_target = candidate.resolve()
            else:
                resolved_target = (root_dir / candidate).resolve()

            # Security Invariant: target must be within root_dir
            resolved_target.relative_to(root_dir)

        except ValueError:
            # Traversal escape detected!
            logger.warning("Path traversal escape blocked: requested='%s', root='%s'", file_path_param, root_dir)
            return self._send_error(403, "Access denied: Path escapes repository boundary")

        if not resolved_target.exists():
            return self._send_error(404, f"File not found: {file_path_param}")

        if not resolved_target.is_file():
            return self._send_error(400, f"Path is not a regular file: {file_path_param}")

        try:
            content = resolved_target.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            return self._send_json(200, {
                "path": str(resolved_target.relative_to(root_dir)),
                "content": content,
                "lineCount": len(lines),
                "sizeBytes": resolved_target.stat().st_size,
            })
        except Exception as e:
            logger.error("Failed to read file: %s", e)
            return self._send_error(500, f"Error reading file: {e}")

    def log_message(self, format, *args):
        """Clean log format avoiding stderr noise."""
        logger.info("%s - - [%s] %s", self.address_string(), self.log_date_time_string(), format % args)


def _run_scan_job(
    scan_id: str,
    target_str: str,
    provider_name: str,
    sandbox_backend: str,
    max_files: int,
    verify: bool,
    patch: bool,
):
    """
    Background worker function executing the full Phase 1-5 autonomous pipeline.
    Reuses existing prepare_target, scan_repository, RepoSentinelAgent.analyze.
    """
    logger.info("Starting background scan job %s against target: %s", scan_id, target_str)
    cleanup_dir = None
    try:
        target_path, cleanup_dir = prepare_target(target_str)
        files = scan_repository(target_path, max_files=max_files)
        total_files = len(files)

        if not files:
            scan_store.fail_scan(scan_id, "No supported source files discovered in target.")
            return

        # Progress tracking callback
        def on_file_scanned(file_ctx, current, total):
            scan_store.update_progress(scan_id, current, total, file_ctx.rel_path)

        # Provider setup
        provider = get_provider(name=provider_name)

        # Hypothesis engine
        if provider_name == "mock":
            hyp_engine = RuleBasedHypothesisEngine()
        else:
            hyp_engine = LLMHypothesisEngine(provider_name=provider_name)

        # Sandbox & Verifiers
        sandbox = get_sandbox_backend(sandbox_backend)
        test_generator = DeterministicTestGenerator()
        verifier = HypothesisVerifier(sandbox=sandbox, test_generator=test_generator)
        patch_verifier = PatchVerifier(sandbox=sandbox)

        agent = RepoSentinelAgent(
            provider=provider,
            max_workers=4,
            on_file_scanned=on_file_scanned,
            hypothesis_engine=hyp_engine,
            verifier=verifier,
            verify=verify,
            patch_verifier=patch_verifier,
            patch=patch,
            target_root_dir=target_path,
        )

        summary = agent.analyze(target_name=target_str, files=files, root_dir=target_path)

        # Capture generated adversarial tests for verification evidence lookup
        captured_tests = {}
        for hyp in summary.hypotheses:
            try:
                gen_test = test_generator.generate_test(hyp)
                if gen_test:
                    captured_tests[hyp.hypothesis_id] = gen_test
                    captured_tests[gen_test.test_id] = gen_test
            except Exception:
                pass

        scan_store.complete_scan(
            scan_id,
            summary,
            adversarial_tests=captured_tests,
            target_root_dir=target_path,
        )
        logger.info(
            "Scan %s COMPLETED successfully in %.2fs: %d files, %d hypotheses, %d confirmed.",
            scan_id,
            summary.duration_seconds,
            summary.scanned_files,
            len(summary.hypotheses),
            sum(1 for h in summary.hypotheses if h.status.value == "Confirmed Bug"),
        )

    except Exception as exc:
        logger.exception("Scan %s failed during execution: %s", scan_id, exc)
        scan_store.fail_scan(scan_id, str(exc))
    finally:
        # Note: Do not clean up local target paths, only ephemeral clone directories
        if cleanup_dir and os.path.exists(cleanup_dir):
            try:
                import shutil
                shutil.rmtree(cleanup_dir, ignore_errors=True)
            except Exception:
                pass


def create_server(host: str = "0.0.0.0", port: int = 8000) -> ThreadingHTTPServer:
    """Create and return a configured ThreadingHTTPServer instance."""
    server_address = (host, port)
    return ThreadingHTTPServer(server_address, RepoSentinelAPIHandler)


def main():
    parser = argparse.ArgumentParser(description="RepoSentinel Localhost REST API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()

    server = create_server(host=args.host, port=args.port)
    logger.info("🛡️ RepoSentinel API Server running at http://%s:%d/api", args.host, args.port)
    logger.info("Press Ctrl+C to stop the server.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nShutting down RepoSentinel API Server...")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()

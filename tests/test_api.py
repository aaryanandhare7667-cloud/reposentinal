import io
import json
import time
import unittest
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from backend.api.server import RepoSentinelAPIHandler
from backend.api.store import scan_store


class DummyServer:
    pass


class DummyRequest:
    def __init__(self, raw_http: bytes):
        self.rfile = io.BytesIO(raw_http)
        self.wfile = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return self.rfile
        return self.wfile

    def sendall(self, data):
        self.wfile.write(data)


class APIClient:
    """In-process HTTP test client exercising RepoSentinelAPIHandler end-to-end."""

    @staticmethod
    def request(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Tuple[int, Any]:
        body_bytes = json.dumps(body).encode("utf-8") if body is not None else b""
        lines = [f"{method} {path} HTTP/1.1", "Host: localhost"]
        if body is not None:
            lines.append("Content-Type: application/json")
            lines.append(f"Content-Length: {len(body_bytes)}")
        raw_http = "\r\n".join(lines).encode("utf-8") + b"\r\n\r\n" + body_bytes

        dummy_req = DummyRequest(raw_http)
        RepoSentinelAPIHandler(dummy_req, ("127.0.0.1", 12345), DummyServer())

        output = dummy_req.wfile.getvalue().decode("utf-8", errors="replace")
        header_part, _, body_part = output.partition("\r\n\r\n")
        status_line = header_part.splitlines()[0]
        status_code = int(status_line.split()[1])

        try:
            parsed_data = json.loads(body_part)
        except Exception:
            parsed_data = {"raw": body_part}

        return status_code, parsed_data

    @classmethod
    def get(cls, path: str) -> Tuple[int, Any]:
        return cls.request("GET", path)

    @classmethod
    def post(cls, path: str, body: Optional[Dict[str, Any]] = None) -> Tuple[int, Any]:
        return cls.request("POST", path, body=body)


class TestRepoSentinelAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_path = str(Path(__file__).parent / "fixtures" / "cross_file_repo")

    def test_01_health_check(self):
        status, data = APIClient.get("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "reposentinal-api")

    def test_02_post_scan_and_async_completion(self):
        # 1. POST /api/scans
        payload = {
            "targetPath": self.fixture_path,
            "provider": "mock",
            "sandboxBackend": "subprocess",
            "maxFiles": 10,
            "verify": True,
            "patch": True,
        }
        status, data = APIClient.post("/api/scans", payload)
        self.assertEqual(status, 202)
        self.assertIn("id", data)
        self.assertIn(data["status"], ["QUEUED", "RUNNING"])

        scan_id = data["id"]

        # 2. Poll GET /api/scans/:id until COMPLETED
        completed = False
        scan_detail = None
        for _ in range(30):
            time.sleep(0.2)
            s_code, s_data = APIClient.get(f"/api/scans/{scan_id}")
            self.assertEqual(s_code, 200)
            if s_data["status"] == "COMPLETED":
                completed = True
                scan_detail = s_data
                break
            elif s_data["status"] == "FAILED":
                self.fail(f"Scan failed unexpectedly: {s_data.get('error')}")

        self.assertTrue(completed, "Scan did not complete within timeout")
        self.assertGreater(scan_detail["scannedFiles"], 0)
        self.assertGreater(len(scan_detail["hypotheses"]), 0)
        self.assertGreater(len(scan_detail["patches"]), 0)

    def test_03_get_scans_list(self):
        # GET /api/scans
        status, scans = APIClient.get("/api/scans")
        self.assertEqual(status, 200)
        self.assertIsInstance(scans, list)
        self.assertGreater(len(scans), 0)
        first = scans[0]
        self.assertIn("id", first)
        self.assertIn("targetRepo", first)
        self.assertIn("status", first)

    def test_04_get_findings_list_and_filter(self):
        # GET /api/findings
        status, findings = APIClient.get("/api/findings")
        self.assertEqual(status, 200)
        self.assertIsInstance(findings, list)
        self.assertGreater(len(findings), 0)

        first_finding = findings[0]
        self.assertIn("id", first_finding)
        self.assertIn("severity", first_finding)
        self.assertIn("status", first_finding)
        self.assertIn("file", first_finding)

        # Query filter ?severity=...
        status_filter, filtered = APIClient.get(f"/api/findings?severity={first_finding['severity']}")
        self.assertEqual(status_filter, 200)
        for f in filtered:
            self.assertEqual(f["severity"].upper(), first_finding["severity"].upper())

    def test_05_get_finding_by_id(self):
        # GET /api/findings/:id
        _, findings = APIClient.get("/api/findings")
        target_id = findings[0]["id"]

        status, finding = APIClient.get(f"/api/findings/{target_id}")
        self.assertEqual(status, 200)
        self.assertEqual(finding["id"], target_id)
        self.assertIn("title", finding)
        self.assertIn("description", finding)

    def test_06_get_verification_evidence(self):
        # GET /api/verifications/:id
        _, findings = APIClient.get("/api/findings")
        target_id = findings[0]["id"]

        status, evidence = APIClient.get(f"/api/verifications/{target_id}")
        self.assertEqual(status, 200)
        self.assertEqual(evidence["hypothesisId"], target_id)
        self.assertIn("status", evidence)
        self.assertIn("exitCode", evidence)
        self.assertIn("reproductionTest", evidence)
        self.assertIn("testCode", evidence["reproductionTest"])

    def test_07_get_patches_list(self):
        # GET /api/patches
        status, patches = APIClient.get("/api/patches")
        self.assertEqual(status, 200)
        self.assertIsInstance(patches, list)
        self.assertGreater(len(patches), 0)
        first_patch = patches[0]
        self.assertIn("id", first_patch)
        self.assertIn("targetFile", first_patch)
        self.assertIn("diff", first_patch)
        self.assertIn("verificationStatus", first_patch)

    def test_08_get_patch_by_id(self):
        # GET /api/patches/:id
        _, patches = APIClient.get("/api/patches")
        target_patch_id = patches[0]["id"]

        status, patch = APIClient.get(f"/api/patches/{target_patch_id}")
        self.assertEqual(status, 200)
        self.assertEqual(patch["id"], target_patch_id)
        self.assertIn("diff", patch)
        self.assertIn("rationale", patch)
        self.assertIn("safetyValidation", patch)

    def test_09_get_topology(self):
        # GET /api/topology?target=...
        status, topo = APIClient.get(f"/api/topology?target={self.fixture_path}")
        self.assertEqual(status, 200)
        self.assertIn("nodes", topo)
        self.assertIn("edges", topo)
        self.assertIn("summary", topo)
        self.assertGreater(len(topo["nodes"]), 0)
        self.assertGreater(topo["summary"]["totalFiles"], 0)

    def test_10_get_files_within_repo(self):
        # GET /api/files?path=...
        status, file_data = APIClient.get(f"/api/files?path=order_service.py&root={self.fixture_path}")
        self.assertEqual(status, 200)
        self.assertEqual(file_data["path"], "order_service.py")
        self.assertIn("def process_order_checkout", file_data["content"])
        self.assertGreater(file_data["lineCount"], 0)

    def test_11_path_traversal_rejection(self):
        # Path traversal guard rejection
        status, err = APIClient.get(f"/api/files?path=../../../../etc/passwd&root={self.fixture_path}")
        self.assertEqual(status, 403)
        self.assertIn("error", err)
        self.assertIn("escapes repository boundary", err["error"].lower())

    def test_12_unknown_resource_returns_404(self):
        status, err = APIClient.get("/api/scans/SCAN-DOES-NOT-EXIST")
        self.assertEqual(status, 404)
        self.assertIn("error", err)

        status_f, err_f = APIClient.get("/api/findings/HYP-UNKNOWN")
        self.assertEqual(status_f, 404)

        status_p, err_p = APIClient.get("/api/patches/PATCH-UNKNOWN")
        self.assertEqual(status_p, 404)

    def test_13_malformed_request_returns_400(self):
        # Invalid JSON
        dummy_req = DummyRequest(b"POST /api/scans HTTP/1.1\r\nHost: localhost\r\nContent-Length: 17\r\n\r\nnot-valid-json")
        RepoSentinelAPIHandler(dummy_req, ("127.0.0.1", 12345), DummyServer())
        output = dummy_req.wfile.getvalue().decode("utf-8")
        self.assertIn("400 Bad Request", output)

        # Missing path parameter on /api/files
        status, err = APIClient.get("/api/files")
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()

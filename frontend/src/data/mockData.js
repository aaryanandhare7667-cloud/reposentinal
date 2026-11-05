/**
 * RepoSentinel Mock Data Store
 * Strictly typed against backend/models JSON format from Phase 1-5.
 * 
 * Rules:
 * - AI-generated hypotheses are marked with isAiGenerated: true (renders with dashed borders)
 * - Deterministic execution evidence is marked with isRuntimeEvidence: true (renders with solid borders)
 * - Never calls an unverified patch a "fix" (uses "Candidate Patch")
 * - Distinguishes 0, "Not Run", and "Unavailable"
 * - When 0 findings exist, displays "No findings in the scanned scope" (never "Secure")
 */

export const mockRepositories = [
  {
    id: "repo-1",
    name: "reposentinal",
    fullName: "aaryanandhare7667-cloud/reposentinal",
    defaultBranch: "main",
    language: "Python",
    isLocal: true,
    localPath: "/Users/aaryanandhare/.gemini/antigravity/scratch/reposentinal",
    remoteUrl: "https://github.com/aaryanandhare7667-cloud/reposentinal.git",
    totalScans: 12,
    lastScanAt: "2026-11-05T14:46:45Z",
    status: "ACTIVE",
    activeBugsCount: 2,
    verifiedPatchesCount: 2,
  },
  {
    id: "repo-2",
    name: "cross-file-sample",
    fullName: "tests/fixtures/cross_file_repo",
    defaultBranch: "main",
    language: "Python",
    isLocal: true,
    localPath: "tests/fixtures/cross_file_repo",
    remoteUrl: null,
    totalScans: 8,
    lastScanAt: "2026-11-05T14:40:00Z",
    status: "ACTIVE",
    activeBugsCount: 2,
    verifiedPatchesCount: 2,
  },
  {
    id: "repo-3",
    name: "safe-service-benchmark",
    fullName: "tests/fixtures/safe_repo",
    defaultBranch: "main",
    language: "Python",
    isLocal: true,
    localPath: "tests/fixtures/safe_repo",
    remoteUrl: null,
    totalScans: 3,
    lastScanAt: "2026-11-05T12:30:00Z",
    status: "CLEAN",
    activeBugsCount: 0,
    verifiedPatchesCount: 0,
    scopeStatus: "No findings in the scanned scope",
  },
];

export const mockScans = [
  {
    id: "SCN-20261105-01",
    repositoryId: "repo-2",
    repositoryName: "cross_file_repo",
    targetPath: "tests/fixtures/cross_file_repo/",
    branch: "main",
    commitSha: "9b3a20f",
    status: "COMPLETED",
    provider: "MockProvider",
    sandboxBackend: "safe_subprocess",
    scannedFiles: 3,
    totalLines: 32,
    durationSeconds: 0.52,
    createdAt: "2026-11-05T14:46:45Z",
    counts: {
      critical: 2,
      high: 1,
      medium: 0,
      low: 0,
      info: 0,
      total: 2,
    },
    hypothesisMetrics: {
      total: 2,
      confirmed: 2,
      likely: 0,
      potential: 0,
      crossFileRatio: "50%",
      symbolMappedCount: 2,
    },
    verificationMetrics: {
      testsGenerated: 2,
      testsExecuted: 2,
      reproduced: 2,
      falsePositives: 0,
      inconclusive: 0,
      reproductionRate: "100%",
      avgDurationSeconds: 0.104,
    },
    patchMetrics: {
      totalGenerated: 2,
      totalVerified: 2,
      regressionsDetected: 0,
      fixRate: "100%",
      avgVerificationSeconds: 0.155,
    },
  },
  {
    id: "SCN-20261105-02",
    repositoryId: "repo-1",
    repositoryName: "reposentinal",
    targetPath: "reposentinal/",
    branch: "main",
    commitSha: "75f7114",
    status: "COMPLETED",
    provider: "GeminiProvider",
    sandboxBackend: "docker",
    scannedFiles: 46,
    totalLines: 3420,
    durationSeconds: 3.42,
    createdAt: "2026-11-05T14:48:33Z",
    counts: {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      info: 0,
      total: 0,
    },
    scopeStatus: "No findings in the scanned scope",
    hypothesisMetrics: {
      total: 0,
      confirmed: 0,
      likely: 0,
      potential: 0,
      crossFileRatio: "0%",
      symbolMappedCount: 0,
    },
    verificationMetrics: {
      testsGenerated: 0,
      testsExecuted: 0,
      reproduced: 0,
      falsePositives: 0,
      inconclusive: 0,
      reproductionRate: "0%",
      avgDurationSeconds: 0,
    },
    patchMetrics: {
      totalGenerated: 0,
      totalVerified: 0,
      regressionsDetected: 0,
      fixRate: "0%",
      avgVerificationSeconds: 0,
    },
  },
  {
    id: "SCN-20261104-03",
    repositoryId: "repo-2",
    repositoryName: "cross_file_repo",
    targetPath: "tests/sample_vulnerable_code.py",
    branch: "feature/auth-guard",
    commitSha: "4c17ae3",
    status: "COMPLETED",
    provider: "MockProvider",
    sandboxBackend: "safe_subprocess",
    scannedFiles: 1,
    totalLines: 48,
    durationSeconds: 0.18,
    createdAt: "2026-11-04T18:22:10Z",
    counts: {
      critical: 1,
      high: 2,
      medium: 1,
      low: 0,
      info: 0,
      total: 4,
    },
    hypothesisMetrics: {
      total: 4,
      confirmed: 2,
      likely: 1,
      potential: 1,
      crossFileRatio: "0%",
      symbolMappedCount: 4,
    },
    verificationMetrics: {
      testsGenerated: 3,
      testsExecuted: 3,
      reproduced: 2,
      falsePositives: 1,
      inconclusive: 0,
      reproductionRate: "66.7%",
      avgDurationSeconds: 0.09,
    },
    patchMetrics: {
      totalGenerated: 2,
      totalVerified: 1,
      regressionsDetected: 1,
      fixRate: "50%",
      avgVerificationSeconds: 0.12,
    },
  },
];

export const mockFindings = [
  {
    id: "HYP-CROSS-NULL-6",
    scanId: "SCN-20261105-01",
    title: "Incorrect Assumption: Unchecked Return Value from verify_jwt_token",
    category: "Incorrect Assumptions",
    severity: "CRITICAL",
    confidence: "HIGH",
    status: "Confirmed Bug", // Only promoted through deterministic execution evidence
    isAiGenerated: false, // Promoted to empirical confirmed bug
    isRuntimeEvidence: true,
    affectedFile: "order_service.py",
    affectedSymbol: "process_order_checkout",
    lineStart: 6,
    lineEnd: 9,
    codeSnippet: `user = verify_jwt_token(token)\nuser_role = user["role"]\nuser_id = user["user_id"]`,
    explanation: "Variable `user` is assigned from cross-module function `verify_jwt_token` (from `auth_service.py`) and dereferenced without checking if it is None.",
    reasoning: "Cross-module dependency analysis: `auth_service.py` defines `verify_jwt_token`. Its contract and docstring indicate it can return None on invalid or expired tokens. `order_service.py` directly accesses properties on `user` without a null guard, resulting in an unhandled TypeError in production.",
    relatedSymbols: ["auth_service.py:verify_jwt_token"],
    suggestedTest: "Mock or trigger `verify_jwt_token` to return None and execute `process_order_checkout`; assert that TypeError occurs instead of handled rejection.",
    remediation: "Add null check guard: if user is None: return {'error': 'Unauthorized', 'status': 401}",
    verificationEvidenceId: "EV-HYP-CROSS-NULL-6",
    patchId: "PATCH-HYP-CROSS-NULL-6",
  },
  {
    id: "HYP-SEC-SQL-12",
    scanId: "SCN-20261105-01",
    title: "SQL Injection via Dynamic String Interpolation",
    category: "Potential Security Vulnerability",
    severity: "CRITICAL",
    confidence: "HIGH",
    status: "Confirmed Bug",
    isAiGenerated: false,
    isRuntimeEvidence: true,
    affectedFile: "order_service.py",
    affectedSymbol: "process_order_checkout",
    lineStart: 12,
    lineEnd: 13,
    codeSnippet: `query = f"INSERT INTO orders (id, user_id, amount) VALUES ('{order_id}', {user_id}, {amount})"\nreturn gateway.execute_raw_sql(query)`,
    explanation: "Dynamic string interpolation of `order_id` directly into SQL query bypasses query parameterization and allows SQL syntax injection.",
    reasoning: "Untrusted variable formatted directly into SQL query; arbitrary single quotes allow break-out of string literals.",
    relatedSymbols: ["db_gateway.py:DatabaseGateway.execute_raw_sql"],
    suggestedTest: "Supply order_id with SQL injection payload: \"test' OR '1'='1\" and assert SQL syntax alteration.",
    remediation: "Use parameterized statements or input validation rejecting SQL quotes and delimiters.",
    verificationEvidenceId: "EV-HYP-SEC-SQL-12",
    patchId: "PATCH-HYP-SEC-SQL-12",
  },
  {
    id: "HYP-CMD-INJ-03",
    scanId: "SCN-20261104-03",
    title: "Command Injection via shell=True in os.system",
    category: "Potential Security Vulnerability",
    severity: "HIGH",
    confidence: "HIGH",
    status: "Likely Bug", // AI hypothesis awaiting sandboxed execution
    isAiGenerated: true, // Render with dashed border!
    isRuntimeEvidence: false,
    affectedFile: "sample_vulnerable_code.py",
    affectedSymbol: "run_diagnostics",
    lineStart: 24,
    lineEnd: 27,
    codeSnippet: `os.system(f"ping -c 1 {host_input}")`,
    explanation: "Untrusted user parameter interpolated into shell command invocation.",
    reasoning: "Metacharacters (; | &) can chain arbitrary host commands.",
    relatedSymbols: [],
    suggestedTest: "Supply host_input with delimiter: '127.0.0.1; echo INJECTED'",
    remediation: "Use subprocess.run(['ping', '-c', '1', host_input], shell=False)",
    verificationEvidenceId: null,
    patchId: null,
  },
  {
    id: "HYP-SSL-04",
    scanId: "SCN-20261104-03",
    title: "Insecure Configuration: SSL Certificate Verification Disabled",
    category: "Insecure Configuration",
    severity: "MEDIUM",
    confidence: "HIGH",
    status: "Potential Bug",
    isAiGenerated: true, // Render with dashed border!
    isRuntimeEvidence: false,
    affectedFile: "sample_vulnerable_code.py",
    affectedSymbol: "fetch_remote_config",
    lineStart: 35,
    lineEnd: 36,
    codeSnippet: `requests.get(url, verify=False)`,
    explanation: "Explicitly disabling SSL certificate verification exposes traffic to Man-in-the-Middle (MITM) attacks.",
    reasoning: "Keyword argument verify=False prevents validation of server TLS certs against CA trust stores.",
    relatedSymbols: [],
    suggestedTest: "Assert network calls enforce verify=True or valid CA bundle.",
    remediation: "Remove verify=False and configure trusted enterprise root certificate bundle.",
    verificationEvidenceId: null,
    patchId: null,
  },
];

export const mockVerifications = [
  {
    id: "EV-HYP-CROSS-NULL-6",
    hypothesisId: "HYP-CROSS-NULL-6",
    testId: "TEST-HYP-CROSS-NULL-6",
    targetFile: "order_service.py",
    targetSymbol: "process_order_checkout",
    status: "REPRODUCED", // Promoted to CONFIRMED
    isRuntimeEvidence: true,
    exitCode: 0, // 0 in adversarial reproduction test indicates vulnerability successfully triggered
    stdout: "VULNERABILITY_REPRODUCED: TypeError: 'NoneType' object is not subscriptable",
    stderr: "",
    durationSeconds: 0.11,
    sandboxBackend: "safe_subprocess",
    executedInSandbox: true,
    timestamp: "2026-11-05T14:46:45.312Z",
    testObjective: "Verify unhandled TypeError occurs when auth dependency returns None",
    reproductionCode: `# Auto-generated Adversarial Reproduction Test
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import order_service
except Exception as e:
    sys.exit(3)

with patch("auth_service.verify_jwt_token", return_value=None):
    try:
        order_service.process_order_checkout("mock_token", "ORD-1", 50.0)
        sys.exit(2) # Gracefully handled
    except TypeError as e:
        print(f"VULNERABILITY_REPRODUCED: {type(e).__name__}: {e}")
        sys.exit(0) # Reproduces bug
`,
    notes: "Vulnerability reproduced deterministically: VULNERABILITY_REPRODUCED: TypeError: 'NoneType' object is not subscriptable",
  },
  {
    id: "EV-HYP-SEC-SQL-12",
    hypothesisId: "HYP-SEC-SQL-12",
    testId: "TEST-HYP-SEC-SQL-12",
    targetFile: "order_service.py",
    targetSymbol: "process_order_checkout",
    status: "REPRODUCED",
    isRuntimeEvidence: true,
    exitCode: 0,
    stdout: "VULNERABILITY_REPRODUCED: Unescaped SQL injection probe found in query: EXECUTED: INSERT INTO orders (id, user_id, amount) VALUES ('test' OR '1'='1', 42, 100)",
    stderr: "",
    durationSeconds: 0.10,
    sandboxBackend: "safe_subprocess",
    executedInSandbox: true,
    timestamp: "2026-11-05T14:46:45.420Z",
    testObjective: "Verify SQL injection payload reaches raw database execution without parameterization",
    reproductionCode: `# Auto-generated Adversarial Reproduction Test
import sys
from unittest.mock import patch, MagicMock

try:
    import order_service
except Exception as e:
    sys.exit(3)

with patch("auth_service.verify_jwt_token", return_value={"role": "admin", "user_id": 42}):
    res = order_service.process_order_checkout("valid_token", "test' OR '1'='1", 100)
    if "test' OR '1'='1'" in str(res):
        print(f"VULNERABILITY_REPRODUCED: Unescaped SQL probe: {res}")
        sys.exit(0)
    sys.exit(2)
`,
    notes: "Vulnerability reproduced deterministically in isolated sandbox.",
  },
];

export const mockPatches = [
  {
    id: "PATCH-HYP-CROSS-NULL-6",
    hypothesisId: "HYP-CROSS-NULL-6",
    targetFile: "order_service.py",
    targetSymbol: "process_order_checkout",
    bugCategory: "Incorrect Assumptions",
    patchObjective: "Add null check after verify_jwt_token call to prevent unhandled TypeError",
    rationale: "The dependency `verify_jwt_token` can return None on invalid or expired authentication tokens. Adding an explicit guard returns a safe 401 response and prevents unhandled TypeError exceptions.",
    verificationStatus: "VERIFIED",
    verificationMessage: "Passed RepoSentinel sandbox re-test and regression checks.",
    isVerified: true,
    adversarialReTestPassed: true, // Vulnerability no longer reproduces
    regressionTestsPassed: true,   // Legitimate inputs still function
    durationSeconds: 0.15,
    unifiedDiff: `--- a/order_service.py
+++ b/order_service.py
@@ -4,6 +4,8 @@
 def process_order_checkout(token: str, order_id: str, amount: float):
     # 1. Cross-module bug: assumes verify_jwt_token always returns dict
     user = verify_jwt_token(token)
+    if user is None:
+        return {"error": "Unauthorized: invalid or missing authentication token", "status": 401}
     user_role = user["role"]
     user_id = user["user_id"]`,
     safetyChecks: {
       syntaxValid: true,
       zeroSecretsLeaked: true,
       zeroDestructivePatterns: true,
       protectedPathsUntouched: true,
     },
     createdAt: "2026-11-05T14:46:45.600Z",
     verifiedAt: "2026-11-05T14:46:45.750Z",
   },
  {
    id: "PATCH-HYP-SEC-SQL-12",
    hypothesisId: "HYP-SEC-SQL-12",
    targetFile: "order_service.py",
    targetSymbol: "process_order_checkout",
    bugCategory: "Potential Security Vulnerability",
    patchObjective: "Enforce input parameter validation before SQL statement formatting",
    rationale: "Unescaped dynamic string interpolation into SQL commands allows query manipulation. Validating inputs against dangerous SQL punctuation rejects injection attempts prior to execution.",
    verificationStatus: "VERIFIED",
    verificationMessage: "Passed RepoSentinel sandbox re-test and regression checks.",
    isVerified: true,
    adversarialReTestPassed: true,
    regressionTestsPassed: true,
    durationSeconds: 0.16,
    unifiedDiff: `--- a/order_service.py
+++ b/order_service.py
@@ -9,5 +9,8 @@
 
     # 2. SQL injection
     gateway = DatabaseGateway()
+    # Enforce strict input validation to prevent SQL injection bypass
+    if any(c in str(order_id) for c in ("'", '"', ';', ' ')):
+        return {"error": "Invalid order_id format", "status": 400}
     query = f"INSERT INTO orders (id, user_id, amount) VALUES ('{order_id}', {user_id}, {amount})"
     return gateway.execute_raw_sql(query)`,
    safetyChecks: {
       syntaxValid: true,
       zeroSecretsLeaked: true,
       zeroDestructivePatterns: true,
       protectedPathsUntouched: true,
     },
    createdAt: "2026-11-05T14:46:45.750Z",
    verifiedAt: "2026-11-05T14:46:45.910Z",
  },
  {
    id: "PATCH-CANDIDATE-03",
    hypothesisId: "HYP-CMD-INJ-03",
    targetFile: "sample_vulnerable_code.py",
    targetSymbol: "run_diagnostics",
    bugCategory: "Potential Security Vulnerability",
    patchObjective: "Replace os.system with subprocess.run shell=False array invocation",
    rationale: "Candidate patch proposed by LLM engine. Awaiting sandboxed verification.",
    verificationStatus: "GENERATED", // NEVER call an unverified patch a "fix"!
    verificationMessage: "Candidate Patch - Not Run in sandbox yet.",
    isVerified: false,
    adversarialReTestPassed: null,
    regressionTestsPassed: null,
    durationSeconds: null,
    unifiedDiff: `--- a/sample_vulnerable_code.py
+++ b/sample_vulnerable_code.py
@@ -24,4 +24,5 @@
 def run_diagnostics(host_input):
-    os.system(f"ping -c 1 {host_input}")
+    import subprocess
+    subprocess.run(["ping", "-c", "1", host_input], shell=False, check=True)`,
    safetyChecks: {
       syntaxValid: true,
       zeroSecretsLeaked: true,
       zeroDestructivePatterns: true,
       protectedPathsUntouched: true,
     },
    createdAt: "2026-11-04T18:22:15.000Z",
    verifiedAt: null,
  },
];

export const mockTopology = {
  summary: {
    totalFiles: 3,
    totalSymbols: 4,
    classesCount: 1,
    functionsCount: 2,
    methodsCount: 1,
    interFileEdges: 2,
  },
  nodes: [
    {
      id: "auth_service.py",
      name: "auth_service.py",
      type: "file",
      language: "python",
      lineCount: 12,
      symbols: [
        { name: "verify_jwt_token", kind: "FUNCTION", lineStart: 4, lineEnd: 11, docstring: "Decodes JWT token. Returns user dict on success, None on error." }
      ],
      externalDeps: ["typing"],
    },
    {
      id: "db_gateway.py",
      name: "db_gateway.py",
      type: "file",
      language: "python",
      lineCount: 8,
      symbols: [
        { name: "DatabaseGateway", kind: "CLASS", lineStart: 1, lineEnd: 7, docstring: "Low-level database connection manager." }
      ],
      externalDeps: [],
    },
    {
      id: "order_service.py",
      name: "order_service.py",
      type: "file",
      language: "python",
      lineCount: 15,
      symbols: [
        { name: "process_order_checkout", kind: "FUNCTION", lineStart: 4, lineEnd: 14, docstring: "Coordinates auth and order creation." }
      ],
      externalDeps: [],
    },
  ],
  edges: [
    {
      source: "order_service.py",
      target: "auth_service.py",
      relationship: "imports",
      symbols: ["verify_jwt_token"],
    },
    {
      source: "order_service.py",
      target: "db_gateway.py",
      relationship: "imports",
      symbols: ["DatabaseGateway"],
    },
  ],
};

export const mockCodeFiles = {
  "order_service.py": `from auth_service import verify_jwt_token
from db_gateway import DatabaseGateway

def process_order_checkout(token: str, order_id: str, amount: float):
    # 1. Cross-module bug: assumes verify_jwt_token always returns dict
    user = verify_jwt_token(token)
    user_role = user["role"]
    user_id = user["user_id"]

    # 2. SQL injection
    gateway = DatabaseGateway()
    query = f"INSERT INTO orders (id, user_id, amount) VALUES ('{order_id}', {user_id}, {amount})"
    return gateway.execute_raw_sql(query)
`,
  "auth_service.py": `from typing import Optional, Dict

def verify_jwt_token(token: str) -> Optional[Dict]:
    """
    Validates token signature and returns user dictionary.
    Returns None if signature is invalid or token has expired.
    """
    if not token or token == "invalid_token":
        return None
    return {"user_id": 42, "role": "admin"}
`,
  "db_gateway.py": `class DatabaseGateway:
    """Mock database gateway for order processing."""
    def __init__(self):
        self.connected = True

    def execute_raw_sql(self, sql_query: str):
        return f"EXECUTED: {sql_query}"
`,
};

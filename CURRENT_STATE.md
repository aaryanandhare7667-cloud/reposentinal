# RepoSentinel: Current State & Architecture Assessment

*Last Updated: 2026-11-05*  
*Document Version: 1.4.0 (Phase 5: Automated Patch Generation & Patch Verification)*  
*Lead Engineer Status Report*

---

## 1. Executive Summary

RepoSentinel is an autonomous bug discovery and verification intelligence system for GitHub repositories. With the completion of **Phase 5**, the system has achieved full closed-loop remediation:

$$\begin{aligned}
\text{Repository Scan} &\longrightarrow \text{Topology Graph} \longrightarrow \text{Bug Hypothesis} \longrightarrow \text{Adversarial Test} \longrightarrow \text{Sandbox Verification} \\
&\longrightarrow \mathbf{Confirmed\ Bug} \longrightarrow \mathbf{Patch\ Generation} \longrightarrow \mathbf{Isolated\ Workspace\ Application} \\
&\longrightarrow \mathbf{Dual\text{-}Phase\ Verification\ (Repro\ Fixed\ \&\ Regressions\ Passed)} \longrightarrow \mathbf{Verified\ Patch\ /\ Diff}
\end{aligned}$$

RepoSentinel now:
1. Synthesizes minimal, idiomatic, targeted code fixes (`GeneratedPatch`) specifically tailored to confirmed vulnerabilities.
2. Validates candidate patches structurally through a defensive safety validator (`PatchSafetyValidator`) to reject destructive code, credential leaks, or unauthorized file modifications.
3. Applies candidate patches exclusively within an isolated ephemeral temporary workspace (`IsolatedPatchWorkspace`). **The user's original repository is NEVER modified or contaminated.**
4. Performs **Dual-Phase Patch Verification**:
   - **Phase A (Adversarial Re-Testing)**: Re-runs the original reproduction test against the patched workspace to verify that the vulnerability is deterministically eliminated.
   - **Phase B (Functional Regression Testing)**: Executes functional tests on valid inputs to verify that legitimate system functionality was not broken by the patch.
5. Differentiates security fixes with regressions (`REGRESSION_DETECTED`) from clean, regression-free fixes (`VERIFIED`).
6. Generates standardized, ready-to-review unified diffs (`.patch` format).
7. Maintains a strict human-in-the-loop requirement: patches are autonomously verified and presented for review, but **never automatically merged or committed to the user's branch without explicit human approval**.

---

## 2. System Architecture

RepoSentinel maintains zero external runtime dependencies (Python >=3.9 standard library) and features a clean, highly modular `backend/` organization with 100% backward-compatible bridges:

```
reposentinal/
├── bin/reposentinal                  # Standalone executable CLI launcher
├── backend/                          # Modular core backend package
│   ├── __init__.py                   # Core exports & versioning (v0.5.0)
│   ├── models/                       # Data domain & representation layer
│   │   ├── __init__.py               # Re-exports models, hypothesis, and patch_models
│   │   ├── models.py                 # Core domain models (Severity, BugFinding, FileContext, ScanSummary)
│   │   ├── hypothesis.py             # BugHypothesis schema, BugStatus, Confidence & Metrics (Phase 3)
│   │   └── patch_models.py           # GeneratedPatch, PatchVerificationResult, PatchQualityMetrics (Phase 5)
│   ├── scanner/                      # Ingestion & file discovery layer
│   │   ├── __init__.py               # Re-exports scanner functions & constants
│   │   └── scanner.py                # Target cloning, directory walker, binary filter, extension map (Phase 1)
│   ├── analysis/                     # Static analysis, indexing, and hypothesis engine
│   │   ├── __init__.py               # Re-exports agent, indexer, context, engines, and providers
│   │   ├── analyzer.py               # Multi-threaded orchestrator & end-to-end pipeline coordination
│   │   ├── indexer.py                # AST Symbol Indexer & Dependency Topology Graph (Phase 2)
│   │   ├── context.py                # Repository Context Builder & Prompt Synthesizer (Phase 3)
│   │   ├── hypothesis_engine.py      # RuleBasedHypothesisEngine & LLMHypothesisEngine (Phase 3)
│   │   └── providers.py              # LLM integrations (MockProvider, GeminiProvider, OpenAIProvider)
│   ├── verification/                 # Sandboxing & adversarial verification layer
│   │   ├── __init__.py               # Re-exports verifier, sandbox backends, and test generators
│   │   ├── verification.py           # VerificationStatus, ExecutionResult, VerificationEvidence (Phase 4)
│   │   ├── verifier.py               # HypothesisVerifier & empirical confirmation engine (Phase 4)
│   │   ├── sandbox.py                # BaseSandbox, DockerSandbox, SafeSubprocessSandbox (Phase 4)
│   │   └── test_generator.py         # AdversarialTest, TestSafetyValidator, DeterministicTestGenerator (Phase 4)
│   ├── patching/                     # Remediation, safety validation, and patch verification layer
│   │   ├── __init__.py               # Re-exports patch verifier, generator, safety, workspace, and applier
│   │   ├── patch_verifier.py         # PatchVerifier: dual-phase verification & regression protection (Phase 5)
│   │   ├── patch_generator.py        # DeterministicPatchGenerator: minimal, safe patch synthesis (Phase 5)
│   │   ├── patch_safety.py           # PatchSafetyValidator: defensive security & syntax checks (Phase 5)
│   │   ├── patch_workspace.py        # IsolatedPatchWorkspace: ephemeral workspace manager (Phase 5)
│   │   └── patch_applier.py          # PatchApplier: workspace diff application & AST check (Phase 5)
│   └── cli/                          # User interface and formatting layer
│       ├── __init__.py               # Re-exports main CLI runner and reporters
│       ├── cli.py                    # Command-line interface with --topology, --no-verify, --no-patch
│       └── reporter.py               # Formatting engines (ANSI Terminal, Markdown, JSON, Patch Diffs)
├── reposentinal/                     # Backward-compatibility bridge package (preserves Phase 1-5 APIs)
│   ├── __init__.py                   # Top-level bridge forwarding to backend
│   ├── models.py, hypothesis.py, patch_models.py
│   ├── scanner.py, analyzer.py, indexer.py, context.py, hypothesis_engine.py, providers.py
│   ├── verification.py, verifier.py, sandbox.py, test_generator.py
│   ├── patch_verifier.py, patch_generator.py, patch_safety.py, patch_workspace.py, patch_applier.py
│   └── cli.py, reporter.py
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── cross_file_repo/          # Multi-file vulnerable repository fixture (auth, orders, db)
│   │   └── safe_repo/                # Safe fixture for false-positive validation
│   ├── sample_vulnerable_code.py      # Intentional vulnerability test fixture
│   ├── test_scanner.py                # Scanner, heuristic, and orchestrator unit tests
│   ├── test_indexer.py                # AST symbol extraction, resolution, and topology tests
│   ├── test_hypothesis.py             # Hypothesis schema, cross-module reasoning, resilience tests
│   ├── test_verification.py           # Adversarial generation, sandbox lifecycle, invariants tests
│   ├── test_patch.py                  # Patch generation, workspace isolation, dual-phase verification tests
│   └── test_backend_structure.py      # Modular backend architecture and subpackage isolation tests
├── pyproject.toml                    # Package configuration & standard entrypoints
└── requirements.txt                  # Zero required runtime dependencies
```

### Complete End-to-End Pipeline (Phase 5):
```
[User / CLI Target]
        │
        ▼
[scanner.prepare_target] ──(Remote URL)──► [git clone --depth 1 to tempdir]
        │
        ▼
[scanner.scan_repository] ──► Extracts FileContext objects (filtered, size-checked, text-verified)
        │
        ▼
[indexer.build_repository_index] ──► Generates Symbol Index & Dependency Topology Graph
        │
        ▼
[context.RepositoryContextBuilder] ──► Synthesizes per-file Cross-Module Relational Context
        │
        ▼
[analyzer.RepoSentinelAgent] ──► Generates Bug Hypotheses (RuleBased or LLM)
        │
        ▼
[verifier.HypothesisVerifier] ──► Synthesizes Adversarial Tests & Executes in Sandbox
        │
        ├── Exit Code 0 ──► Promotes to [Confirmed Bug]
        │
        ▼
[patch_verifier.PatchVerifier] (Automated Remediation Engine)
        │
        ├──► [patch_generator.DeterministicPatchGenerator]
        │         │
        │         ▼ Synthesizes minimal candidate GeneratedPatch
        │
        ├──► [patch_safety.PatchSafetyValidator]
        │         │
        │         ▼ Checks syntax (ast.parse), prevents destructive patterns and secret leaks
        │
        ├──► [patch_workspace.IsolatedPatchWorkspace]
        │         │
        │         ▼ Creates ephemeral tempdir (user's repo is 100% untouched)
        │
        ├──► [patch_applier.PatchApplier]
        │         │
        │         ▼ Applies patch in isolated workspace
        │
        ├──► [Phase A: Adversarial Re-Testing]
        │         │
        │         ▼ Vulnerability still reproduced?
        │           ├── YES ──► Status: VERIFICATION_FAILED
        │           └── NO  ──► Vulnerability FIXED!
        │
        ├──► [Phase B: Functional Regression Testing]
        │         │
        │         ▼ Legitimate valid calls execute successfully?
        │           ├── NO  ──► Status: REGRESSION_DETECTED
        │           └── YES ──► Status: VERIFIED!
        │
        ▼
[reporter.TerminalReporter / MarkdownReporter / JSONReporter]
- Outputs Verified Patches with colorized Unified Diffs
- Outputs Empirical Patch Quality Metrics
```

---

## 3. Patch Verification States & Decision Model

| Status | Definition | Transition Condition |
|---|---|---|
| `GENERATED` | Candidate patch synthesized. | Initial generator state before validation. |
| `VALIDATION_FAILED` | Patch rejected by safety validator. | Fails closed on syntax error, destructive command, or credential. |
| `APPLY_FAILED` | Workspace file application error. | File missing or cannot be written in temporary workspace. |
| `APPLIED` | Successfully applied in workspace. | File updated and verified by AST parser. |
| `VULNERABILITY_FIXED` | Adversarial test no longer reproduces. | Intermediate state indicating exploit is mitigated. |
| `REGRESSION_DETECTED` | Vulnerability fixed, but breaks valid calls. | Legitimate input tests fail after patch application. |
| `VERIFICATION_FAILED` | Vulnerability still reproduces after patch. | Adversarial test continues to trigger vulnerability. |
| `VERIFIED` | Exploit eliminated AND all regressions pass. | Dual-phase verification confirmed deterministically. |
| `INCONCLUSIVE` | Hypothesis unconfirmed or generator missing. | Patch cannot proceed without confirmed reproduction. |

---

## 4. Critical Invariants

1. **Workspace Isolation**: A patch cannot become `VERIFIED` unless it was applied and tested inside an isolated temporary workspace. The user's host repository files are never modified.
2. **Deterministic Mitigated Exploit**: A patch cannot become `VERIFIED` unless the original adversarial reproduction test is re-run and proves the vulnerability is no longer reproducible.
3. **Regression Protection**: A patch cannot become `VERIFIED` if required functional regression tests fail on legitimate inputs.
4. **Anti-Hallucination**: LLM output alone can never mark a patch as `VERIFIED`. Only deterministic sandbox execution evidence can grant this status.
5. **No Automatic Commits**: Candidate patches are presented as verified unified diffs for human review; RepoSentinel never commits, pushes, or merges without explicit human approval.

---

## 5. Test Suite & Verification Status

Automated test execution: `python3 -m unittest discover tests`

- `test_deterministic_patch_generation_null_assumption`: Validates minimal null guard synthesis.
- `test_patch_safety_validator_rejects_destructive_patterns`: Confirms rejection of `rmtree`, `rm -rf`, `os.remove`.
- `test_patch_safety_validator_rejects_credentials`: Confirms rejection of hardcoded tokens and secrets.
- `test_patch_safety_validator_rejects_syntax_errors`: Confirms rejection of broken Python syntax.
- `test_patch_safety_validator_rejects_protected_system_paths`: Confirms rejection of attempts to alter CI/CD or RepoSentinel internals.
- `test_isolated_workspace_lifecycle_and_immutability`: Confirms original host repository files are 100% byte-for-byte identical before, during, and after patch verification.
- `test_patch_applier_verifies_clean_syntax`: Validates workspace file write and AST verification.
- `test_successful_patch_verification_dual_phase`: Proves dual-phase verification (`order_service.py` vulnerability fixed + regression passed -> `VERIFIED`).
- `test_regression_detected_when_patch_breaks_valid_calls`: Proves that a patch breaking valid checkouts is flagged as `REGRESSION_DETECTED` and refused `VERIFIED`.
- `test_verification_failed_when_vulnerability_still_reproduces`: Proves that an ineffective patch is classified as `VERIFICATION_FAILED`.
- `test_invariant_unconfirmed_hypothesis_rejected_for_patching`: Confirms unconfirmed hypotheses cannot receive verified patches.
- `test_end_to_end_agent_with_patching`: Validates complete `RepoSentinelAgent` run with `--patch`.
- All 27 Phase 1–4 unit and integration tests.

**Total**: `39/39 tests passing (100%) in 2.65s`.

---

## 6. Patch Quality Metrics

When executed with patching enabled, RepoSentinel outputs empirical research metrics:
- `patches_generated`: Total candidate patches synthesized.
- `patches_validated`: Patches passing safety validation.
- `patches_applied`: Patches successfully applied to isolated workspaces.
- `patches_verified`: Patches with confirmed vulnerability mitigation and zero regressions.
- `regression_detected_count`: Fixes that inadvertently broke legitimate functionality.
- `vulnerability_fix_rate`: Ratio of mitigated exploits to applied patches.
- `patch_verification_rate`: Ratio of fully verified regression-free patches to generated patches.
- `total_lines_added` / `total_lines_removed`: Patch size metrics.
- `average_patch_time` / `average_verification_time`: Efficiency metrics.

---

## 7. Next Planned Phase

### Phase 6: Interactive Developer Review & PR Bot
- Interactive terminal review prompt (`[y] Apply Patch | [n] Discard | [e] Edit Diff`).
- Automated GitHub Pull Request comment bot to post verified patch diffs directly onto GitHub pull requests.
- Optional branch patch committer with signed commits.

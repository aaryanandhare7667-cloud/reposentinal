import React from 'react';
import { 
  BookOpen, 
  ShieldCheck, 
  Terminal, 
  GitPullRequest, 
  Network, 
  FileCode, 
  CheckCircle2, 
  AlertTriangle,
  Lock,
  Layers,
  ArrowRight,
  Code
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export default function MethodPage() {
  const stages = [
    {
      num: 1,
      title: 'Repository Scan & AST Symbol Indexing',
      category: 'Phase 1 & 2',
      borderStyle: 'border-slate-800',
      description: 'Parses Python source files using standard library AST (`ast.parse`). Indexes classes, functions, async methods, signatures, docstrings, and cross-file import statements into an in-memory symbol table without executing untrusted code.'
    },
    {
      num: 2,
      title: 'Repository Topology & Call Graph Construction',
      category: 'Phase 2',
      borderStyle: 'border-slate-800',
      description: 'Builds cross-file caller and callee edges. Resolves inter-module imports and maps potential data-flow paths from HTTP controller entry points down to database, filesystem, or shell execution sinks.'
    },
    {
      num: 3,
      title: 'Repository-Aware Hypothesis Synthesis',
      category: 'Phase 3 (AI Generated)',
      borderStyle: 'border-dashed border-indigo-400/50',
      badge: 'Dashed Border = AI Claim',
      description: 'Synthesizes bug hypotheses by inspecting symbol call chains and source code contexts. Formulates a concrete failure condition and theoretical exploit payload, marked strictly as a theoretical hypothesis.'
    },
    {
      num: 4,
      title: 'Targeted Adversarial Test Synthesis',
      category: 'Phase 4 (AI Generated)',
      borderStyle: 'border-dashed border-indigo-400/50',
      badge: 'Dashed Border = AI Test',
      description: 'Generates a standalone Python unit test designed specifically to trigger the hypothetical failure branch. The test imports the target module and asserts vulnerability behavior without side effects.'
    },
    {
      num: 5,
      title: 'Ephemeral Sandboxed Verification',
      category: 'Phase 4 (Runtime Empirical)',
      borderStyle: 'border-solid border-emerald-500/50',
      badge: 'Solid Border = Runtime Evidence',
      description: 'Executes the adversarial test script inside an isolated process jail with airgapped network sockets, strict 15-second CPU timeouts, and read-only host mounts. Captures stdout, stderr, and exit code. Only an empirical test failure confirms the bug.'
    },
    {
      num: 6,
      title: 'Smallest Safe Patch Synthesis & Safety Validation',
      category: 'Phase 5 (AI + Static Guards)',
      borderStyle: 'border-dashed border-indigo-400/50',
      badge: 'Candidate Patch',
      description: 'Synthesizes minimal unified diff targeting only the vulnerable symbol (e.g. parameterized SQL query). Validates unified diff syntax, target file existence, scope restriction, absence of destructive commands, and secret-leak guards.'
    },
    {
      num: 7,
      title: 'Dual-Phase Regression & Patch Verification',
      category: 'Phase 5 (Runtime Empirical)',
      borderStyle: 'border-solid border-emerald-500/50',
      badge: 'Verified Patch',
      description: 'Applies candidate patch exclusively inside a temporary scratch workspace. Executes reproduction test (must now pass) and runs existing repository regression test suite (must have zero failures). Only then is the patch labeled Verified.'
    }
  ];

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Intelligence', to: '/findings' },
          { label: 'Methodology & Invariants', to: '/method' }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-indigo-400" />
            RepoSentinel Autonomous Methodology
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Empirical runtime verification, zero-hallucination guardrails, and isolated patch synthesis invariants.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="text-xs font-mono px-3 py-1.5 rounded bg-emerald-950/20 border border-emerald-500/40 text-emerald-400">
            System Invariant: Zero Hallucinated Claims
          </div>
        </div>
      </div>

      {/* Security UX Core Principle Banner */}
      <Card title="Design System & Security UX Invariant: Dashed vs. Solid Borders">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div className="p-4 rounded-lg bg-indigo-950/20 border border-dashed border-indigo-400/60">
            <div className="flex items-center gap-2 text-indigo-300 font-mono text-xs font-semibold uppercase">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-400" />
              Dashed Border = AI-Generated Claim / Artifact
            </div>
            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
              Applied to theoretical bug hypotheses, generated adversarial test scripts, and candidate patches. Never presented as confirmed vulnerability evidence or a validated fix until runtime execution proves it.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-emerald-950/20 border border-solid border-emerald-500/60">
            <div className="flex items-center gap-2 text-emerald-300 font-mono text-xs font-semibold uppercase">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              Solid Border = Executed / Observed Runtime Evidence
            </div>
            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
              Applied exclusively to empirical evidence gathered inside isolated sandbox runs (exit codes, captured stdout/stderr traces, confirmed reproduction runs, and regression-tested patches).
            </p>
          </div>
        </div>
      </Card>

      {/* 7-Stage Pipeline Details */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 font-mono">
          The 7-Stage Autonomous Pipeline Architecture
        </h3>

        <div className="space-y-3">
          {stages.map((stage) => (
            <div 
              key={stage.num}
              className={`p-4 rounded-lg bg-slate-900/60 ${stage.borderStyle} transition-colors`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-slate-800 text-indigo-400 font-mono text-xs flex items-center justify-center font-bold">
                    {stage.num}
                  </span>
                  <span className="text-sm font-bold text-white font-mono">{stage.title}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono text-slate-400">{stage.category}</span>
                  {stage.badge && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {stage.badge}
                    </span>
                  )}
                </div>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed pl-9">
                {stage.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Operational Invariants */}
      <Card title="Repository & Execution Safety Invariants">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3 rounded bg-slate-950 border border-slate-800">
            <div className="text-emerald-400 font-semibold mb-1">1. ZERO USER REPO MUTATION</div>
            <div className="text-slate-400">
              All scans are read-only. Test runs and patch evaluations take place exclusively in isolated ephemeral scratch directories.
            </div>
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800">
            <div className="text-emerald-400 font-semibold mb-1">2. SMALLEST SAFE CHANGE</div>
            <div className="text-slate-400">
              Patches prefer parameterized APIs over string sanitization; whole-file rewrites are rejected by the safety validator.
            </div>
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800">
            <div className="text-emerald-400 font-semibold mb-1">3. STRICT RE-TEST INVARIANT</div>
            <div className="text-slate-400">
              A patch is never marked "Verified" unless the original reproduction test now succeeds and existing test suites pass.
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

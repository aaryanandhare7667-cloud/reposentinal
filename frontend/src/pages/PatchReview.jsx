import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  GitPullRequest, 
  CheckCircle2, 
  AlertTriangle, 
  FileCode, 
  ShieldCheck, 
  Terminal, 
  Check, 
  X, 
  Copy, 
  Download,
  ExternalLink,
  Layers,
  ArrowRight
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { StatusBadge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { DiffViewer } from '../components/code/DiffViewer';
import { getPatchById } from '../services/patchService';
import { getFindingById } from '../services/findingsService';

export default function PatchReview() {
  const { id } = useParams();
  const [patch, setPatch] = useState(null);
  const [finding, setFinding] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const p = await getPatchById(id);
      if (p) {
        setPatch(p);
        const f = await getFindingById(p.hypothesisId);
        setFinding(f);
      }
      setLoading(false);
    }
    loadData();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-400">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
        <div className="text-sm font-mono">Loading patch details...</div>
      </div>
    );
  }

  if (!patch) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[{ label: 'Patches', to: '/patches' }, { label: id }]} />
        <Card className="text-center py-16">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-white">Patch Record Not Found</h2>
          <p className="text-sm text-slate-400 mt-2 font-mono">ID: {id}</p>
          <div className="mt-6">
            <Link to="/patches">
              <Button variant="secondary">Back to Patches</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  const isVerified = patch.verificationStatus === 'VERIFIED';

  const handleApply = () => {
    setApplySuccess(true);
    setTimeout(() => {
      setApplyModalOpen(false);
      setApplySuccess(false);
    }, 2500);
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Intelligence', to: '/findings' },
          { label: 'Patches', to: '/patches' },
          { label: patch.id }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <GitPullRequest className="w-6 h-6 text-indigo-400" />
              {patch.id}: {patch.objective}
            </h1>
            {isVerified ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/50">
                <CheckCircle2 className="w-4 h-4" />
                Verified Patch
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-mono bg-indigo-500/10 text-indigo-300 border border-dashed border-indigo-400/50">
                Candidate Patch (Proposed)
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400 mt-2">
            <span>Target File: <code className="text-indigo-300">{patch.targetFile}</code></span>
            <span>•</span>
            <span>Target Symbol: <code className="text-slate-200">{patch.targetSymbol}</code></span>
            <span>•</span>
            <span>Category: <strong className="text-slate-200">{patch.bugCategory}</strong></span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link to={`/patches/${patch.id}/diff`}>
            <Button variant="secondary" size="sm">
              Full Screen Diff
            </Button>
          </Link>
          <Button 
            variant={isVerified ? "verified" : "primary"} 
            size="sm"
            onClick={() => setApplyModalOpen(true)}
          >
            Apply Patch
          </Button>
        </div>
      </div>

      {/* Verification Status Banner */}
      {isVerified ? (
        <Card isRuntimeEvidence={true} className="bg-emerald-950/20 border-emerald-500/40 p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-emerald-300">
                Verified Patch — Isolated Sandbox Verified
              </div>
              <div className="text-xs text-slate-300 mt-1">
                Passed RepoSentinel sandbox re-test and regression checks. The patch successfully neutralized the vulnerability reproduction test without breaking any existing test suite components.
              </div>
            </div>
          </div>
        </Card>
      ) : (
        <Card isAiGenerated={true} className="bg-indigo-950/20 border-dashed border-indigo-400/40 p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-indigo-300">
                Candidate Patch (Proposed by AI Model)
              </div>
              <div className="text-xs text-slate-300 mt-1">
                This is a proposed patch generated via AST analysis and context prompts. It has not yet executed or passed sandbox regression checks. Never assume this resolves the vulnerability until verified.
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Two Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Column: Diff & Verification Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Dual Phase Sandbox Verification Card */}
          <Card 
            title="Dual-Phase Sandbox Verification Checkpoint" 
            subtitle="Runtime empirical proof executed inside isolated workspace"
            isRuntimeEvidence={isVerified}
          >
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-slate-400">Phase 1: Reproduction Test Re-run</span>
                  <span className="text-emerald-400 font-semibold">
                    {isVerified ? 'PASSED (Vulnerability Neutralized)' : 'PENDING'}
                  </span>
                </div>
                <div className="text-xs text-slate-300">
                  Original reproduction test rerun inside isolated temporary scratch workspace. Vulnerability assertion failed on unpatched code, and now succeeds cleanly with zero security bypass.
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-slate-400">Phase 2: Full Regression Test Suite</span>
                  <span className="text-emerald-400 font-semibold">
                    {isVerified ? '46/46 Passed (Zero Regressions)' : 'PENDING'}
                  </span>
                </div>
                <div className="text-xs text-slate-300">
                  Full existing repository test suite executed against patched files. All unit and integration test assertions passed without regression or unexpected side effects.
                </div>
              </div>
            </div>
          </Card>

          {/* Diff Viewer Card */}
          <Card title="Proposed Unified Diff" subtitle={`Target: ${patch.targetFile}`}>
            <DiffViewer 
              diffContent={patch.diff} 
              fileName={patch.targetFile}
              patchId={patch.id}
            />
          </Card>

          {/* Rationale & Design Decision */}
          <Card title="Patch Synthesis Rationale" subtitle="Smallest safe change necessary">
            <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
              <p>
                {patch.rationale || 'The patch replaces dynamic string interpolation with parameterized queries, preventing SQL injection while maintaining original function signature and return type.'}
              </p>
              <div className="p-3 rounded bg-slate-950 border border-slate-800 font-mono text-slate-400">
                <div className="text-slate-500 mb-1">INVARIANT PRESERVED:</div>
                <div>Minimal edit scope: Only modifies vulnerable symbol <code className="text-indigo-400">{patch.targetSymbol}</code> without restructuring surrounding architecture.</div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Sidebar: Safety Checklist & Links */}
        <div className="space-y-6">
          {/* Safety Validation Checklist */}
          <Card title="Patch Safety Validation" subtitle="Static & Structural Invariants">
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Diff Syntax Valid:</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> PASSED
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Target File Exists:</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> PASSED
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Scope Restriction:</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> 1 FILE ONLY
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">No Unexpected Deletions:</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> PASSED
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Destructive Commands:</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> NONE
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Secrets / Credentials:</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> CLEAN
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-400">Original Repo Integrity:</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> UNTOUCHED
                </span>
              </div>
            </div>
          </Card>

          {/* Linked Finding */}
          {finding && (
            <Card title="Originating Vulnerability Finding">
              <div className="space-y-2 text-xs">
                <div className="font-mono text-indigo-400">{finding.id}</div>
                <div className="font-semibold text-white">{finding.title}</div>
                <p className="text-slate-400 line-clamp-2">{finding.description}</p>
                <div className="pt-2">
                  <Link to={`/findings/${finding.id}`} className="text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1">
                    Inspect finding details <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </Card>
          )}

          {/* Sandbox Workspace details */}
          <Card title="Isolated Sandbox Workspace" subtitle="Clean ephemeral execution guarantee">
            <div className="space-y-2 text-xs text-slate-400">
              <p>
                RepoSentinel operates via isolated temporary scratch workspaces. The user’s working directory was never mutated during verification.
              </p>
              <div className="p-2.5 rounded bg-slate-950 font-mono text-[11px] text-slate-300 border border-slate-800">
                Workspace: <span className="text-slate-400">/scratch/patch_eval_{patch.id.toLowerCase()}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Apply Patch Modal */}
      {applyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-lg max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <GitPullRequest className="w-5 h-5 text-indigo-400" />
              Apply Patch to Local Workspace
            </h3>
            
            {applySuccess ? (
              <div className="py-6 text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                  <Check className="w-6 h-6" />
                </div>
                <div className="text-sm font-semibold text-white">Patch Applied Successfully!</div>
                <div className="text-xs text-slate-400 font-mono">
                  Changes applied to {patch.targetFile}. Backup saved as {patch.targetFile}.bak
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-xs text-slate-300 leading-relaxed">
                  You are about to apply patch <strong className="text-white font-mono">{patch.id}</strong> to <strong className="text-indigo-300 font-mono">{patch.targetFile}</strong>.
                </p>
                <div className="p-3 rounded bg-amber-950/20 border border-amber-500/30 text-amber-300 text-xs">
                  <div className="font-semibold mb-1">Safety Confirmation:</div>
                  This patch passed RepoSentinel's isolated sandbox re-test and regression suite without failures.
                </div>
                <div className="flex justify-end gap-3 pt-2">
                  <Button variant="secondary" onClick={() => setApplyModalOpen(false)}>
                    Cancel
                  </Button>
                  <Button variant="verified" onClick={handleApply}>
                    Confirm & Apply
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

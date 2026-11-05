import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  GitPullRequest, 
  CheckCircle2, 
  AlertTriangle, 
  Download, 
  Copy, 
  Check, 
  ArrowLeft,
  FileCode,
  ShieldCheck,
  Code
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { DiffViewer } from '../components/code/DiffViewer';
import { getPatchById } from '../services/patchService';

export default function DiffViewerPage() {
  const { id } = useParams();
  const [patch, setPatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function loadPatch() {
      setLoading(true);
      const data = await getPatchById(id);
      setPatch(data);
      setLoading(false);
    }
    loadPatch();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-400">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
        <div className="text-sm font-mono">Loading unified diff viewer...</div>
      </div>
    );
  }

  if (!patch) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[{ label: 'Patches', to: '/patches' }, { label: id }]} />
        <Card className="text-center py-16">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-white">Patch Diff Not Found</h2>
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

  const handleCopy = () => {
    navigator.clipboard.writeText(patch.diff);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([patch.diff || patch.finalDiff || ''], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const fileName = (patch.targetFile || patch.target_file || 'patch').split('/').pop();
    const patchId = (patch.id || 'patch').toLowerCase();
    link.download = `${patchId}_${fileName}.patch`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Intelligence', to: '/findings' },
          { label: 'Patches', to: '/patches' },
          { label: patch.id, to: `/patches/${patch.id}` },
          { label: 'Unified Diff' }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <Link to={`/patches/${patch.id}`}>
              <Button variant="ghost" size="sm" className="p-1.5">
                <ArrowLeft className="w-4 h-4 text-slate-400" />
              </Button>
            </Link>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <FileCode className="w-6 h-6 text-indigo-400" />
              Unified Diff: {patch.targetFile || patch.target_file || 'order_service.py'}
            </h1>
            {isVerified ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/50">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Verified Patch
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-mono bg-indigo-500/10 text-indigo-300 border border-dashed border-indigo-400/50">
                Candidate Patch (Proposed)
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400 mt-2">
            <span>Patch ID: <strong className="text-white">{patch.id}</strong></span>
            <span>•</span>
            <span>Target Symbol: <code className="text-indigo-300">{patch.targetSymbol}</code></span>
            <span>•</span>
            <span>Objective: <span className="text-slate-300">{patch.objective}</span></span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={handleCopy}>
            {copied ? <Check className="w-4 h-4 text-emerald-400 mr-1.5" /> : <Copy className="w-4 h-4 mr-1.5" />}
            {copied ? 'Copied Diff' : 'Copy Diff'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="w-4 h-4 mr-1.5" />
            Download .patch
          </Button>
          <Link to={`/patches/${patch.id}`}>
            <Button variant="primary" size="sm">
              Review Details
            </Button>
          </Link>
        </div>
      </div>

      {/* Verification State Banner */}
      {isVerified ? (
        <Card isRuntimeEvidence={true} className="bg-emerald-950/20 border-emerald-500/40 p-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div className="text-xs text-slate-200">
              <strong className="text-emerald-400">Verified Patch:</strong> Passed RepoSentinel sandbox re-test and regression checks. This unified diff was verified inside an ephemeral isolated workspace.
            </div>
          </div>
        </Card>
      ) : (
        <Card isAiGenerated={true} className="bg-indigo-950/20 border-dashed border-indigo-400/40 p-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-indigo-400 shrink-0" />
            <div className="text-xs text-slate-200">
              <strong className="text-indigo-300">Candidate Patch (Proposed):</strong> This diff has not yet been verified by isolated sandbox execution. Do not apply directly to production.
            </div>
          </div>
        </Card>
      )}

      {/* Full Screen Diff Viewer */}
      <Card title="Patch File Changes" subtitle={`--- a/${patch.targetFile} +++ b/${patch.targetFile}`}>
        <DiffViewer 
          diffContent={patch.diff} 
          fileName={patch.targetFile}
          patchId={patch.id}
        />
      </Card>

      {/* Footer Notes */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-lg bg-slate-900/40 border border-slate-800 text-xs text-slate-400 font-mono">
        <div>
          Minimal safe modification policy applied: Zero unrelated files or surrounding lines modified.
        </div>
        <div className="text-slate-500">
          Format: Git Unified Diff v2 (POSIX compliant)
        </div>
      </div>
    </div>
  );
}

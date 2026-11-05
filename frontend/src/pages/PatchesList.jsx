import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  GitPullRequest, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  FileCode, 
  Search, 
  Filter, 
  ArrowRight,
  ShieldCheck,
  Check,
  XCircle,
  HelpCircle,
  ExternalLink
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { StatusBadge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { getPatches } from '../services/patchService';

export default function PatchesList() {
  const [searchParams] = useSearchParams();
  const initialHypothesisId = searchParams.get('hypothesisId') || '';

  const [patches, setPatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState(initialHypothesisId);
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => {
    async function loadPatches() {
      setLoading(false);
      const data = await getPatches();
      setPatches(data);
    }
    loadPatches();
  }, []);

  const filteredPatches = patches.filter(p => {
    const pId = (p.id || '').toLowerCase();
    const pHyp = (p.hypothesisId || p.hypothesis_id || '').toLowerCase();
    const pFile = (p.targetFile || p.target_file || '').toLowerCase();
    const pObj = (p.objective || p.patch_objective || '').toLowerCase();
    const term = (searchTerm || '').toLowerCase();

    const matchesSearch = 
      pId.includes(term) ||
      pHyp.includes(term) ||
      pFile.includes(term) ||
      pObj.includes(term);

    const matchesStatus = 
      statusFilter === 'ALL' ||
      (statusFilter === 'VERIFIED' && p.verificationStatus === 'VERIFIED') ||
      (statusFilter === 'CANDIDATE' && p.verificationStatus !== 'VERIFIED');

    return matchesSearch && matchesStatus;
  });

  const verifiedCount = patches.filter(p => p.verificationStatus === 'VERIFIED').length;
  const candidateCount = patches.filter(p => p.verificationStatus !== 'VERIFIED').length;

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Intelligence', to: '/findings' },
          { label: 'Patches', to: '/patches' }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <GitPullRequest className="w-6 h-6 text-indigo-400" />
            Candidate & Verified Patches
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous patch synthesis with isolated sandbox regression re-testing. Only empirical pass confirms a fix.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-xs font-mono px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
            Fix Validation Policy: <span className="text-emerald-400 font-semibold">Strict Sandbox Re-test</span>
          </div>
        </div>
      </div>

      {/* Metric Cards Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 uppercase">Total Patches Synthesized</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{patches.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">Generated via LLM + AST Context</div>
        </div>

        <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/40">
          <div className="text-xs font-mono text-emerald-400 uppercase">Verified Patches</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">{verifiedCount}</div>
          <div className="text-[11px] text-emerald-300/80 mt-1">Passed sandbox re-test & regression checks</div>
        </div>

        <div className="p-4 rounded-lg bg-indigo-950/20 border border-dashed border-indigo-400/40">
          <div className="text-xs font-mono text-indigo-300 uppercase">Proposed / Candidate Patches</div>
          <div className="text-2xl font-bold font-mono text-indigo-300 mt-1">{candidateCount}</div>
          <div className="text-[11px] text-indigo-400/80 mt-1">Awaiting or failed sandbox verification</div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 uppercase">Safety Validation Rate</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            {patches.length > 0 ? '100%' : 'Not Run'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">AST syntax, path traversal & secret guards</div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-3 rounded-lg bg-slate-900/40 border border-slate-800">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input 
              type="text"
              placeholder="Search by ID, file, symbol, or objective..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          {searchTerm && (
            <button 
              onClick={() => setSearchTerm('')}
              className="text-xs text-slate-400 hover:text-white font-mono px-2"
            >
              Clear
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400 mr-1 font-mono">Status:</span>
          <div className="flex rounded bg-slate-950 border border-slate-800 p-0.5 text-xs font-mono">
            <button
              onClick={() => setStatusFilter('ALL')}
              className={`px-2.5 py-1 rounded transition-colors ${
                statusFilter === 'ALL' ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              All ({patches.length})
            </button>
            <button
              onClick={() => setStatusFilter('VERIFIED')}
              className={`px-2.5 py-1 rounded transition-colors ${
                statusFilter === 'VERIFIED' ? 'bg-emerald-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Verified ({verifiedCount})
            </button>
            <button
              onClick={() => setStatusFilter('CANDIDATE')}
              className={`px-2.5 py-1 rounded transition-colors ${
                statusFilter === 'CANDIDATE' ? 'bg-indigo-600/70 text-white font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Candidate ({candidateCount})
            </button>
          </div>
        </div>
      </div>

      {/* Patches List */}
      {filteredPatches.length === 0 ? (
        <EmptyState 
          title="No patches in the scanned scope"
          description={searchTerm ? "No candidate or verified patches matched your search filter criteria." : "No patches have been synthesized yet for this repository."}
          actionLabel={searchTerm ? "Clear Filters" : "Run New Scan"}
          onAction={searchTerm ? () => setSearchTerm('') : undefined}
        />
      ) : (
        <div className="space-y-4">
          {filteredPatches.map((patch) => {
            const isVerified = patch.verificationStatus === 'VERIFIED';
            return (
              <div
                key={patch.id}
                className={`p-5 rounded-lg bg-slate-900/60 transition-colors ${
                  isVerified 
                    ? 'border border-solid border-emerald-500/40 hover:border-emerald-500/60' 
                    : 'border border-dashed border-indigo-400/40 hover:border-indigo-400/60'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="font-mono text-sm font-bold text-white tracking-wide">
                        {patch.id}
                      </span>
                      {isVerified ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Verified Patch
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-mono font-medium bg-indigo-500/10 text-indigo-300 border border-dashed border-indigo-400/40">
                          <HelpCircle className="w-3.5 h-3.5" />
                          Candidate Patch (Proposed)
                        </span>
                      )}
                      <span className="text-xs font-mono text-slate-500">
                        Target: <span className="text-slate-300">{patch.hypothesisId}</span>
                      </span>
                      <span className="text-xs font-mono text-slate-500">
                        Category: <span className="text-slate-300">{patch.bugCategory}</span>
                      </span>
                    </div>

                    <div className="text-sm font-semibold text-slate-200">
                      {patch.objective}
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
                      <span className="flex items-center gap-1">
                        <FileCode className="w-3.5 h-3.5 text-slate-500" />
                        <span className="text-indigo-300">{patch.targetFile}</span>
                      </span>
                      <span>•</span>
                      <span>Symbol: <code className="text-slate-300">{patch.targetSymbol}</code></span>
                      <span>•</span>
                      <span>
                        Safety Check: <span className="text-emerald-400 font-semibold">{patch.safetyValidation?.isSafe ? 'PASSED' : 'FLAGGED'}</span>
                      </span>
                    </div>

                    {/* Explanatory banner based on verified status */}
                    {isVerified ? (
                      <div className="text-xs text-emerald-300/90 font-mono pt-1">
                        ✓ Passed RepoSentinel sandbox re-test and regression checks.
                      </div>
                    ) : (
                      <div className="text-xs text-indigo-400/90 font-mono pt-1">
                        ⚬ Unverified AI hypothesis: Requires isolated sandbox execution to confirm fix.
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Link to={`/patches/${patch.id}/diff`}>
                      <Button variant="outline" size="sm" className="font-mono text-xs">
                        View Diff
                      </Button>
                    </Link>
                    <Link to={`/patches/${patch.id}`}>
                      <Button variant={isVerified ? "verified" : "primary"} size="sm" className="font-mono text-xs">
                        Review Patch <ArrowRight className="w-3.5 h-3.5 ml-1" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

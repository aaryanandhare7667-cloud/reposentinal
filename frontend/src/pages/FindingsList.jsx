import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bug, Search, Filter, FlaskConical, Wrench, ShieldCheck, Sparkles } from 'lucide-react';
import { Card } from '../components/common/Card';
import { SeverityBadge, StatusBadge } from '../components/common/Badge';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { findingsService } from '../services/findingsService';

export function FindingsList() {
  const [findings, setFindings] = useState([]);
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => {
    async function loadFindings() {
      const data = await findingsService.getFindings();
      setFindings(data);
    }
    loadFindings();
  }, []);

  const filtered = findings.filter((f) => {
    const fileStr = f.affectedFile || f.file || '';
    const symStr = f.affectedSymbol || f.symbol || '';
    const titleStr = f.title || '';
    const matchesSearch =
      titleStr.toLowerCase().includes(search.toLowerCase()) ||
      fileStr.toLowerCase().includes(search.toLowerCase()) ||
      symStr.toLowerCase().includes(search.toLowerCase());
    const matchesSev = severityFilter === 'ALL' || f.severity === severityFilter;
    const matchesStatus =
      statusFilter === 'ALL' ||
      (statusFilter === 'CONFIRMED' && (f.status === 'Confirmed Bug' || f.isVerified)) ||
      (statusFilter === 'AI_CLAIM' && (f.isAiGenerated || !f.isVerified));
    return matchesSearch && matchesSev && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Findings' }]} />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <h1 className="text-lg font-bold text-text-primary tracking-tight">
            Security Findings & Hypotheses
          </h1>
          <p className="text-xs text-text-muted mt-1 font-mono">
            Empirical runtime evidence (solid) vs AI-generated hypotheses (dashed).
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-3 rounded bg-bg-card border border-border flex flex-wrap items-center gap-3 text-xs font-mono">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter by title, symbol, or filename..."
            className="w-full pl-8 pr-3 py-1.5 bg-bg-surface border border-border rounded text-text-primary focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono text-xs"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-text-muted text-[11px] uppercase">Severity:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-bg-surface border border-border rounded text-text-primary focus:outline-none text-xs font-mono"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-text-muted text-[11px] uppercase">Verification:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-bg-surface border border-border rounded text-text-primary focus:outline-none text-xs font-mono"
          >
            <option value="ALL">All Statuses</option>
            <option value="CONFIRMED">Confirmed Bugs (Solid)</option>
            <option value="AI_CLAIM">AI Hypotheses (Dashed)</option>
          </select>
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="p-12 text-center rounded bg-bg-card border border-border text-xs font-mono text-text-muted">
            No findings in the scanned scope
          </div>
        ) : (
          filtered.map((f) => (
          <div
            key={f.id}
            className={`p-4 rounded bg-bg-card transition-colors ${
              f.isRuntimeEvidence
                ? 'border border-solid border-emerald-500/50 hover:border-emerald-400'
                : 'border border-dashed border-indigo-400/50 hover:border-indigo-300'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-2">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono text-brand-400 font-semibold">{f.id}</span>
                  <Link
                    to={`/findings/${f.id}`}
                    className="text-sm font-semibold text-text-primary hover:text-brand-400"
                  >
                    {f.title}
                  </Link>
                </div>
                <div className="flex items-center gap-2 mt-1 text-xs font-mono text-text-muted">
                  <span className="text-text-secondary">{f.affectedFile}:{f.lineStart}</span>
                  <span>•</span>
                  <span>{f.affectedSymbol}</span>
                  <span>•</span>
                  <span className="text-text-muted">{f.category}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <SeverityBadge severity={f.severity} />
                <StatusBadge
                  status={f.status}
                  isAiGenerated={f.isAiGenerated}
                  isRuntimeEvidence={f.isRuntimeEvidence}
                />
              </div>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed mb-3">
              {f.explanation}
            </p>

            <div className="pt-2 border-t border-border flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-4">
                {f.verificationEvidenceId ? (
                  <Link
                    to={`/verification/${f.verificationEvidenceId}`}
                    className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1.5"
                  >
                    <FlaskConical className="w-3.5 h-3.5" />
                    <span>Sandbox Evidence (Reproduced)</span>
                  </Link>
                ) : (
                  <span className="text-text-muted flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                    <span>AI Claim (Unverified)</span>
                  </span>
                )}
              </div>

              {f.patchId ? (
                <Link
                  to={`/patches/${f.patchId}/diff`}
                  className="text-emerald-400 hover:text-emerald-300 flex items-center gap-1.5"
                >
                  <Wrench className="w-3.5 h-3.5" />
                  <span>Inspect Verified Patch & Diff</span>
                </Link>
              ) : (
                <span className="text-text-muted">Patch Unavailable</span>
              )}
            </div>
          </div>
        )))}
      </div>
    </div>
  );
}

export default FindingsList;

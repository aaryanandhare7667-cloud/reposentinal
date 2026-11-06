import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  FolderGit2, 
  GitBranch, 
  Clock, 
  Play, 
  Network, 
  ShieldCheck, 
  AlertTriangle,
  ExternalLink,
  ArrowRight,
  GitPullRequest
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { StatusBadge, SeverityBadge } from '../components/common/Badge';
import { getRepositoryById } from '../services/repositoryService';
import { getScans } from '../services/scanService';
import { getFindings } from '../services/findingsService';

export default function RepositoryDetail() {
  const { id } = useParams();
  const [repo, setRepo] = useState(null);
  const [scans, setScans] = useState([]);
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const r = await getRepositoryById(id);
      setRepo(r);
      const allScans = await getScans();
      setScans(allScans);
      const allFindings = await getFindings();
      setFindings(allFindings);
      setLoading(false);
    }
    loadData();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-400">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
        <div className="text-sm font-mono">Loading repository details...</div>
      </div>
    );
  }

  if (!repo) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[{ label: 'Repositories', to: '/repositories' }, { label: id }]} />
        <Card className="text-center py-16">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-white">Repository Not Found</h2>
          <p className="text-sm text-slate-400 mt-2 font-mono">ID: {id}</p>
          <div className="mt-6">
            <Link to="/repositories">
              <Button variant="secondary">Back to Repositories</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Intelligence', to: '/repositories' },
          { label: 'Repositories', to: '/repositories' },
          { label: repo.name }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <FolderGit2 className="w-6 h-6 text-indigo-400" />
              {repo.name}
            </h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
              Branch: {repo.defaultBranch || 'main'}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400 mt-2">
            <span>Path: <strong className="text-slate-300">{repo.path}</strong></span>
            {repo.url && (
              <>
                <span>•</span>
                <a href={repo.url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                  GitHub <ExternalLink className="w-3 h-3" />
                </a>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link to={`/topology`}>
            <Button variant="outline" size="sm">
              <Network className="w-3.5 h-3.5 mr-1" /> Topology
            </Button>
          </Link>
          <Link to={`/scans/new?repo=${repo.id}`}>
            <Button variant="primary" size="sm">
              <Play className="w-3.5 h-3.5 mr-1" /> Run Scan
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400">INDEXED FILES</div>
          <div className="text-xl font-bold font-mono text-white mt-1">24 Files</div>
          <div className="text-[11px] text-slate-500 mt-1">Python AST parsed</div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400">AST SYMBOLS</div>
          <div className="text-xl font-bold font-mono text-indigo-400 mt-1">142 Symbols</div>
          <div className="text-[11px] text-slate-500 mt-1">Classes & Functions</div>
        </div>

        <div className="p-4 rounded-lg bg-rose-950/20 border border-rose-500/30">
          <div className="text-xs font-mono text-rose-400">CONFIRMED VULNERABILITIES</div>
          <div className="text-xl font-bold font-mono text-rose-300 mt-1">
            {repo.stats?.verifiedFindings || 0} Bugs
          </div>
          <div className="text-[11px] text-rose-400/80 mt-1">Sandbox verified</div>
        </div>

        <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/30">
          <div className="text-xs font-mono text-emerald-400">VERIFIED PATCHES</div>
          <div className="text-xl font-bold font-mono text-emerald-300 mt-1">
            {repo.stats?.verifiedPatches || 0} Patches
          </div>
          <div className="text-[11px] text-emerald-400/80 mt-1">Regression clean</div>
        </div>
      </div>

      {/* Two Column Layout: Scans & Findings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Scans */}
        <Card title="Execution History on this Repository" subtitle="Recent scans & test runs">
          <div className="space-y-3">
            {scans.map((scan) => (
              <div 
                key={scan.id}
                className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-white">{scan.id}</span>
                    <StatusBadge status={scan.status} />
                  </div>
                  <div className="text-[11px] font-mono text-slate-400 mt-1">
                    {scan.createdAt} • {scan.durationMs}ms duration
                  </div>
                </div>

                <Link to={`/scans/${scan.id}`}>
                  <Button variant="ghost" size="sm" className="text-xs font-mono">
                    Details <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </Card>

        {/* Active Findings */}
        <Card title="Repository Findings & Hypotheses" subtitle="Sandboxed vs theoretical bugs">
          <div className="space-y-3">
            {findings.map((f) => {
              const isConfirmed = f.status === 'CONFIRMED';
              return (
                <div 
                  key={f.id}
                  className={`p-3 rounded-lg bg-slate-950 flex items-center justify-between ${
                    isConfirmed 
                      ? 'border border-solid border-emerald-500/40' 
                      : 'border border-dashed border-indigo-400/40'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-white">{f.id}</span>
                      <SeverityBadge severity={f.severity} />
                      <StatusBadge status={f.status} isRuntimeEvidence={isConfirmed} />
                    </div>
                    <div className="text-xs text-slate-200 font-semibold truncate max-w-sm">
                      {f.title}
                    </div>
                    <div className="text-[11px] font-mono text-slate-400">
                      {f.file}:{f.lineStart}
                    </div>
                  </div>

                  <Link to={`/findings/${f.id}`}>
                    <Button variant="ghost" size="sm" className="text-xs font-mono">
                      Inspect <ArrowRight className="w-3 h-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}

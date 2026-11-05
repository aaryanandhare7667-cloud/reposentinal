import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FolderGit2, 
  GitBranch, 
  Clock, 
  ShieldCheck, 
  AlertTriangle, 
  Search, 
  Plus, 
  ArrowRight,
  ExternalLink,
  Code,
  Network
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { StatusBadge } from '../components/common/Badge';
import { getRepositories } from '../services/repositoryService';

export default function RepositoriesList() {
  const [repositories, setRepositories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function loadRepos() {
      setLoading(true);
      const data = await getRepositories();
      setRepositories(data);
      setLoading(false);
    }
    loadRepos();
  }, []);

  const filteredRepos = repositories.filter(repo => {
    const term = (searchTerm || '').toLowerCase();
    const rName = (repo.name || '').toLowerCase();
    const rPath = (repo.path || '').toLowerCase();
    const rUrl = (repo.url || '').toLowerCase();
    return rName.includes(term) || rPath.includes(term) || rUrl.includes(term);
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Intelligence', to: '/repositories' },
          { label: 'Repositories', to: '/repositories' }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <FolderGit2 className="w-6 h-6 text-indigo-400" />
            Target Repositories
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Monitored GitHub repositories and local codebases configured for autonomous sandbox verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/scans/new">
            <Button variant="primary" size="sm" className="flex items-center gap-1.5">
              <Plus className="w-4 h-4" />
              Scan Repository
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/40 border border-slate-800">
        <div className="relative w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text"
            placeholder="Search repositories by name or path..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <div className="text-xs font-mono text-slate-400">
          {filteredRepos.length} Repositories Registered
        </div>
      </div>

      {/* Repositories Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredRepos.map((repo) => {
          const hasConfirmed = repo.stats?.verifiedFindings > 0;
          return (
            <div 
              key={repo.id}
              className={`p-5 rounded-lg bg-slate-900/60 transition-all ${
                hasConfirmed 
                  ? 'border border-rose-500/30 hover:border-rose-500/50' 
                  : 'border border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <FolderGit2 className="w-5 h-5 text-indigo-400" />
                    <Link to={`/repositories/${repo.id}`} className="text-base font-bold text-white hover:text-indigo-400 font-mono transition-colors">
                      {repo.name}
                    </Link>
                  </div>
                  <div className="text-xs font-mono text-slate-500 flex items-center gap-1.5">
                    <GitBranch className="w-3.5 h-3.5 text-slate-400" />
                    <span>{repo.defaultBranch || 'main'}</span>
                    <span>•</span>
                    <span className="truncate max-w-xs">{repo.path}</span>
                  </div>
                </div>

                <StatusBadge 
                  status={repo.stats?.verifiedFindings > 0 ? 'VULNERABLE' : (repo.lastScanDate ? 'VERIFIED' : 'PENDING')} 
                />
              </div>

              {/* Status / Findings Metrics */}
              <div className="my-4 p-3 rounded bg-slate-950 border border-slate-800/80 grid grid-cols-3 gap-2 text-center text-xs font-mono">
                <div>
                  <div className="text-slate-500 text-[10px]">VERIFIED BUGS</div>
                  <div className={repo.stats?.verifiedFindings > 0 ? "text-rose-400 font-bold text-sm mt-0.5" : "text-emerald-400 font-semibold text-sm mt-0.5"}>
                    {repo.stats?.verifiedFindings !== undefined ? repo.stats.verifiedFindings : '0'}
                  </div>
                </div>
                <div>
                  <div className="text-slate-500 text-[10px]">AI HYPOTHESES</div>
                  <div className="text-indigo-300 font-semibold text-sm mt-0.5">
                    {repo.stats?.hypotheses !== undefined ? repo.stats.hypotheses : '0'}
                  </div>
                </div>
                <div>
                  <div className="text-slate-500 text-[10px]">VERIFIED PATCHES</div>
                  <div className="text-emerald-400 font-semibold text-sm mt-0.5">
                    {repo.stats?.verifiedPatches !== undefined ? repo.stats.verifiedPatches : '0'}
                  </div>
                </div>
              </div>

              {/* Security Scope Rule Notice */}
              <div className="text-[11px] font-mono text-slate-400 mb-4">
                {repo.stats?.verifiedFindings === 0 ? (
                  <span className="text-slate-400">Status: No findings in the scanned scope</span>
                ) : (
                  <span className="text-rose-400">Status: {repo.stats?.verifiedFindings} verified flaw(s) require remediation</span>
                )}
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-800/80">
                <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Last Scan: {repo.lastScanDate || 'Not Run'}
                </span>

                <div className="flex items-center gap-2">
                  <Link to={`/topology`}>
                    <Button variant="ghost" size="sm" className="text-xs p-1.5" title="View Topology">
                      <Network className="w-3.5 h-3.5" />
                    </Button>
                  </Link>
                  <Link to={`/repositories/${repo.id}`}>
                    <Button variant="secondary" size="sm" className="text-xs font-mono">
                      View Target <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

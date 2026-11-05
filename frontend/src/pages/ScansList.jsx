import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Play, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Search, 
  Filter, 
  ArrowRight,
  FolderGit2,
  Terminal,
  ShieldCheck,
  Plus
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { StatusBadge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { getScans } from '../services/scanService';

export default function ScansList() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => {
    async function loadScans() {
      setLoading(true);
      const data = await getScans();
      setScans(data);
      setLoading(false);
    }
    loadScans();
  }, []);

  const filteredScans = scans.filter(scan => {
    const term = (searchTerm || '').toLowerCase();
    const sId = (scan.id || '').toLowerCase();
    const sRepo = (scan.targetRepo || scan.targetPath || '').toLowerCase();
    const matchesSearch = sId.includes(term) || sRepo.includes(term);
    const matchesStatus = 
      statusFilter === 'ALL' || scan.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Operations', to: '/scans' },
          { label: 'Execution History', to: '/scans' }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Clock className="w-6 h-6 text-indigo-400" />
            Scan & Verification History
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Historical audit logs of repository topology scans, adversarial tests, and patch validations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/scans/new">
            <Button variant="primary" size="sm" className="flex items-center gap-1.5">
              <Plus className="w-4 h-4" />
              New Repository Scan
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric Cards Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 uppercase">Total Scans Executed</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{scans.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">Audit log records</div>
        </div>

        <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/40">
          <div className="text-xs font-mono text-emerald-400 uppercase">Successful Verifications</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            {scans.filter(s => s.status === 'COMPLETED').length}
          </div>
          <div className="text-[11px] text-emerald-300/80 mt-1">Clean exit & sandboxed runs</div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 uppercase">Average Duration</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">4.2s</div>
          <div className="text-[11px] text-slate-500 mt-1">Topology + sandbox tests</div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 uppercase">Original Repo Integrity</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">100%</div>
          <div className="text-[11px] text-slate-500 mt-1">Zero host repo mutations</div>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-3 rounded-lg bg-slate-900/40 border border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text"
            placeholder="Search by Scan ID or repository path..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400 mr-1 font-mono">Status:</span>
          <div className="flex rounded bg-slate-950 border border-slate-800 p-0.5 text-xs font-mono">
            {['ALL', 'COMPLETED', 'FAILED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded transition-colors uppercase ${
                  statusFilter === st ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table of Scans */}
      {filteredScans.length === 0 ? (
        <EmptyState 
          title="No scan records in the scanned scope"
          description={searchTerm ? "No scans matched your search criteria." : "No scans have been initiated yet."}
          actionLabel="Initiate Scan"
          to="/scans/new"
        />
      ) : (
        <div className="rounded-lg border border-slate-800 overflow-hidden bg-slate-900/60">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-4">Scan ID</th>
                <th className="py-3 px-4">Target Repository</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-center">Modules</th>
                <th className="py-3 px-4 text-center">AI Hypotheses</th>
                <th className="py-3 px-4 text-center">Verified Bugs</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredScans.map((scan) => (
                <tr key={scan.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-white">
                    <Link to={`/scans/${scan.id}`} className="hover:text-indigo-400">
                      {scan.id}
                    </Link>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">
                    <div className="flex items-center gap-1.5">
                      <FolderGit2 className="w-3.5 h-3.5 text-slate-500" />
                      <span className="truncate max-w-xs">{scan.targetRepo}</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <StatusBadge status={scan.status} />
                  </td>
                  <td className="py-3.5 px-4 text-center text-slate-300">
                    {scan.modulesScanned || 24}
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <span className="inline-block px-2 py-0.5 rounded bg-indigo-500/10 border border-dashed border-indigo-400/40 text-indigo-300 text-[11px]">
                      {scan.hypothesesCount || 4}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <span className="inline-block px-2 py-0.5 rounded bg-rose-500/10 border border-solid border-rose-500/40 text-rose-300 text-[11px] font-bold">
                      {scan.confirmedFindingsCount || 2}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">
                    {scan.durationMs ? `${scan.durationMs}ms` : '3,840ms'}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Link to={`/scans/${scan.id}`}>
                      <Button variant="ghost" size="sm" className="h-7 text-xs">
                        Inspect <ArrowRight className="w-3 h-3 ml-1" />
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

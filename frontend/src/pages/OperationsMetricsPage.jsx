import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  ShieldCheck, 
  CheckCircle2, 
  Clock, 
  Terminal, 
  Cpu, 
  Layers, 
  Filter, 
  Download,
  AlertTriangle
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export default function OperationsMetricsPage() {
  const [timeRange, setTimeRange] = useState('30d');

  const funnelStages = [
    { name: '1. AST Topology & Files Scanned', count: 184, percent: '100%', color: 'bg-indigo-500' },
    { name: '2. Bug Hypotheses Synthesized', count: 42, percent: '22.8%', color: 'bg-indigo-400' },
    { name: '3. Adversarial Tests Generated', count: 42, percent: '22.8%', color: 'bg-indigo-400' },
    { name: '4. Sandboxed Executions Run', count: 42, percent: '22.8%', color: 'bg-purple-500' },
    { name: '5. Empirically Confirmed Bugs', count: 18, percent: '9.8%', color: 'bg-rose-500' },
    { name: '6. Candidate Patches Synthesized', count: 18, percent: '9.8%', color: 'bg-amber-500' },
    { name: '7. Verified Patches (Passing Re-test & Regressions)', count: 16, percent: '8.7%', color: 'bg-emerald-500' }
  ];

  const categoryBreakdown = [
    { name: 'SQL Injection', verified: 7, candidate: 2, total: 9 },
    { name: 'Server-Side Request Forgery (SSRF)', verified: 4, candidate: 1, total: 5 },
    { name: 'Unchecked Null Return / Dereference', verified: 3, candidate: 1, total: 4 },
    { name: 'Insecure Deserialization', verified: 2, candidate: 0, total: 2 }
  ];

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Intelligence', to: '/findings' },
          { label: 'Security Operations Metrics', to: '/metrics' }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-indigo-400" />
            Security Operations & Benchmark Metrics
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Empirical runtime verification metrics, sandbox reproduction rates, and zero-hallucination indicators.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex rounded bg-slate-900 border border-slate-800 p-0.5 text-xs font-mono">
            {['24h', '7d', '30d', 'all'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 rounded transition-colors uppercase ${
                  timeRange === range ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Top 4 Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/40">
          <div className="text-xs font-mono text-emerald-400 uppercase">Empirical Verification Rate</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">42.8%</div>
          <div className="text-[11px] text-emerald-300/80 mt-1">
            18 confirmed bugs out of 42 AI hypotheses (57.2% hallucination filter rate)
          </div>
        </div>

        <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/40">
          <div className="text-xs font-mono text-emerald-400 uppercase">Patch Fix Pass Rate</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">88.9%</div>
          <div className="text-[11px] text-emerald-300/80 mt-1">
            16 / 18 candidate patches passed sandbox re-test & regression checks
          </div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 uppercase">Mean Time to Verification</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">3.4s</div>
          <div className="text-[11px] text-slate-500 mt-1">Average sandbox execution duration per adversarial test</div>
        </div>

        <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400 uppercase">Original Workspace Mutation</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">0 Bytes (0%)</div>
          <div className="text-[11px] text-slate-500 mt-1">100% isolated inside scratch execution jails</div>
        </div>
      </div>

      {/* Funnel Section */}
      <Card 
        title="RepoSentinel Autonomous Verification Pipeline Funnel" 
        subtitle="Step-by-step attrition from repository scan to verified patches"
      >
        <div className="space-y-3 pt-2">
          {funnelStages.map((stage, idx) => (
            <div key={stage.name} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-300">{stage.name}</span>
                <span className="text-slate-400">{stage.count} items ({stage.percent})</span>
              </div>
              <div className="h-3 w-full bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-800">
                <div 
                  className={`h-full rounded-full ${stage.color}`}
                  style={{ width: stage.percent }}
                />
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Category Breakdown & Invariants Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Vulnerability Category Verification Breakdown" subtitle="Confirmed vs candidate patches by CVE type">
          <div className="space-y-3">
            {categoryBreakdown.map((cat) => (
              <div key={cat.name} className="p-3 rounded bg-slate-950 border border-slate-800">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="font-semibold text-white">{cat.name}</span>
                  <span className="text-slate-400">{cat.total} total</span>
                </div>
                <div className="flex items-center gap-4 text-xs font-mono">
                  <span className="text-emerald-400">
                    ✓ {cat.verified} Verified Patches
                  </span>
                  <span>•</span>
                  <span className="text-indigo-400">
                    ⚬ {cat.candidate} Candidate / In Review
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Runtime Execution Security Invariants" subtitle="Hardware & kernel-enforced sandboxing stats">
          <div className="space-y-3 text-xs font-mono">
            <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-slate-400">NETWORK RESTRICTIONS</div>
                <div className="text-white font-semibold mt-0.5">Airgapped (No inbound or outbound sockets)</div>
              </div>
              <span className="px-2 py-1 rounded bg-emerald-500/20 text-emerald-400 text-[11px] font-bold">100% ENFORCED</span>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-slate-400">EXECUTION TIMEOUT BUDGET</div>
                <div className="text-white font-semibold mt-0.5">15.0 seconds maximum per test</div>
              </div>
              <span className="px-2 py-1 rounded bg-emerald-500/20 text-emerald-400 text-[11px] font-bold">0 OVERRUNS</span>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-slate-400">FILE SYSTEM ISOLATION</div>
                <div className="text-white font-semibold mt-0.5">Temporary scratch workspace with automated unlinking</div>
              </div>
              <span className="px-2 py-1 rounded bg-emerald-500/20 text-emerald-400 text-[11px] font-bold">100% CLEANED</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

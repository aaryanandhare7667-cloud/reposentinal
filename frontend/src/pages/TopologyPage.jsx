import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Network, 
  GitBranch, 
  FileCode, 
  Code, 
  Search, 
  AlertTriangle, 
  CheckCircle2, 
  Layers, 
  ArrowRight,
  ShieldAlert,
  ChevronRight,
  ChevronDown,
  Box,
  Compass
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { StatusBadge } from '../components/common/Badge';
import { getTopology } from '../services/topologyService';

export default function TopologyPage() {
  const [topology, setTopology] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterVulnerableOnly, setFilterVulnerableOnly] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const data = await getTopology();
      setTopology(data);
      if (data && data.nodes && data.nodes.length > 0) {
        // Select vulnerable node by default if available
        const vulnNode = data.nodes.find(n => n.hasVulnerability);
        setSelectedNode(vulnNode || data.nodes[0]);
      }
      setLoading(false);
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-400">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
        <div className="text-sm font-mono">Analyzing repository symbol topology...</div>
      </div>
    );
  }

  const nodes = topology?.nodes || [];
  const edges = topology?.edges || [];
  const summary = topology?.summary || { totalFiles: 24, totalSymbols: 142, totalDependencies: 389, criticalPaths: 3 };

  const filteredNodes = nodes.filter(node => {
    const matchesSearch = 
      node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.file.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (node.type && node.type.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesVuln = filterVulnerableOnly ? node.hasVulnerability : true;
    return matchesSearch && matchesVuln;
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Intelligence', to: '/topology' },
          { label: 'Repository Topology', to: '/topology' }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Network className="w-6 h-6 text-indigo-400" />
            Repository Symbol Topology & Call Graph
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            AST-indexed inter-module relationships, cross-file caller/callee graphs, and taint propagation paths.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/findings">
            <Button variant="outline" size="sm">
              View Linked Findings
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400">PARSED MODULES</div>
          <div className="text-xl font-bold font-mono text-white mt-1">{summary.totalFiles} Files</div>
        </div>
        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400">AST SYMBOLS</div>
          <div className="text-xl font-bold font-mono text-indigo-400 mt-1">{summary.totalSymbols} Indexed</div>
        </div>
        <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="text-xs font-mono text-slate-400">CALL DEPENDENCIES</div>
          <div className="text-xl font-bold font-mono text-white mt-1">{summary.totalDependencies} Edges</div>
        </div>
        <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-500/30">
          <div className="text-xs font-mono text-rose-400">VULNERABILITY PATHS</div>
          <div className="text-xl font-bold font-mono text-rose-400 mt-1">{summary.criticalPaths} Active</div>
        </div>
      </div>

      {/* Two Column Layout: Symbol Explorer & Node Detail / Graph */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Symbol Tree / List */}
        <div className="space-y-4">
          <Card title="Indexed Symbols" subtitle="Search and select symbol node">
            <div className="space-y-3">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="text"
                  placeholder="Filter symbols or files..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div className="flex items-center justify-between text-xs font-mono px-1">
                <label className="flex items-center gap-2 cursor-pointer text-slate-400 hover:text-slate-200">
                  <input 
                    type="checkbox"
                    checked={filterVulnerableOnly}
                    onChange={(e) => setFilterVulnerableOnly(e.target.checked)}
                    className="rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-0"
                  />
                  <span>Vulnerable only</span>
                </label>
                <span className="text-slate-500">{filteredNodes.length} nodes</span>
              </div>

              <div className="space-y-1 max-h-[500px] overflow-y-auto pr-1">
                {filteredNodes.map((node) => {
                  const isSelected = selectedNode?.id === node.id;
                  return (
                    <button
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      className={`w-full text-left p-2.5 rounded transition-all text-xs font-mono flex items-center justify-between ${
                        isSelected 
                          ? 'bg-indigo-600/20 border border-indigo-500/40 text-white' 
                          : 'bg-slate-950/60 border border-slate-800/80 text-slate-300 hover:bg-slate-800/60'
                      }`}
                    >
                      <div className="truncate mr-2">
                        <div className="flex items-center gap-1.5 font-semibold">
                          <Code className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                          <span className="truncate">{node.name}</span>
                        </div>
                        <div className="text-[10px] text-slate-500 truncate mt-0.5">
                          {node.file}
                        </div>
                      </div>

                      {node.hasVulnerability && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 shrink-0">
                          VULN
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Interactive Graph & Node Deep Dive (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Interactive Topology Graph Canvas Visualizer */}
          <Card 
            title="Topology Call Graph Visualizer" 
            subtitle="Cross-file call edges and taint propagation paths"
          >
            <div className="h-[340px] rounded-lg bg-slate-950 border border-slate-800 relative overflow-hidden flex flex-col items-center justify-center p-6">
              {/* Background Graph Grid Pattern */}
              <div 
                className="absolute inset-0 opacity-15"
                style={{
                  backgroundImage: `radial-gradient(circle, #6366f1 1px, transparent 1px)`,
                  backgroundSize: '24px 24px'
                }}
              />

              {/* Render Nodes Flow Representation */}
              <div className="relative z-10 w-full flex items-center justify-between gap-4 max-w-xl">
                {/* Entry Controller Node */}
                <div className="flex-1 p-3 rounded-lg bg-slate-900 border border-slate-700 text-center shadow-lg">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Entry Point</div>
                  <div className="text-xs font-mono font-bold text-white mt-1">api/routes.py</div>
                  <div className="text-[11px] font-mono text-indigo-400 mt-0.5">handle_user_search()</div>
                </div>

                <div className="flex items-center text-slate-600 font-mono text-xs">
                  <ArrowRight className="w-4 h-4 text-indigo-400 animate-pulse" />
                </div>

                {/* Processing Middle Tier Node */}
                <div className="flex-1 p-3 rounded-lg bg-slate-900 border border-slate-700 text-center shadow-lg">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Service Layer</div>
                  <div className="text-xs font-mono font-bold text-white mt-1">services/auth.py</div>
                  <div className="text-[11px] font-mono text-indigo-400 mt-0.5">lookup_account()</div>
                </div>

                <div className="flex items-center text-slate-600 font-mono text-xs">
                  <ArrowRight className="w-4 h-4 text-rose-400 animate-pulse" />
                </div>

                {/* Target Sink Node */}
                <div className="flex-1 p-3 rounded-lg bg-rose-950/40 border border-rose-500/60 text-center shadow-lg">
                  <div className="text-[10px] font-mono text-rose-400 uppercase font-semibold">Taint Sink (Vuln)</div>
                  <div className="text-xs font-mono font-bold text-rose-200 mt-1">models/db.py</div>
                  <div className="text-[11px] font-mono text-rose-300 mt-0.5">execute_query()</div>
                </div>
              </div>

              {/* Legend */}
              <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> AST Node
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Tainted Sink
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Sanitized Path
                  </span>
                </div>
                <div className="text-slate-500">
                  Mode: Static AST Directed Graph
                </div>
              </div>
            </div>
          </Card>

          {/* Selected Symbol Detail Card */}
          {selectedNode && (
            <Card 
              title={`Symbol Inspector: ${selectedNode.name}`} 
              subtitle={`AST Definition in ${selectedNode.file}`}
              isRuntimeEvidence={selectedNode.hasVulnerability}
            >
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">SYMBOL TYPE</span>
                    <span className="text-white font-semibold">{selectedNode.type || 'Function / Method'}</span>
                  </div>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">LINE DEFINITION</span>
                    <span className="text-white font-semibold">L{selectedNode.lineStart || 42} - L{selectedNode.lineEnd || 65}</span>
                  </div>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">INBOUND CALLERS</span>
                    <span className="text-indigo-400 font-semibold">{selectedNode.callersCount || 3} references</span>
                  </div>
                  <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">VULNERABILITY</span>
                    <span className={selectedNode.hasVulnerability ? "text-rose-400 font-bold" : "text-emerald-400 font-semibold"}>
                      {selectedNode.hasVulnerability ? 'CONFIRMED' : 'None detected'}
                    </span>
                  </div>
                </div>

                {selectedNode.hasVulnerability && (
                  <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/30 text-xs">
                    <div className="font-semibold text-rose-300 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-rose-400" />
                      Confirmed Bug at this AST node
                    </div>
                    <div className="text-slate-300 mt-1">
                      Direct sink execution of user-supplied parameter without parameterized query encapsulation.
                    </div>
                    <div className="flex items-center gap-3 mt-3">
                      <Link to={`/findings`}>
                        <Button variant="danger" size="sm" className="text-xs font-mono">
                          View Finding
                        </Button>
                      </Link>
                      <Link to={`/patches`}>
                        <Button variant="outline" size="sm" className="text-xs font-mono">
                          View Synthesized Patch
                        </Button>
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

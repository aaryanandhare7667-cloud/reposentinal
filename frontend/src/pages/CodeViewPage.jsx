import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  FileCode, 
  Folder, 
  ChevronRight, 
  ChevronDown, 
  AlertTriangle, 
  ShieldAlert, 
  GitPullRequest, 
  ExternalLink,
  Search,
  Copy,
  Check,
  Code
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { CodeViewer } from '../components/code/CodeViewer';
import { getFileContent, getRepositories } from '../services/repositoryService';
import { getFindings } from '../services/findingsService';

export default function CodeViewPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedFile = searchParams.get('file') || 'backend/models/database.py';

  const [currentFile, setCurrentFile] = useState(requestedFile);
  const [fileContent, setFileContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [findings, setFindings] = useState([]);
  const [copied, setCopied] = useState(false);

  // File tree structure
  const fileTree = [
    {
      name: 'backend',
      type: 'dir',
      children: [
        {
          name: 'models',
          type: 'dir',
          children: [
            { name: 'database.py', path: 'backend/models/database.py', hasFinding: true },
            { name: 'schema.py', path: 'backend/models/schema.py', hasFinding: false }
          ]
        },
        {
          name: 'analysis',
          type: 'dir',
          children: [
            { name: 'topology.py', path: 'backend/analysis/topology.py', hasFinding: false },
            { name: 'ast_indexer.py', path: 'backend/analysis/ast_indexer.py', hasFinding: false }
          ]
        },
        {
          name: 'verification',
          type: 'dir',
          children: [
            { name: 'sandbox.py', path: 'backend/verification/sandbox.py', hasFinding: false },
            { name: 'verifier.py', path: 'backend/verification/verifier.py', hasFinding: false }
          ]
        },
        {
          name: 'patching',
          type: 'dir',
          children: [
            { name: 'generator.py', path: 'backend/patching/generator.py', hasFinding: false },
            { name: 'safety.py', path: 'backend/patching/safety.py', hasFinding: false },
            { name: 'workspace.py', path: 'backend/patching/workspace.py', hasFinding: false }
          ]
        }
      ]
    },
    {
      name: 'tests',
      type: 'dir',
      children: [
        {
          name: 'fixtures',
          type: 'dir',
          children: [
            { name: 'cross_file_repo/app.py', path: 'tests/fixtures/cross_file_repo/app.py', hasFinding: false }
          ]
        }
      ]
    }
  ];

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const content = await getFileContent(currentFile);
      setFileContent(content || `# File: ${currentFile}\n# Loading content...`);
      const allFindings = await getFindings();
      setFindings(allFindings);
      setLoading(false);
    }
    loadData();
  }, [currentFile]);

  const activeFinding = findings.find(f => f.file === currentFile);

  const handleSelectFile = (path) => {
    setCurrentFile(path);
    setSearchParams({ file: path });
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(fileContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Intelligence', to: '/findings' },
          { label: 'Code View', to: '/code' },
          { label: currentFile }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Code className="w-6 h-6 text-indigo-400" />
            Repository Source Code & AST Annotations
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Target: <span className="text-slate-200">reposentinal @ main</span> — Scanned revision
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={handleCopyCode}>
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400 mr-1.5" /> : <Copy className="w-3.5 h-3.5 mr-1.5" />}
            {copied ? 'Copied' : 'Copy File'}
          </Button>
          <Link to="/topology">
            <Button variant="outline" size="sm">
              View in Topology
            </Button>
          </Link>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: File Tree (1 col) */}
        <div className="space-y-4">
          <Card title="Repository Tree" subtitle="Monitored repository files">
            <div className="space-y-1 font-mono text-xs">
              {fileTree.map((dir) => (
                <div key={dir.name} className="space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-400 font-semibold py-1">
                    <Folder className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{dir.name}/</span>
                  </div>
                  <div className="pl-4 space-y-1 border-l border-slate-800 ml-1.5">
                    {dir.children.map((sub) => {
                      if (sub.type === 'dir') {
                        return (
                          <div key={sub.name} className="space-y-1">
                            <div className="flex items-center gap-1.5 text-slate-400 py-0.5">
                              <Folder className="w-3 h-3 text-slate-500" />
                              <span>{sub.name}/</span>
                            </div>
                            <div className="pl-4 space-y-1 border-l border-slate-800 ml-1">
                              {sub.children.map((f) => (
                                <button
                                  key={f.path}
                                  onClick={() => handleSelectFile(f.path)}
                                  className={`w-full text-left py-1 px-1.5 rounded flex items-center justify-between text-xs transition-colors ${
                                    currentFile === f.path 
                                      ? 'bg-indigo-600/20 text-white font-semibold' 
                                      : 'text-slate-400 hover:text-slate-200'
                                  }`}
                                >
                                  <span className="truncate">{f.name}</span>
                                  {f.hasFinding && (
                                    <span className="w-2 h-2 rounded-full bg-rose-500 shrink-0" title="Active finding" />
                                  )}
                                </button>
                              ))}
                            </div>
                          </div>
                        );
                      }
                      return null;
                    })}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Code Viewer (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Active Finding Banner if applicable */}
          {activeFinding && (
            <Card 
              isRuntimeEvidence={activeFinding.status === 'CONFIRMED'}
              className="bg-rose-950/20 border-rose-500/40 p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 shrink-0">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-rose-200 flex items-center gap-2">
                      <span>Vulnerability Confirmed at Lines {activeFinding.lineStart}–{activeFinding.lineEnd}</span>
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300">
                        {activeFinding.id}
                      </span>
                    </div>
                    <div className="text-xs text-slate-300 mt-1">
                      {activeFinding.title} — {activeFinding.description}
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs font-mono text-slate-400">
                      <span>Affected Symbol: <code className="text-indigo-400">{activeFinding.symbol}</code></span>
                      <span>•</span>
                      <span>Verification: <strong className="text-emerald-400">SANDBOX VERIFIED</strong></span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Link to={`/findings/${activeFinding.id}`}>
                    <Button variant="danger" size="sm" className="text-xs">
                      Finding Details
                    </Button>
                  </Link>
                  <Link to={`/patches?hypothesisId=${activeFinding.id}`}>
                    <Button variant="primary" size="sm" className="text-xs">
                      View Patch
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>
          )}

          {/* Code Viewer Panel */}
          <Card title={currentFile} subtitle="Syntax highlighting & line annotations">
            <CodeViewer 
              code={fileContent}
              fileName={currentFile}
              highlightStart={activeFinding ? activeFinding.lineStart : null}
              highlightEnd={activeFinding ? activeFinding.lineEnd : null}
            />
          </Card>
        </div>
      </div>
    </div>
  );
}

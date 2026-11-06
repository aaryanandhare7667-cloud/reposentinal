import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bug, Terminal, Wrench, Network, BookOpen, Settings, ArrowRight } from 'lucide-react';
import { mockFindings, mockPatches, mockScans } from '../../data/mockData';

export function CommandPalette({ isOpen, onClose }) {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (!isOpen) setQuery('');
  }, [isOpen]);

  if (!isOpen) return null;

  const quickPages = [
    { label: 'Security Overview', to: '/', icon: Terminal },
    { label: 'New Scan', to: '/scans/new', icon: Terminal },
    { label: 'All Findings', to: '/findings', icon: Bug },
    { label: 'Verified Patches', to: '/patches', icon: Wrench },
    { label: 'Topology Graph', to: '/topology', icon: Network },
    { label: 'Method & Pipeline', to: '/method', icon: BookOpen },
    { label: 'Settings', to: '/settings', icon: Settings },
  ];

  const filteredFindings = mockFindings.filter(
    (f) =>
      f.title.toLowerCase().includes(query.toLowerCase()) ||
      f.id.toLowerCase().includes(query.toLowerCase()) ||
      f.affectedFile.toLowerCase().includes(query.toLowerCase())
  );

  const filteredPatches = mockPatches.filter(
    (p) =>
      p.targetFile.toLowerCase().includes(query.toLowerCase()) ||
      p.id.toLowerCase().includes(query.toLowerCase()) ||
      p.patchObjective.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (to) => {
    navigate(to);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-100">
      <div
        className="bg-bg-card border border-border rounded-lg shadow-2xl w-full max-w-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center px-4 border-b border-border bg-bg-surface/60">
          <Search className="w-4 h-4 text-text-muted shrink-0 mr-2.5" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, hypothesis ID, or file..."
            className="w-full py-3.5 bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none font-mono"
          />
          <kbd
            onClick={onClose}
            className="text-[10px] font-mono px-1.5 py-0.5 bg-bg-surface border border-border rounded text-text-muted cursor-pointer hover:text-text-primary"
          >
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-3">
          {/* Findings */}
          {filteredFindings.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[10px] font-mono uppercase text-text-muted">
                Findings ({filteredFindings.length})
              </div>
              <div className="space-y-0.5">
                {filteredFindings.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => handleSelect(`/findings/${f.id}`)}
                    className="w-full flex items-center justify-between p-2 rounded text-left hover:bg-bg-hover transition-colors group"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Bug className="w-3.5 h-3.5 text-red-400 shrink-0" />
                      <div className="truncate">
                        <div className="text-xs font-medium text-text-primary group-hover:text-white truncate">
                          {f.title}
                        </div>
                        <div className="text-[10px] font-mono text-text-muted truncate">
                          {f.id} • {f.affectedFile}:{f.lineStart}
                        </div>
                      </div>
                    </div>
                    <ArrowRight className="w-3 h-3 text-text-muted group-hover:text-text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Patches */}
          {filteredPatches.length > 0 && (
            <div>
              <div className="px-2 py-1 text-[10px] font-mono uppercase text-text-muted">
                Patches ({filteredPatches.length})
              </div>
              <div className="space-y-0.5">
                {filteredPatches.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => handleSelect(`/patches/${p.id}`)}
                    className="w-full flex items-center justify-between p-2 rounded text-left hover:bg-bg-hover transition-colors group"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Wrench className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <div className="truncate">
                        <div className="text-xs font-medium text-text-primary group-hover:text-white truncate">
                          {p.targetFile} - {p.patchObjective}
                        </div>
                        <div className="text-[10px] font-mono text-text-muted truncate">
                          {p.id} • {p.verificationStatus}
                        </div>
                      </div>
                    </div>
                    <ArrowRight className="w-3 h-3 text-text-muted group-hover:text-text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Navigation Shortcuts */}
          <div>
            <div className="px-2 py-1 text-[10px] font-mono uppercase text-text-muted">Navigation</div>
            <div className="space-y-0.5">
              {quickPages
                .filter((p) => p.label.toLowerCase().includes(query.toLowerCase()))
                .map((page) => {
                  const Icon = page.icon;
                  return (
                    <button
                      key={page.to}
                      onClick={() => handleSelect(page.to)}
                      className="w-full flex items-center justify-between p-2 rounded text-left hover:bg-bg-hover transition-colors group"
                    >
                      <div className="flex items-center gap-2">
                        <Icon className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                        <span className="text-xs font-medium text-text-primary group-hover:text-white">
                          {page.label}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-text-muted">{page.to}</span>
                    </button>
                  );
                })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

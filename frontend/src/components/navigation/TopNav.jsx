import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Play, GitBranch, Shield, Command } from 'lucide-react';
import { Button } from '../common/Button';
import { checkBackendHealth, subscribeBackendStatus } from '../../services/api';

export function TopNav({ onOpenCommandPalette, selectedRepo = 'cross_file_repo' }) {
  const navigate = useNavigate();
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    checkBackendHealth().then(setIsOnline);
    const unsubscribe = subscribeBackendStatus(setIsOnline);
    const interval = setInterval(checkBackendHealth, 4000);
    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="h-14 bg-bg-surface/80 backdrop-blur-sm border-b border-border px-4 flex items-center justify-between shrink-0 z-20">
      {/* Left: Active Target Context & Backend Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-bg-card border border-border text-xs font-mono">
          <GitBranch className="w-3.5 h-3.5 text-brand-400" />
          <span className="text-text-secondary font-medium">target:</span>
          <span className="text-text-primary font-semibold">{selectedRepo}</span>
          <span className="text-text-muted">@main</span>
        </div>

        {/* Live Backend Connection Indicator */}
        <div
          className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono border ${
            isOnline
              ? 'border-emerald-500/40 bg-emerald-950/20 text-emerald-400'
              : 'border-red-500/40 bg-red-950/20 text-red-400'
          }`}
          title={isOnline ? 'Backend API connected on http://localhost:8000' : 'Backend API offline'}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isOnline ? 'bg-emerald-500' : 'bg-red-500 animate-pulse'
            }`}
          />
          <span>{isOnline ? 'API :8000 Online' : 'API Offline'}</span>
        </div>

        <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono border border-emerald-500/40 bg-emerald-950/20 text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span>Sandbox Active</span>
        </div>
      </div>

      {/* Right: Search / Command Palette & New Scan */}
      <div className="flex items-center gap-2.5">
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-2 px-3 py-1.5 rounded bg-bg-card border border-border text-xs text-text-muted hover:text-text-primary hover:border-border-highlight transition-colors"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Search symbols, hypotheses, diffs...</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 text-[10px] font-mono px-1.5 py-0.5 bg-bg-surface border border-border rounded text-text-muted">
            <Command className="w-2.5 h-2.5" />K
          </kbd>
        </button>

        <Button
          variant="primary"
          size="sm"
          icon={Play}
          onClick={() => navigate('/scans/new')}
        >
          New Scan
        </Button>
      </div>
    </header>
  );
}

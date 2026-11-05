import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { Sidebar } from '../components/navigation/Sidebar';
import { TopNav } from '../components/navigation/TopNav';
import { CommandPalette } from '../components/navigation/CommandPalette';
import { checkBackendHealth, subscribeBackendStatus } from '../services/api';

export function AppLayout({ children }) {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    checkBackendHealth().then(setIsOnline);
    const unsubscribe = subscribeBackendStatus(setIsOnline);

    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      unsubscribe();
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B0F17] text-slate-100">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Top Header */}
        <TopNav onOpenCommandPalette={() => setIsCommandPaletteOpen(true)} />

        {/* Offline Alert Banner */}
        {!isOnline && (
          <div className="bg-red-950/40 border-b border-red-500/40 px-6 py-2.5 flex items-center justify-between text-xs font-mono text-red-300 shrink-0">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <span>
                <strong>Backend Unavailable:</strong> RepoSentinel API server on{' '}
                <code className="bg-red-900/40 px-1 py-0.5 rounded text-white">http://localhost:8000</code> is offline. Run{' '}
                <code className="bg-red-900/40 px-1 py-0.5 rounded text-white">python3 -m backend.api.server --port 8000</code> to connect.
              </span>
            </div>
            <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-red-900/50 text-[10px] text-red-300 uppercase tracking-wider font-semibold border border-red-500/30">
              Offline Mode • No Invented Verdicts
            </span>
          </div>
        )}

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto px-6 py-5">
          <div className="max-w-7xl mx-auto space-y-6">
            {children || <Outlet />}
          </div>
        </main>
      </div>

      {/* Global Command Palette */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />
    </div>
  );
}

export default AppLayout;

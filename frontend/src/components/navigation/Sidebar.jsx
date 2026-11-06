import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Shield,
  Activity,
  Bug,
  FlaskConical,
  Wrench,
  GitFork,
  Network,
  BarChart3,
  BookOpen,
  Settings,
  FolderGit2,
  Terminal,
} from 'lucide-react';

export function Sidebar() {
  const mainNav = [
    { to: '/', label: 'Security Overview', icon: Activity },
    { to: '/scans', label: 'Scans & History', icon: Terminal },
    { to: '/findings', label: 'Findings', icon: Bug },
    { to: '/patches', label: 'Patches', icon: Wrench },
    { to: '/repositories', label: 'Repositories', icon: FolderGit2 },
  ];

  const analysisNav = [
    { to: '/topology', label: 'Topology Graph', icon: Network },
    { to: '/metrics', label: 'SecOps Metrics', icon: BarChart3 },
    { to: '/method', label: 'Method & Pipeline', icon: BookOpen },
  ];

  return (
    <aside className="w-56 bg-bg-surface border-r border-border flex flex-col shrink-0 select-none">
      {/* Brand Header */}
      <div className="h-14 px-4 flex items-center gap-2.5 border-b border-border">
        <div className="w-7 h-7 rounded bg-brand-600/20 border border-brand-500/40 flex items-center justify-center text-brand-500 shadow-sm">
          <Shield className="w-4 h-4" />
        </div>
        <div>
          <span className="text-xs font-bold tracking-wider text-text-primary uppercase flex items-center gap-1.5">
            RepoSentinel
          </span>
          <span className="text-[10px] font-mono text-brand-400 font-medium">v0.5.0 • Autonomous</span>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 py-3 px-2 space-y-4 overflow-y-auto">
        {/* Core Security Ops */}
        <div>
          <div className="px-2.5 mb-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-text-muted">
            Operations
          </div>
          <nav className="space-y-0.5">
            {mainNav.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-brand-600/20 text-white border border-brand-500/30'
                        : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                    }`
                  }
                >
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Repository Analysis & Architecture */}
        <div>
          <div className="px-2.5 mb-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-text-muted">
            Intelligence
          </div>
          <nav className="space-y-0.5">
            {analysisNav.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-brand-600/20 text-white border border-brand-500/30'
                        : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                    }`
                  }
                >
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer / Settings */}
      <div className="p-2 border-t border-border space-y-1">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-2.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
              isActive
                ? 'bg-brand-600/20 text-white border border-brand-500/30'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
            }`
          }
        >
          <Settings className="w-3.5 h-3.5 shrink-0" />
          <span>Settings</span>
        </NavLink>

        <div className="px-2.5 py-2 mt-1 rounded bg-bg-card border border-border/60 text-[10px] font-mono text-text-muted">
          <div className="flex items-center justify-between text-emerald-400 font-medium mb-0.5">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Engine Online
            </span>
            <span>46/46 OK</span>
          </div>
          <div className="text-text-muted truncate">Sandbox: safe_subprocess</div>
        </div>
      </div>
    </aside>
  );
}

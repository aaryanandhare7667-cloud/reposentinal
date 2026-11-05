import React from 'react';
import { Terminal, Shield, Check, AlertOctagon, Clock } from 'lucide-react';

export function VerificationTimeline({ evidence }) {
  if (!evidence) {
    return (
      <div className="p-4 rounded border border-border bg-bg-surface text-center text-xs text-text-muted">
        No sandboxed verification evidence collected for this item.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Execution Status Bar */}
      <div className="p-3 rounded border border-solid border-emerald-500/50 bg-emerald-950/20 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold">
          <Shield className="w-4 h-4 text-emerald-400" />
          <span>Deterministic Reproduction Confirmed</span>
        </div>
        <div className="flex items-center gap-4 text-text-muted text-[11px]">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {evidence.durationSeconds}s
          </span>
          <span>Backend: {evidence.sandboxBackend}</span>
          <span>Exit Code: {evidence.exitCode}</span>
        </div>
      </div>

      {/* Reproduction Stdout / Trace */}
      <div className="rounded border border-border bg-bg-base overflow-hidden">
        <div className="px-3 py-1.5 bg-bg-surface/80 border-b border-border flex items-center justify-between text-[11px] font-mono text-text-muted">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-brand-400" />
            <span>Sandbox Execution Log (Isolated Trace)</span>
          </div>
          <span className="text-emerald-400">Exit Code: {evidence.exitCode}</span>
        </div>
        <pre className="p-3 text-xs font-mono text-text-primary whitespace-pre-wrap leading-relaxed overflow-x-auto selection:bg-brand-500/30">
          {evidence.stdout || evidence.notes}
        </pre>
      </div>

      {/* Reproduction Test Script Code */}
      {evidence.reproductionCode && (
        <div className="rounded border border-border bg-bg-base overflow-hidden">
          <div className="px-3 py-1.5 bg-bg-surface/80 border-b border-border text-[11px] font-mono text-text-muted">
            <span>Reproduction Test Script ({evidence.testId})</span>
          </div>
          <pre className="p-3 text-xs font-mono text-text-secondary whitespace-pre-wrap leading-relaxed overflow-x-auto">
            {evidence.reproductionCode}
          </pre>
        </div>
      )}
    </div>
  );
}

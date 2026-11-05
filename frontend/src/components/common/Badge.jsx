import React from 'react';
import { ShieldAlert, AlertTriangle, Info, CheckCircle2, FlaskConical, Bot, Cpu } from 'lucide-react';

export function SeverityBadge({ severity, className = '' }) {
  const sev = (severity || 'INFO').toUpperCase();

  const configs = {
    CRITICAL: {
      bg: 'bg-red-950/40',
      border: 'border-red-500/60',
      text: 'text-red-400',
      dot: 'bg-red-500',
      icon: ShieldAlert,
    },
    HIGH: {
      bg: 'bg-orange-950/40',
      border: 'border-orange-500/60',
      text: 'text-orange-400',
      dot: 'bg-orange-500',
      icon: AlertTriangle,
    },
    MEDIUM: {
      bg: 'bg-amber-950/30',
      border: 'border-amber-500/50',
      text: 'text-amber-400',
      dot: 'bg-amber-400',
      icon: AlertTriangle,
    },
    LOW: {
      bg: 'bg-blue-950/30',
      border: 'border-blue-500/50',
      text: 'text-blue-400',
      dot: 'bg-blue-400',
      icon: Info,
    },
    INFO: {
      bg: 'bg-slate-900/40',
      border: 'border-slate-700',
      text: 'text-slate-400',
      dot: 'bg-slate-400',
      icon: Info,
    },
  };

  const config = configs[sev] || configs.INFO;
  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border ${config.bg} ${config.border} ${config.text} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      <Icon className="w-3 h-3" />
      <span>{sev}</span>
    </span>
  );
}

/**
 * StatusBadge enforces critical security UX rules:
 * - Dashed borders represent AI-generated claims/artifacts
 * - Solid borders represent executed/observed runtime evidence
 * - Never calls an unverified patch a "fix" (uses "Candidate Patch")
 * - Distinguishes 0, Not Run, and Unavailable
 */
export function StatusBadge({ status, isAiGenerated = false, isRuntimeEvidence = false, className = '' }) {
  const norm = (status || '').toLowerCase();

  // 1. Confirmed Bug / Verified Patch -> Solid runtime evidence
  if (norm.includes('confirmed') || norm.includes('verified') || isRuntimeEvidence) {
    return (
      <span
        title="Empirically verified by isolated sandboxed execution"
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border border-solid border-emerald-500/60 bg-emerald-950/30 text-emerald-400 ${className}`}
      >
        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
        <span>{status || 'VERIFIED'}</span>
      </span>
    );
  }

  // 2. Reproduced -> Sandbox evidence
  if (norm.includes('reproduced')) {
    return (
      <span
        title="Vulnerability triggered in isolated sandbox"
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border border-solid border-cyan-500/60 bg-cyan-950/30 text-cyan-400 ${className}`}
      >
        <FlaskConical className="w-3 h-3 text-cyan-400" />
        <span>REPRODUCED</span>
      </span>
    );
  }

  // 3. Regression Detected -> Solid alert
  if (norm.includes('regression')) {
    return (
      <span
        title="Candidate patch broke functional regression tests"
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border border-solid border-red-500 bg-red-950/40 text-red-400 ${className}`}
      >
        <AlertTriangle className="w-3 h-3" />
        <span>REGRESSION DETECTED</span>
      </span>
    );
  }

  // 4. Candidate / Proposed Patch (Never call unverified a "fix")
  if (norm.includes('candidate') || norm.includes('generated') || norm.includes('applied')) {
    return (
      <span
        title="Candidate Patch: Unverified by sandbox"
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border border-dashed border-indigo-400/60 bg-indigo-950/20 text-indigo-300 ${className}`}
      >
        <Bot className="w-3 h-3 text-indigo-400" />
        <span>Candidate Patch</span>
      </span>
    );
  }

  // 5. Likely Bug or Potential Bug -> AI Generated Claim (Dashed border)
  if (norm.includes('likely') || norm.includes('potential') || isAiGenerated) {
    return (
      <span
        title="AI-generated hypothesis: Awaiting sandboxed verification"
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border border-dashed border-indigo-400/60 bg-indigo-950/20 text-indigo-300 ${className}`}
      >
        <Bot className="w-3 h-3 text-indigo-400" />
        <span>{status}</span>
      </span>
    );
  }

  // 6. False Positive / Inconclusive
  if (norm.includes('false') || norm.includes('inconclusive')) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border border-border-subtle bg-bg-surface text-text-muted ${className}`}
      >
        <span>{status}</span>
      </span>
    );
  }

  // Fallback neutral
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border border-border bg-bg-surface text-text-secondary ${className}`}
    >
      <span>{status || 'Not Run'}</span>
    </span>
  );
}

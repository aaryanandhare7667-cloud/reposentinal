import React from 'react';
import { ShieldCheck, HelpCircle, AlertCircle, Ban } from 'lucide-react';

export function EmptyState({
  title = "No findings in the scanned scope",
  description = "No vulnerabilities or bug hypotheses were identified within the scanned files and symbols.",
  type = "clean", // "clean", "not_run", "unavailable", "empty"
  action = null,
}) {
  const configs = {
    clean: {
      icon: ShieldCheck,
      iconColor: 'text-emerald-400',
      bg: 'bg-emerald-950/20 border-emerald-500/20',
    },
    not_run: {
      icon: HelpCircle,
      iconColor: 'text-text-muted',
      bg: 'bg-bg-surface border-border',
    },
    unavailable: {
      icon: Ban,
      iconColor: 'text-amber-400',
      bg: 'bg-amber-950/20 border-amber-500/20',
    },
    empty: {
      icon: AlertCircle,
      iconColor: 'text-text-muted',
      bg: 'bg-bg-surface border-border',
    },
  };

  const config = configs[type] || configs.clean;
  const Icon = config.icon;

  return (
    <div className={`p-8 rounded border text-center ${config.bg}`}>
      <div className="inline-flex p-3 rounded-full bg-bg-card border border-border mb-3">
        <Icon className={`w-6 h-6 ${config.iconColor}`} />
      </div>
      <h3 className="text-sm font-medium text-text-primary mb-1">{title}</h3>
      <p className="text-xs text-text-secondary max-w-md mx-auto mb-4">{description}</p>
      {action && <div className="flex justify-center">{action}</div>}
    </div>
  );
}

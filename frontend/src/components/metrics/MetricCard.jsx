import React from 'react';

export function MetricCard({
  title,
  value,
  subvalue,
  icon: Icon,
  variant = 'default', // 'default', 'critical', 'high', 'success', 'cyan', 'dashed'
  className = '',
}) {
  const variants = {
    default: {
      border: 'border-border',
      text: 'text-text-primary',
      iconBg: 'bg-bg-elevated text-text-muted',
    },
    critical: {
      border: 'border-red-500/40',
      text: 'text-red-400',
      iconBg: 'bg-red-950/40 text-red-400',
    },
    high: {
      border: 'border-orange-500/40',
      text: 'text-orange-400',
      iconBg: 'bg-orange-950/40 text-orange-400',
    },
    success: {
      border: 'border-emerald-500/50',
      text: 'text-emerald-400',
      iconBg: 'bg-emerald-950/40 text-emerald-400',
    },
    cyan: {
      border: 'border-cyan-500/40',
      text: 'text-cyan-400',
      iconBg: 'bg-cyan-950/40 text-cyan-400',
    },
    dashed: {
      border: 'border-dashed border-indigo-500/50',
      text: 'text-indigo-300',
      iconBg: 'bg-indigo-950/40 text-indigo-400',
    },
  };

  const style = variants[variant] || variants.default;

  return (
    <div className={`p-4 rounded bg-bg-card border ${style.border} ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-mono uppercase tracking-wider text-text-muted">{title}</span>
        {Icon && (
          <div className={`p-1.5 rounded ${style.iconBg}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`text-2xl font-bold font-mono tracking-tight ${style.text}`}>
          {value !== undefined && value !== null ? value : 'Not Run'}
        </span>
        {subvalue && <span className="text-xs text-text-muted font-mono">{subvalue}</span>}
      </div>
    </div>
  );
}

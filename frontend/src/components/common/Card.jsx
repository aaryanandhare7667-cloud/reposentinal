import React from 'react';

export function Card({
  children,
  className = '',
  title,
  subtitle,
  actions,
  isAiGenerated = false,
  isRuntimeEvidence = false,
  onClick,
}) {
  let borderClass = 'border border-border';
  if (isAiGenerated) {
    borderClass = 'border border-dashed border-indigo-400/50';
  } else if (isRuntimeEvidence) {
    borderClass = 'border border-solid border-emerald-500/50';
  }

  return (
    <div
      onClick={onClick}
      className={`bg-bg-card rounded ${borderClass} transition-colors ${
        onClick ? 'cursor-pointer hover:border-border-highlight' : ''
      } ${className}`}
    >
      {(title || subtitle || actions) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/80">
          <div>
            {title && <h3 className="text-xs font-semibold text-text-primary tracking-wide">{title}</h3>}
            {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}

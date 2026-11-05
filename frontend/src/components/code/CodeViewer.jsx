import React from 'react';
import { FileCode, AlertCircle } from 'lucide-react';

export function CodeViewer({
  code = '',
  filePath = 'file.py',
  highlightStart = null,
  highlightEnd = null,
  highlightLabel = 'Vulnerable Code Region',
}) {
  const lines = (code || '').split('\n');

  return (
    <div className="rounded border border-border bg-bg-base overflow-hidden">
      {/* Code Header */}
      <div className="px-4 py-2 bg-bg-surface border-b border-border flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-brand-400" />
          <span className="text-text-primary font-semibold">{filePath}</span>
        </div>
        <span className="text-[11px] text-text-muted">{lines.length} lines</span>
      </div>

      {/* Code Body */}
      <div className="overflow-x-auto p-2 font-mono text-xs leading-relaxed">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, idx) => {
              const lineNum = idx + 1;
              const isHighlighted =
                highlightStart !== null &&
                lineNum >= highlightStart &&
                (highlightEnd === null || lineNum <= highlightEnd);

              return (
                <tr
                  key={idx}
                  className={`hover:bg-white/[0.02] ${
                    isHighlighted ? 'bg-red-950/30 border-l-2 border-red-500' : ''
                  }`}
                >
                  <td className="w-12 px-2.5 py-0.5 text-right select-none text-[10px] text-text-muted border-r border-border/40 font-mono">
                    {lineNum}
                  </td>
                  <td className="px-3 py-0.5 whitespace-pre font-mono text-text-secondary">
                    {line}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {highlightStart && (
        <div className="px-3 py-1.5 bg-red-950/20 border-t border-red-500/30 text-[11px] font-mono text-red-400 flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>
            {highlightLabel}: Lines {highlightStart}
            {highlightEnd && highlightEnd !== highlightStart ? `–${highlightEnd}` : ''}
          </span>
        </div>
      )}
    </div>
  );
}

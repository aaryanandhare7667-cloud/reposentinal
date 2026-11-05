import React, { useState } from 'react';
import { Copy, Check, FileDiff, Download } from 'lucide-react';
import { Button } from '../common/Button';

export function DiffViewer({ diff = '', targetFile = 'file.py', patchId = 'PATCH-01' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(diff);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([diff], { type: 'text/x-patch' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${patchId}.patch`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const lines = diff.split('\n');

  return (
    <div className="rounded border border-border bg-bg-base overflow-hidden">
      {/* Diff Header */}
      <div className="px-4 py-2 bg-bg-surface border-b border-border flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-2">
          <FileDiff className="w-4 h-4 text-emerald-400" />
          <span className="text-text-primary font-semibold">{targetFile}</span>
          <span className="text-text-muted text-[11px]">({patchId}.patch)</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" icon={copied ? Check : Copy} onClick={handleCopy}>
            {copied ? 'Copied' : 'Copy Diff'}
          </Button>
          <Button variant="secondary" size="sm" icon={Download} onClick={handleDownload}>
            Download .patch
          </Button>
        </div>
      </div>

      {/* Diff Body */}
      <div className="overflow-x-auto p-2 font-mono text-xs leading-relaxed">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, idx) => {
              let rowStyle = 'text-text-secondary';
              let linePrefix = '';

              if (line.startsWith('---') || line.startsWith('+++')) {
                rowStyle = 'text-text-muted font-bold bg-bg-surface/40';
              } else if (line.startsWith('@@')) {
                rowStyle = 'text-cyan-400 bg-cyan-950/20 font-semibold py-0.5';
              } else if (line.startsWith('+')) {
                rowStyle = 'text-emerald-300 bg-emerald-950/40 border-l-2 border-emerald-500';
                linePrefix = '+';
              } else if (line.startsWith('-')) {
                rowStyle = 'text-red-300 bg-red-950/40 border-l-2 border-red-500';
                linePrefix = '-';
              }

              return (
                <tr key={idx} className={`hover:bg-white/[0.02] ${rowStyle}`}>
                  <td className="w-10 px-2 py-0.5 text-right select-none text-[10px] text-text-muted border-r border-border/40 font-mono">
                    {idx + 1}
                  </td>
                  <td className="px-3 py-0.5 whitespace-pre font-mono">
                    {line}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

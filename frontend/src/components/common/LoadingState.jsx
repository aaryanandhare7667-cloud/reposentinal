import React from 'react';
import { Loader2 } from 'lucide-react';

export function LoadingState({ message = "Scanning repository artifacts..." }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <Loader2 className="w-6 h-6 text-brand-500 animate-spin mb-3" />
      <p className="text-xs font-mono text-text-secondary">{message}</p>
    </div>
  );
}

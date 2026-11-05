import React, { useState } from 'react';
import { 
  Settings as SettingsIcon, 
  Cpu, 
  ShieldCheck, 
  Key, 
  Server, 
  Clock, 
  Save, 
  Check, 
  AlertTriangle,
  FolderLock,
  Layers
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export default function SettingsPage() {
  const [sandboxProvider, setSandboxProvider] = useState('process_jail');
  const [timeoutSeconds, setTimeoutSeconds] = useState(15);
  const [memoryLimitMb, setMemoryLimitMb] = useState(512);
  const [llmProvider, setLlmProvider] = useState('gemini');
  const [geminiApiKey, setGeminiApiKey] = useState('AIzaSyD-••••••••••••••••••••••••••••');
  const [forbidDeletions, setForbidDeletions] = useState(true);
  const [maxDiffLines, setMaxDiffLines] = useState(50);
  const [protectCiCd, setProtectCiCd] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Settings', to: '/settings' },
          { label: 'Engine Configuration', to: '/settings' }
        ]} 
      />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <SettingsIcon className="w-6 h-6 text-indigo-400" />
            Engine & Sandbox Settings
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure ephemeral sandboxing backends, AI hypothesis providers, and patch safety validation rules.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {saved && (
            <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
              <Check className="w-4 h-4" /> Settings updated
            </span>
          )}
          <Button variant="primary" onClick={handleSave} className="flex items-center gap-1.5">
            <Save className="w-4 h-4" />
            Save Configuration
          </Button>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Sandbox Environment */}
        <Card title="1. Ephemeral Sandbox Execution Environment" subtitle="Physical isolation for adversarial test verification">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">
                Isolation Provider
              </label>
              <select
                value={sandboxProvider}
                onChange={(e) => setSandboxProvider(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              >
                <option value="process_jail">Ephemeral Subprocess Jail (Standard)</option>
                <option value="docker">Docker Container (Airgapped Bridge)</option>
                <option value="firecracker" disabled>Firecracker MicroVM (Planned - Unavailable)</option>
              </select>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Local isolated process jail runs on host with zero write permissions to user repo.
              </span>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">
                Execution Timeout Budget
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="5"
                  max="60"
                  value={timeoutSeconds}
                  onChange={(e) => setTimeoutSeconds(parseInt(e.target.value) || 15)}
                  className="w-28 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                />
                <span className="text-xs text-slate-400 font-mono">seconds per adversarial test</span>
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Enforced by SIGKILL if test fails to exit cleanly.
              </span>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">
                Memory Limit (RAM)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="128"
                  max="2048"
                  step="128"
                  value={memoryLimitMb}
                  onChange={(e) => setMemoryLimitMb(parseInt(e.target.value) || 512)}
                  className="w-28 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                />
                <span className="text-xs text-slate-400 font-mono">MB per execution</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">
                Network Policy
              </label>
              <div className="p-2.5 rounded bg-slate-950 border border-slate-800 flex items-center justify-between">
                <span className="text-xs text-emerald-400 font-mono font-semibold">Strict Airgap (Disabled)</span>
                <span className="text-[11px] text-slate-500 font-mono">Immutable</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Section 2: AI Hypothesis Engine */}
        <Card title="2. Autonomous LLM Inference Engine" subtitle="Model provider for AST context analysis & test synthesis">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">
                Inference Provider
              </label>
              <select
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              >
                <option value="gemini">Google Gemini Pro (Advanced Reasoning)</option>
                <option value="openai">OpenAI GPT-4o</option>
                <option value="ollama">Local Ollama (DeepSeek-Coder / Llama 3)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">
                API Authentication Key
              </label>
              <div className="relative">
                <Key className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="password"
                  value={geminiApiKey}
                  onChange={(e) => setGeminiApiKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Section 3: Patch Safety Validator */}
        <Card title="3. Automated Patch Safety Validator Invariants" subtitle="Pre-application security filters for candidate patches">
          <div className="space-y-4">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={forbidDeletions}
                onChange={(e) => setForbidDeletions(e.target.checked)}
                className="rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-0 mt-0.5"
              />
              <div>
                <div className="text-xs font-semibold text-white">Forbid File Deletions</div>
                <div className="text-xs text-slate-400">
                  Reject candidate patches that attempt to delete files or empty existing source modules.
                </div>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={protectCiCd}
                onChange={(e) => setProtectCiCd(e.target.checked)}
                className="rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-0 mt-0.5"
              />
              <div>
                <div className="text-xs font-semibold text-white">Protect CI/CD & Infrastructure Files</div>
                <div className="text-xs text-slate-400">
                  Instantly flag and reject any patch touching .github/, Dockerfile, Makefile, or requirements.txt.
                </div>
              </div>
            </label>

            <div className="pt-2">
              <label className="block text-xs font-mono text-slate-400 mb-1.5 uppercase">
                Maximum Unified Diff Line Delta
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="5"
                  max="200"
                  value={maxDiffLines}
                  onChange={(e) => setMaxDiffLines(parseInt(e.target.value) || 50)}
                  className="w-28 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                />
                <span className="text-xs text-slate-400 font-mono">lines maximum per patch (smallest safe change)</span>
              </div>
            </div>
          </div>
        </Card>

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="primary" type="submit" className="flex items-center gap-1.5">
            <Save className="w-4 h-4" />
            Save Configuration
          </Button>
        </div>
      </form>
    </div>
  );
}

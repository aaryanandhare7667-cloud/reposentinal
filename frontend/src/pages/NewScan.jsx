import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Play,
  Terminal,
  Shield,
  Layers,
  Cpu,
  CheckCircle2,
  Loader2,
  Folder,
  Globe,
  Sliders,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { scanService } from '../services/scanService';

export function NewScan() {
  const navigate = useNavigate();
  const [targetPath, setTargetPath] = useState('tests/fixtures/cross_file_repo/');
  const [provider, setProvider] = useState('MockProvider');
  const [sandboxBackend, setSandboxBackend] = useState('safe_subprocess');
  const [enableTopology, setEnableTopology] = useState(true);
  const [enableVerify, setEnableVerify] = useState(true);
  const [enablePatch, setEnablePatch] = useState(true);
  const [maxFiles, setMaxFiles] = useState(50);
  const [isScanning, setIsScanning] = useState(false);
  const [scanStage, setScanStage] = useState(0);

  const stages = [
    'Preparing repository target & cloning scope...',
    'Scanning source files & filtering binary noise...',
    'Building AST symbol index & dependency topology graph...',
    'Generating cross-module bug hypotheses...',
    'Synthesizing adversarial reproduction tests...',
    'Executing tests in isolated execution sandbox...',
    'Applying candidate patches in ephemeral isolated workspace...',
    'Running dual-phase verification (repro re-test + regression tests)...',
  ];

  const handleLaunch = async (e) => {
    e.preventDefault();
    setIsScanning(true);

    // Simulate animated scanning progress through stages
    for (let i = 0; i < stages.length; i++) {
      setScanStage(i);
      await new Promise((r) => setTimeout(r, 450));
    }

    const newScan = await scanService.triggerScan({
      targetPath,
      provider,
      sandboxBackend,
      enableTopology,
      enableVerify,
      enablePatch,
      maxFiles: parseInt(maxFiles, 10),
    });

    setIsScanning(false);
    navigate(`/scans/${newScan.id}`);
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Scans', to: '/scans' }, { label: 'New Scan' }]} />

      <div className="pb-2 border-b border-border">
        <h1 className="text-lg font-bold text-text-primary tracking-tight">
          Launch Autonomous Bug Discovery Scan
        </h1>
        <p className="text-xs text-text-muted mt-1 font-mono">
          Configure analysis target, LLM provider, isolated execution sandbox, and automated remediation.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Form: Configuration */}
        <div className="lg:col-span-2">
          <Card title="Scan Configuration Parameters">
            <form onSubmit={handleLaunch} className="space-y-5 text-xs font-mono">
              {/* Target Input */}
              <div className="space-y-1.5">
                <label className="block text-text-secondary font-semibold">
                  Target Scope (Local Path or GitHub URL)
                </label>
                <div className="relative">
                  <Folder className="absolute left-3 top-2.5 w-4 h-4 text-text-muted" />
                  <input
                    type="text"
                    value={targetPath}
                    onChange={(e) => setTargetPath(e.target.value)}
                    placeholder="e.g. tests/fixtures/cross_file_repo/ or https://github.com/..."
                    className="w-full pl-9 pr-4 py-2 bg-bg-surface border border-border rounded text-text-primary focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono"
                    required
                  />
                </div>
                <p className="text-[11px] text-text-muted">
                  Supports local paths or remote GitHub repository URLs (cloned shallowly to ephemeral sandbox).
                </p>
              </div>

              {/* Provider Selection */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="block text-text-secondary font-semibold">
                    Hypothesis Engine / Provider
                  </label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-surface border border-border rounded text-text-primary focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono"
                  >
                    <option value="MockProvider">MockProvider (Offline Heuristics)</option>
                    <option value="GeminiProvider">Google Gemini (REST API)</option>
                    <option value="OpenAIProvider">OpenAI / DeepSeek (v1 API)</option>
                    <option value="OllamaProvider">Ollama (Local Open-Source)</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-text-secondary font-semibold">
                    Sandbox Execution Backend
                  </label>
                  <select
                    value={sandboxBackend}
                    onChange={(e) => setSandboxBackend(e.target.value)}
                    className="w-full px-3 py-2 bg-bg-surface border border-border rounded text-text-primary focus:outline-none focus:ring-1 focus:ring-brand-500 font-mono"
                  >
                    <option value="safe_subprocess">SafeSubprocessSandbox (Isolated Process)</option>
                    <option value="docker">DockerSandbox (Containerized --network=none)</option>
                    <option value="auto">Auto (Docker preferred with fallback)</option>
                  </select>
                </div>
              </div>

              {/* Pipeline Flags */}
              <div className="pt-3 border-t border-border space-y-3">
                <span className="block text-text-secondary font-semibold uppercase text-[10px] tracking-wider">
                  Analysis & Remediation Toggles
                </span>

                <div className="space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableTopology}
                      onChange={(e) => setEnableTopology(e.target.checked)}
                      className="rounded border-border text-brand-600 focus:ring-0 bg-bg-surface"
                    />
                    <span className="text-text-primary font-medium">Build Repository Topology Graph (`--topology`)</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableVerify}
                      onChange={(e) => setEnableVerify(e.target.checked)}
                      className="rounded border-border text-brand-600 focus:ring-0 bg-bg-surface"
                    />
                    <span className="text-text-primary font-medium">
                      Execute Sandboxed Adversarial Verification (Default: Enabled)
                    </span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enablePatch}
                      onChange={(e) => setEnablePatch(e.target.checked)}
                      className="rounded border-border text-brand-600 focus:ring-0 bg-bg-surface"
                    />
                    <span className="text-text-primary font-medium">
                      Synthesize & Verify Candidate Patches in Isolated Workspace
                    </span>
                  </label>
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-4 border-t border-border flex justify-end gap-3">
                <Button variant="outline" onClick={() => navigate('/')}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit" icon={Play} disabled={isScanning}>
                  {isScanning ? 'Executing Scan...' : 'Start Scan'}
                </Button>
              </div>
            </form>
          </Card>
        </div>

        {/* Right Info: Safety & Invariant Guarantees */}
        <div className="space-y-4">
          <Card title="Security & Isolation Invariants">
            <div className="space-y-3 text-xs font-mono text-text-secondary leading-relaxed">
              <div className="p-2.5 rounded bg-bg-surface border border-solid border-emerald-500/40">
                <div className="text-emerald-400 font-semibold mb-1 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Host Filesystem Untouched</span>
                </div>
                <p className="text-[11px] text-text-muted">
                  Patches and reproduction tests are generated and executed strictly within ephemeral workspaces. Your local repository files are never modified.
                </p>
              </div>

              <div className="p-2.5 rounded bg-bg-surface border border-dashed border-indigo-400/40">
                <div className="text-indigo-300 font-semibold mb-1 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5" />
                  <span>Deterministic Evidence Required</span>
                </div>
                <p className="text-[11px] text-text-muted">
                  Findings are marked Confirmed Bug only if an isolated reproduction test triggers the vulnerability with proof.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Scanning Progress Overlay Modal */}
      {isScanning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-bg-card border border-border rounded-lg shadow-2xl p-6 max-w-lg w-full text-center space-y-4">
            <div className="inline-flex p-3 rounded-full bg-brand-600/20 text-brand-400 border border-brand-500/40 animate-pulse">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>

            <div>
              <h3 className="text-sm font-bold text-text-primary uppercase tracking-wide">
                RepoSentinel Agent Executing
              </h3>
              <p className="text-xs font-mono text-brand-400 mt-1">
                {stages[scanStage]}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-bg-surface rounded-full h-1.5 overflow-hidden border border-border">
              <div
                className="bg-brand-500 h-full transition-all duration-300"
                style={{ width: `${((scanStage + 1) / stages.length) * 100}%` }}
              />
            </div>

            <div className="text-[11px] font-mono text-text-muted">
              Stage {scanStage + 1} of {stages.length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default NewScan;

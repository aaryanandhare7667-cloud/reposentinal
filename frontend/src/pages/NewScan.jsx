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
  const [provider, setProvider] = useState('mock');
  const [sandboxBackend, setSandboxBackend] = useState('subprocess');
  const [enableTopology, setEnableTopology] = useState(true);
  const [enableVerify, setEnableVerify] = useState(true);
  const [enablePatch, setEnablePatch] = useState(true);
  const [maxFiles, setMaxFiles] = useState(50);
  const [isScanning, setIsScanning] = useState(false);
  const [currentFile, setCurrentFile] = useState('');
  const [progressCount, setProgressCount] = useState({ current: 0, total: 0 });
  const [statusMessage, setStatusMessage] = useState('Initiating scan with backend...');

  const handleLaunch = async (e) => {
    e.preventDefault();
    setIsScanning(true);
    setStatusMessage('Initiating scan with real backend...');

    const newScan = await scanService.triggerScan({
      targetPath,
      provider,
      sandboxBackend,
      enableTopology,
      enableVerify,
      enablePatch,
      maxFiles: parseInt(maxFiles, 10),
    });

    if (!newScan || !newScan.id) {
      setIsScanning(false);
      return;
    }

    // Live polling until backend marks scan COMPLETED or FAILED
    const startTime = Date.now();
    const interval = setInterval(async () => {
      const live = await scanService.getScanById(newScan.id);
      if (live) {
        if (live.progress) {
          setProgressCount({
            current: live.progress.current || 0,
            total: live.progress.total || 0,
          });
          if (live.progress.currentFile) {
            setCurrentFile(live.progress.currentFile);
            setStatusMessage(`Analyzing [${live.progress.current}/${live.progress.total}] -> ${live.progress.currentFile}`);
          } else if (live.status === 'RUNNING') {
            setStatusMessage('Synthesizing AST topology and running sandboxed tests...');
          }
        }

        if (live.status === 'COMPLETED' || live.status === 'FAILED') {
          clearInterval(interval);
          setIsScanning(false);
          navigate(`/scans/${newScan.id}`);
        }
      }

      // Safeguard timeout (15s)
      if (Date.now() - startTime > 15000) {
        clearInterval(interval);
        setIsScanning(false);
        navigate(`/scans/${newScan.id}`);
      }
    }, 400);
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
                    <option value="mock">MockProvider (Offline Heuristics)</option>
                    <option value="gemini">Google Gemini (REST API)</option>
                    <option value="openai">OpenAI / DeepSeek (v1 API)</option>
                    <option value="ollama">Ollama (Local Open-Source)</option>
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
                    <option value="subprocess">SafeSubprocessSandbox (Isolated Process)</option>
                    <option value="docker">DockerSandbox (Containerized --network=none)</option>
                    <option value="auto">Auto (Docker preferred with fallback)</option>
                  </select>
                </div>
              </div>

              {/* Pipeline Flags */}
              <div className="pt-2 border-t border-border space-y-3">
                <div className="text-text-secondary font-semibold">Execution Pipeline Phases</div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <label className="flex items-center gap-2 cursor-pointer p-2 rounded bg-bg-surface border border-border hover:border-text-muted transition-colors">
                    <input
                      type="checkbox"
                      checked={enableTopology}
                      onChange={(e) => setEnableTopology(e.target.checked)}
                      className="rounded bg-bg-card border-border text-brand-500 focus:ring-0"
                    />
                    <span>Phase 2: Topology</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer p-2 rounded bg-bg-surface border border-border hover:border-text-muted transition-colors">
                    <input
                      type="checkbox"
                      checked={enableVerify}
                      onChange={(e) => setEnableVerify(e.target.checked)}
                      className="rounded bg-bg-card border-border text-brand-500 focus:ring-0"
                    />
                    <span>Phase 4: Sandboxed Verification</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer p-2 rounded bg-bg-surface border border-border hover:border-text-muted transition-colors">
                    <input
                      type="checkbox"
                      checked={enablePatch}
                      onChange={(e) => setEnablePatch(e.target.checked)}
                      className="rounded bg-bg-card border-border text-brand-500 focus:ring-0"
                    />
                    <span>Phase 5: Auto Patches</span>
                  </label>
                </div>
              </div>

              {/* Maximum Files Slider */}
              <div className="space-y-1.5 pt-2 border-t border-border">
                <div className="flex justify-between items-center text-text-secondary">
                  <span>File Scan Budget</span>
                  <span className="font-bold text-text-primary">{maxFiles} files max</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="200"
                  step="5"
                  value={maxFiles}
                  onChange={(e) => setMaxFiles(e.target.value)}
                  className="w-full accent-brand-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="pt-4 flex items-center justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/scans')}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  className="flex items-center gap-2 px-5"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>Start Autonomous Scan</span>
                </Button>
              </div>
            </form>
          </Card>
        </div>

        {/* Right Panel: Informational Architecture */}
        <div className="space-y-4">
          <Card title="Autonomous Pipeline Workflow">
            <div className="space-y-3 font-mono text-xs text-text-muted">
              <div className="flex items-start gap-2.5">
                <div className="w-5 h-5 rounded bg-bg-surface border border-border flex items-center justify-center text-[10px] text-brand-400 font-bold shrink-0 mt-0.5">
                  1
                </div>
                <div>
                  <strong className="text-text-primary block">Repository Scan & AST Index</strong>
                  Walks filesystem, extracts classes, functions, calls, and imports without code execution.
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <div className="w-5 h-5 rounded bg-bg-surface border border-border flex items-center justify-center text-[10px] text-brand-400 font-bold shrink-0 mt-0.5">
                  2
                </div>
                <div>
                  <strong className="text-text-primary block">Repository-Aware Hypothesis</strong>
                  Synthesizes cross-file bug hypotheses based on contract mismatches and tainted sinks.
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <div className="w-5 h-5 rounded bg-bg-surface border border-border flex items-center justify-center text-[10px] text-brand-400 font-bold shrink-0 mt-0.5">
                  3
                </div>
                <div>
                  <strong className="text-text-primary block">Ephemeral Sandboxed Verification</strong>
                  Executes targeted adversarial tests inside isolated jail to prove vulnerability presence.
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <div className="w-5 h-5 rounded bg-bg-surface border border-border flex items-center justify-center text-[10px] text-brand-400 font-bold shrink-0 mt-0.5">
                  4
                </div>
                <div>
                  <strong className="text-text-primary block">Automated Patch & Regression Verification</strong>
                  Generates minimal safe unified diffs and validates via reproduction re-test and regression suite.
                </div>
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
                {statusMessage}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-bg-surface rounded-full h-1.5 overflow-hidden border border-border">
              <div
                className="bg-brand-500 h-full transition-all duration-300"
                style={{
                  width: progressCount.total > 0
                    ? `${Math.max(10, (progressCount.current / progressCount.total) * 100)}%`
                    : '45%'
                }}
              />
            </div>

            <div className="text-[11px] font-mono text-text-muted">
              {progressCount.total > 0
                ? `Processed ${progressCount.current} of ${progressCount.total} files`
                : 'Isolated execution sandbox active'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default NewScan;

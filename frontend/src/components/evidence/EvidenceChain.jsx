import React from 'react';
import {
  FileCode,
  Network,
  Bot,
  FlaskConical,
  ShieldCheck,
  Wrench,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

export function EvidenceChain({
  currentStep = 7, // 1 to 7
  hasReproduction = true,
  hasPatch = true,
  isPatchVerified = true,
}) {
  const steps = [
    {
      id: 1,
      title: 'Repository Scan & AST Index',
      desc: 'Extracted symbols & inter-file dependencies',
      icon: FileCode,
      status: 'complete',
      isEvidence: true,
    },
    {
      id: 2,
      title: 'Cross-Module Topology',
      desc: 'Mapped caller usages & function contracts',
      icon: Network,
      status: 'complete',
      isEvidence: true,
    },
    {
      id: 3,
      title: 'Bug Hypothesis',
      desc: 'AI Reasoning: Unchecked return assumption',
      icon: Bot,
      status: 'complete',
      isEvidence: false, // AI claim -> dashed border
    },
    {
      id: 4,
      title: 'Adversarial Reproduction Test',
      desc: 'Synthesized test with mock dependency',
      icon: FlaskConical,
      status: 'complete',
      isEvidence: true,
    },
    {
      id: 5,
      title: 'Sandboxed Execution',
      desc: hasReproduction ? 'Triggered TypeError in isolated sandbox' : 'Execution inconclusive',
      icon: ShieldCheck,
      status: hasReproduction ? 'complete' : 'pending',
      isEvidence: true,
    },
    {
      id: 6,
      title: 'Candidate Patch Synthesis',
      desc: hasPatch ? 'Synthesized targeted null guard patch' : 'Pending',
      icon: Wrench,
      status: hasPatch ? 'complete' : 'pending',
      isEvidence: false, // Candidate patch
    },
    {
      id: 7,
      title: 'Dual-Phase Patch Verification',
      desc: isPatchVerified
        ? 'Passed RepoSentinel sandbox re-test and regression checks.'
        : 'Regression check pending',
      icon: CheckCircle2,
      status: isPatchVerified ? 'complete' : 'pending',
      isEvidence: true,
    },
  ];

  return (
    <div className="py-2">
      <div className="flex items-center justify-between mb-3 text-xs font-mono text-text-muted">
        <span className="uppercase tracking-wider">Verification & Remediation Pipeline</span>
        <span className="text-emerald-400 font-semibold">
          {isPatchVerified ? '7/7 Stages Confirmed' : 'Pipeline in Progress'}
        </span>
      </div>

      <div className="relative pl-6 space-y-4 before:content-[''] before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-border">
        {steps.map((step) => {
          const Icon = step.icon;
          const isComplete = step.status === 'complete';
          const isAiClaim = !step.isEvidence;

          return (
            <div key={step.id} className="relative flex items-start gap-3 group">
              {/* Step Marker */}
              <div
                className={`absolute -left-6 mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs font-mono transition-colors ${
                  isComplete
                    ? isAiClaim
                      ? 'bg-indigo-950 border border-dashed border-indigo-400 text-indigo-300'
                      : 'bg-emerald-950 border border-solid border-emerald-400 text-emerald-300'
                    : 'bg-bg-elevated border border-border text-text-muted'
                }`}
              >
                {step.id}
              </div>

              {/* Step Card */}
              <div
                className={`flex-1 p-3 rounded text-xs transition-colors ${
                  isAiClaim
                    ? 'border border-dashed border-indigo-400/40 bg-indigo-950/10'
                    : 'border border-solid border-border/80 bg-bg-card'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <Icon
                      className={`w-3.5 h-3.5 ${
                        isAiClaim ? 'text-indigo-400' : 'text-emerald-400'
                      }`}
                    />
                    <span className="font-semibold text-text-primary">{step.title}</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                      isAiClaim
                        ? 'border border-dashed border-indigo-400/60 text-indigo-300'
                        : 'border border-solid border-emerald-500/60 text-emerald-400'
                    }`}
                  >
                    {isAiClaim ? 'AI Claim' : 'Runtime Evidence'}
                  </span>
                </div>
                <p className="text-text-secondary font-mono text-[11px]">{step.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Bug,
  FlaskConical,
  Wrench,
  CheckCircle2,
  FileCode,
  Network,
  AlertCircle,
  HelpCircle,
  Terminal,
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { SeverityBadge, StatusBadge } from '../components/common/Badge';
import { CodeViewer } from '../components/code/CodeViewer';
import { EvidenceChain } from '../components/evidence/EvidenceChain';
import { findingsService } from '../services/findingsService';
import { repositoryService } from '../services/repositoryService';

export function FindingDetail() {
  const { id } = useParams();
  const [finding, setFinding] = useState(null);
  const [sourceCode, setSourceCode] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const f = await findingsService.getFindingById(id);
      setFinding(f);
      if (f && f.affectedFile) {
        const code = await repositoryService.getFileContent(f.affectedFile);
        setSourceCode(code);
      }
      setLoading(false);
    }
    loadData();
  }, [id]);

  if (loading) {
    return <div className="p-8 text-center text-xs font-mono text-text-muted">Loading finding details...</div>;
  }

  if (!finding) {
    return (
      <div className="p-8 text-center text-xs font-mono text-text-muted">
        Finding {id} was not found.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Findings', to: '/findings' },
          { label: finding.id },
        ]}
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-3 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-mono text-brand-400 font-bold">{finding.id}</span>
            <SeverityBadge severity={finding.severity} />
            <StatusBadge
              status={finding.status}
              isAiGenerated={finding.isAiGenerated}
              isRuntimeEvidence={finding.isRuntimeEvidence}
            />
          </div>
          <h1 className="text-lg font-bold text-text-primary tracking-tight">
            {finding.title}
          </h1>
          <div className="flex items-center gap-2 mt-1 text-xs font-mono text-text-muted">
            <span className="text-text-secondary">{finding.affectedFile}:{finding.lineStart}–{finding.lineEnd}</span>
            <span>•</span>
            <span>Symbol: <strong className="text-text-primary">{finding.affectedSymbol}</strong></span>
            <span>•</span>
            <span>Category: {finding.category}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {finding.verificationEvidenceId && (
            <Link to={`/verification/${finding.verificationEvidenceId}`}>
              <Button variant="secondary" size="sm" icon={FlaskConical}>
                Sandbox Log
              </Button>
            </Link>
          )}
          {finding.patchId && (
            <Link to={`/patches/${finding.patchId}/diff`}>
              <Button variant="verified" size="sm" icon={Wrench}>
                Verified Diff
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Grid: Details & Evidence Chain */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Explanation, Code Context, Remediation */}
        <div className="lg:col-span-2 space-y-5">
          {/* Explanation Card */}
          <Card title="Hypothesis Analysis & Reasoning">
            <div className="space-y-3 text-xs leading-relaxed">
              <div>
                <h4 className="text-[11px] font-mono uppercase text-text-muted mb-1 font-semibold">
                  Explanation
                </h4>
                <p className="text-text-secondary">{finding.explanation}</p>
              </div>

              <div className="pt-2 border-t border-border">
                <h4 className="text-[11px] font-mono uppercase text-text-muted mb-1 font-semibold">
                  Cross-Module Architectural Reasoning
                </h4>
                <p className="text-text-secondary">{finding.reasoning}</p>
              </div>

              {finding.relatedSymbols?.length > 0 && (
                <div className="pt-2 border-t border-border">
                  <h4 className="text-[11px] font-mono uppercase text-text-muted mb-1 font-semibold">
                    Related Symbols & Dependencies
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {finding.relatedSymbols.map((sym, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-bg-surface border border-border text-[11px] font-mono text-text-secondary"
                      >
                        {sym}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Code Viewer with Highlighted Vulnerability */}
          <div>
            <h3 className="text-xs font-mono font-semibold uppercase text-text-muted mb-2 tracking-wider">
              Source Code Context ({finding.affectedFile})
            </h3>
            <CodeViewer
              code={sourceCode}
              filePath={finding.affectedFile}
              highlightStart={finding.lineStart}
              highlightEnd={finding.lineEnd}
              highlightLabel="Vulnerable Symbol Definition"
            />
          </div>

          {/* Suggested Reproduction Test & Remediation */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card title="Suggested Reproduction Scenario">
              <p className="text-xs text-text-secondary font-mono leading-relaxed">
                {finding.suggestedTest}
              </p>
            </Card>

            <Card title="Remediation Strategy">
              <p className="text-xs text-emerald-300 font-mono leading-relaxed">
                {finding.remediation}
              </p>
            </Card>
          </div>
        </div>

        {/* Right Col: Lifecycle Stepper & Status */}
        <div className="space-y-4">
          <Card title="Verification Lifecycle">
            <EvidenceChain
              currentStep={7}
              hasReproduction={Boolean(finding.verificationEvidenceId)}
              hasPatch={Boolean(finding.patchId)}
              isPatchVerified={Boolean(finding.patchId)}
            />
          </Card>

          <Card title="Verification Rule Invariant">
            <div className="p-3 rounded bg-bg-surface border border-border text-xs font-mono text-text-secondary leading-relaxed">
              <p className="mb-2">
                <strong className="text-emerald-400">Deterministic Confirmation:</strong> Findings are only promoted to <span className="text-emerald-400 font-bold">Confirmed Bug</span> when an isolated test triggers runtime failure.
              </p>
              <p className="text-text-muted text-[11px]">
                LLM prompt responses alone can never confirm a vulnerability.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default FindingDetail;

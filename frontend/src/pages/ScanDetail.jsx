import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Terminal,
  Shield,
  Clock,
  FileCode,
  FlaskConical,
  Wrench,
  Network,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { MetricCard } from '../components/metrics/MetricCard';
import { Card } from '../components/common/Card';
import { SeverityBadge, StatusBadge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { scanService } from '../services/scanService';
import { findingsService } from '../services/findingsService';
import { patchService } from '../services/patchService';

export function ScanDetail() {
  const { id } = useParams();
  const [scan, setScan] = useState(null);
  const [findings, setFindings] = useState([]);
  const [patches, setPatches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let timer = null;
    let isMounted = true;

    async function loadScanData() {
      const s = await scanService.getScanById(id);
      if (!isMounted) return;

      if (s) {
        setScan(s);
        const f = await findingsService.getFindings({ scanId: id });
        const p = await patchService.getPatches();
        if (isMounted) {
          setFindings(f.length > 0 ? f : await findingsService.getFindings());
          setPatches(p);
          setLoading(false);
        }

        if (s.status === 'RUNNING' || s.status === 'QUEUED') {
          timer = setTimeout(loadScanData, 1000);
        }
      } else {
        setLoading(false);
      }
    }

    loadScanData();
    return () => {
      isMounted = false;
      if (timer) clearTimeout(timer);
    };
  }, [id]);

  if (loading) return <LoadingState message="Loading scan execution artifacts..." />;
  if (!scan) return <EmptyState title="Scan Not Found" description={`No scan execution record found with ID ${id}`} type="empty" />;

  const isScopeClean = (scan.counts?.total || 0) === 0;

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Scans', to: '/scans' }, { label: scan.id }]} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-text-primary tracking-tight font-mono">
              {scan.id}
            </h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950/30 border border-emerald-500/40 text-emerald-400">
              {scan.status}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs font-mono text-text-muted">
            <span>Target: <strong className="text-text-primary">{scan.targetPath}</strong></span>
            <span>•</span>
            <span>Provider: <strong className="text-text-primary">{scan.provider}</strong></span>
            <span>•</span>
            <span>Sandbox: <strong className="text-text-primary">{scan.sandboxBackend}</strong></span>
            <span>•</span>
            <span>Duration: <strong className="text-text-primary">{scan.durationSeconds}s</strong></span>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <MetricCard
          title="Scanned Files"
          value={scan.scannedFiles}
          subvalue={`${scan.totalLines} lines analyzed`}
          icon={FileCode}
          variant="default"
        />
        <MetricCard
          title="Confirmed Bugs"
          value={(scan.counts?.critical || 0) + (scan.counts?.high || 0)}
          subvalue={`${scan.counts?.critical || 0} Critical • ${scan.counts?.high || 0} High`}
          icon={AlertTriangle}
          variant={(scan.counts?.total || 0) > 0 ? 'critical' : 'success'}
        />
        <MetricCard
          title="Sandbox Repro Rate"
          value={
            scan.verificationMetrics?.reproductionRate ||
            (scan.verification_metrics?.reproduction_rate !== undefined
              ? `${Math.round(scan.verification_metrics.reproduction_rate * 100)}%`
              : '0%')
          }
          subvalue={`${scan.verificationMetrics?.reproduced ?? scan.verification_metrics?.reproduced_count ?? 0} reproduced`}
          icon={FlaskConical}
          variant="cyan"
        />
        <MetricCard
          title="Verified Patches"
          value={scan.patchMetrics?.totalVerified ?? scan.patch_metrics?.patches_verified ?? 0}
          subvalue={`${scan.patchMetrics?.fixRate || (scan.patch_metrics?.vulnerability_fix_rate !== undefined ? `${Math.round(scan.patch_metrics.vulnerability_fix_rate * 100)}%` : '0%')} Fix Rate`}
          icon={Wrench}
          variant="success"
        />
      </div>

      {/* Findings Section */}
      {isScopeClean ? (
        <EmptyState
          title="No findings in the scanned scope"
          description="All scanned files and symbols completed AST analysis, heuristic auditing, and sandboxed checks with zero vulnerabilities flagged."
          type="clean"
        />
      ) : (
        <Card title={`Discovered Findings & Hypotheses (${findings.length})`}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left font-mono">
              <thead className="bg-bg-surface text-text-muted uppercase text-[10px] border-b border-border">
                <tr>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Finding Title</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Location</th>
                  <th className="py-2.5 px-3">Verification Evidence</th>
                  <th className="py-2.5 px-3">Patch</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {findings.map((f) => (
                  <tr key={f.id} className="hover:bg-bg-surface/50 transition-colors">
                    <td className="py-2.5 px-3">
                      <SeverityBadge severity={f.severity} />
                    </td>
                    <td className="py-2.5 px-3 font-medium text-text-primary">
                      <Link to={`/findings/${f.id}`} className="hover:text-brand-400">
                        {f.title}
                      </Link>
                      <div className="text-[11px] text-text-muted truncate max-w-sm mt-0.5">
                        {f.explanation}
                      </div>
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge
                        status={f.status}
                        isAiGenerated={f.isAiGenerated}
                        isRuntimeEvidence={f.isRuntimeEvidence}
                      />
                    </td>
                    <td className="py-2.5 px-3 text-text-secondary">
                      {f.affectedFile}:{f.lineStart}
                    </td>
                    <td className="py-2.5 px-3">
                      {f.verificationEvidenceId ? (
                        <Link
                          to={`/verification/${f.verificationEvidenceId}`}
                          className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                        >
                          <FlaskConical className="w-3.5 h-3.5" />
                          <span>Reproduced</span>
                        </Link>
                      ) : (
                        <span className="text-text-muted">Not Run</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3">
                      {f.patchId ? (
                        <Link
                          to={`/patches/${f.patchId}`}
                          className="text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
                        >
                          <Wrench className="w-3.5 h-3.5" />
                          <span>Verified Diff</span>
                        </Link>
                      ) : (
                        <span className="text-text-muted">Unavailable</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Verified Patches Queue */}
      {patches.length > 0 && !isScopeClean && (
        <Card title={`Remediation Patches (${patches.length})`}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {patches.map((p) => (
              <div
                key={p.id}
                className={`p-3.5 rounded ${
                  p.isVerified
                    ? 'border border-solid border-emerald-500/40 bg-bg-card'
                    : 'border border-dashed border-indigo-400/40 bg-indigo-950/10'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono font-bold text-text-primary">
                    {p.targetFile}
                  </span>
                  <StatusBadge
                    status={p.verificationStatus}
                    isRuntimeEvidence={p.isVerified}
                    isAiGenerated={!p.isVerified}
                  />
                </div>
                <p className="text-xs text-text-secondary mb-3">{p.patchObjective}</p>
                <div className="flex items-center justify-between text-xs font-mono pt-2 border-t border-border">
                  <span className="text-[11px] text-text-muted">
                    {p.isVerified ? 'Passed re-test & regression checks' : 'Candidate Patch (Unverified)'}
                  </span>
                  <Link to={`/patches/${p.id}/diff`} className="text-brand-400 hover:text-brand-300">
                    View Diff &rarr;
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

export default ScanDetail;

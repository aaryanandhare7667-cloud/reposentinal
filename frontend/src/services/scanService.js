import { request } from './api';
import { mockScans } from '../data/mockData';

export const scanService = {
  async getScans() {
    const live = await request('/scans');
    return live || mockScans;
  },

  async getScanById(id) {
    const live = await request(`/scans/${id}`);
    if (live) return live;
    return mockScans.find((s) => s.id === id) || null;
  },

  async triggerScan(payload) {
    const live = await request('/scans', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (live) return live;

    // Simulated new scan run
    const newScan = {
      id: `SCN-${Date.now().toString().slice(-6)}`,
      repositoryId: payload.repositoryId || 'repo-1',
      repositoryName: payload.repositoryName || payload.targetPath.split('/').filter(Boolean).pop() || 'target-repo',
      targetPath: payload.targetPath,
      branch: payload.branch || 'main',
      commitSha: payload.commitSha || 'a1b2c3d',
      status: 'COMPLETED',
      provider: payload.provider || 'MockProvider',
      sandboxBackend: payload.sandboxBackend || 'safe_subprocess',
      scannedFiles: 3,
      totalLines: 32,
      durationSeconds: 0.54,
      createdAt: new Date().toISOString(),
      counts: {
        critical: 2,
        high: 1,
        medium: 0,
        low: 0,
        info: 0,
        total: 2,
      },
      hypothesisMetrics: {
        total: 2,
        confirmed: 2,
        likely: 0,
        potential: 0,
        crossFileRatio: '50%',
        symbolMappedCount: 2,
      },
      verificationMetrics: {
        testsGenerated: 2,
        testsExecuted: 2,
        reproduced: 2,
        falsePositives: 0,
        inconclusive: 0,
        reproductionRate: '100%',
        avgDurationSeconds: 0.11,
      },
      patchMetrics: {
        totalGenerated: 2,
        totalVerified: 2,
        regressionsDetected: 0,
        fixRate: '100%',
        avgVerificationSeconds: 0.16,
      },
    };
    return newScan;
  },
};

export const getScans = scanService.getScans;
export const getScanById = scanService.getScanById;
export const triggerScan = scanService.triggerScan;

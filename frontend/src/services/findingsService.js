import { request } from './api';

export const findingsService = {
  async getFindings(filters = {}) {
    const live = await request('/findings');
    let findings = live !== null ? live : [];

    if (filters.severity) {
      findings = findings.filter((f) => f.severity.toLowerCase() === filters.severity.toLowerCase());
    }
    if (filters.status) {
      findings = findings.filter((f) => f.status.toLowerCase() === filters.status.toLowerCase());
    }
    if (filters.scanId) {
      findings = findings.filter((f) => f.scanId === filters.scanId);
    }
    return findings;
  },

  async getFindingById(id) {
    const live = await request(`/findings/${id}`);
    return live || null;
  },
};

export const getFindings = findingsService.getFindings;
export const getFindingById = findingsService.getFindingById;

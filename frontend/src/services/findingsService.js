import { request } from './api';
import { mockFindings } from '../data/mockData';

export const findingsService = {
  async getFindings(filters = {}) {
    const live = await request('/findings');
    let findings = live || mockFindings;

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
    if (live) return live;
    return mockFindings.find((f) => f.id === id) || null;
  },
};

export const getFindings = findingsService.getFindings;
export const getFindingById = findingsService.getFindingById;

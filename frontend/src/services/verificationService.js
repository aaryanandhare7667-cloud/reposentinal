import { request } from './api';
import { mockVerifications } from '../data/mockData';

export const verificationService = {
  async getVerifications() {
    const live = await request('/verifications');
    return live || mockVerifications;
  },

  async getVerificationById(id) {
    const live = await request(`/verifications/${id}`);
    if (live) return live;
    return mockVerifications.find((v) => v.id === id || v.hypothesisId === id) || null;
  },
};

export const getVerifications = verificationService.getVerifications;
export const getVerificationById = verificationService.getVerificationById;

import { request } from './api';

export const verificationService = {
  async getVerifications() {
    const live = await request('/verifications');
    return live !== null ? live : [];
  },

  async getVerificationById(id) {
    const live = await request(`/verifications/${id}`);
    return live || null;
  },
};

export const getVerifications = verificationService.getVerifications;
export const getVerificationById = verificationService.getVerificationById;

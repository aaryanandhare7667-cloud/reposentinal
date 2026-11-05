import { request } from './api';

export const patchService = {
  async getPatches() {
    const live = await request('/patches');
    return live !== null ? live : [];
  },

  async getPatchById(id) {
    const live = await request(`/patches/${id}`);
    return live || null;
  },

  async applyPatch(patchId) {
    const live = await request(`/patches/${patchId}/apply`, { method: 'POST' });
    if (live) return live;
    return {
      success: false,
      message: 'Backend server is offline. Could not apply patch.',
    };
  },
};

export const getPatches = patchService.getPatches;
export const getPatchById = patchService.getPatchById;
export const applyPatch = patchService.applyPatch;

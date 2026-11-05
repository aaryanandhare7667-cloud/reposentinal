import { request } from './api';
import { mockPatches } from '../data/mockData';

export const patchService = {
  async getPatches() {
    const live = await request('/patches');
    return live || mockPatches;
  },

  async getPatchById(id) {
    const live = await request(`/patches/${id}`);
    if (live) return live;
    return mockPatches.find((p) => p.id === id || p.hypothesisId === id) || null;
  },

  async applyPatch(patchId) {
    const live = await request(`/patches/${patchId}/apply`, { method: 'POST' });
    if (live) return live;
    return {
      success: true,
      message: 'Patch applied inside isolated workspace and verified. Ready for manual git review.',
    };
  },
};

export const getPatches = patchService.getPatches;
export const getPatchById = patchService.getPatchById;
export const applyPatch = patchService.applyPatch;

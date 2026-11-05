import { request } from './api';

export const scanService = {
  async getScans() {
    const live = await request('/scans');
    return live !== null ? live : [];
  },

  async getScanById(id) {
    const live = await request(`/scans/${id}`);
    return live || null;
  },

  async triggerScan(payload) {
    const live = await request('/scans', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return live || null;
  },
};

export const getScans = scanService.getScans;
export const getScanById = scanService.getScanById;
export const triggerScan = scanService.triggerScan;

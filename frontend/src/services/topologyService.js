import { request } from './api';
import { mockTopology } from '../data/mockData';

export const topologyService = {
  async getTopology() {
    const live = await request('/topology');
    return live || mockTopology;
  },
};

export const getTopology = topologyService.getTopology;

import { request } from './api';

export const topologyService = {
  async getTopology() {
    const live = await request('/topology');
    return live || {
      nodes: [],
      edges: [],
      summary: {
        totalFiles: 0,
        totalSymbols: 0,
        totalDependencies: 0,
        criticalPaths: 0,
      },
    };
  },
};

export const getTopology = topologyService.getTopology;

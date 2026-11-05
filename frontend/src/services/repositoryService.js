import { request } from './api';
import { mockRepositories, mockCodeFiles } from '../data/mockData';

export const repositoryService = {
  async getRepositories() {
    const live = await request('/repositories');
    return live || mockRepositories;
  },

  async getRepositoryById(id) {
    const live = await request(`/repositories/${id}`);
    if (live) return live;
    return mockRepositories.find((r) => r.id === id || r.name === id) || null;
  },

  async getFileContent(filePath) {
    const live = await request(`/files?path=${encodeURIComponent(filePath)}`);
    if (live) return live.content;
    const baseName = filePath.split('/').pop();
    return mockCodeFiles[baseName] || mockCodeFiles[filePath] || '# File not loaded or unavailable in offline demo';
  },
};

export const getRepositories = repositoryService.getRepositories;
export const getRepositoryById = repositoryService.getRepositoryById;
export const getFileContent = repositoryService.getFileContent;

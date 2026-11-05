import { request } from './api';

export const repositoryService = {
  async getRepositories() {
    const live = await request('/repositories');
    return live || [];
  },

  async getRepositoryById(id) {
    const live = await request(`/repositories/${id}`);
    return live || null;
  },

  async getFileContent(filePath) {
    const live = await request(`/files?path=${encodeURIComponent(filePath)}`);
    if (live) return live.content;
    return null;
  },
};

export const getRepositories = repositoryService.getRepositories;
export const getRepositoryById = repositoryService.getRepositoryById;
export const getFileContent = repositoryService.getFileContent;

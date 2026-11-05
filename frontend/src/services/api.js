/**
 * Base API client with backend integration point.
 * Connects the React frontend to the real RepoSentinel localhost Python API.
 * If the API is available, real backend data is strictly preferred.
 * If backend is offline/unreachable, gracefully falls back to mock models.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export async function request(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    
    if (!res.ok) {
      if (res.status === 404) {
        return null;
      }
      const errBody = await res.json().catch(() => ({}));
      console.warn(`[RepoSentinel API] ${res.status}: ${errBody.error || res.statusText}`);
      return null;
    }
    
    return await res.json();
  } catch (err) {
    // Backend offline / network failure: fallback to demo store
    console.debug(`[RepoSentinel API] Backend unavailable at ${API_BASE_URL}${endpoint}. Utilizing fallback data layer.`);
    return null;
  }
}

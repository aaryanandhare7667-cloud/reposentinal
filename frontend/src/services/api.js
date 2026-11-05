/**
 * Base API client with backend integration point.
 * Initially checks if a live backend REST server is reachable; if not, safely
 * falls back to local data store without throwing unhandled exceptions.
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
      throw new Error(`HTTP Error ${res.status}: ${res.statusText}`);
    }
    
    return await res.json();
  } catch (err) {
    // If backend server is not running, log cleanly and return null for service layer fallback
    console.debug(`[RepoSentinel API] Backend unavailable at ${API_BASE_URL}${endpoint}. Utilizing fallback data layer.`);
    return null;
  }
}

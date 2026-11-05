/**
 * Base API client with backend integration point.
 * Connects the React frontend to the real RepoSentinel localhost Python API.
 * If backend is offline/unreachable, notifies listeners and prevents inventing fake security verdicts.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

let isBackendOnline = true;
let statusListeners = new Set();

export function getBackendStatus() {
  return isBackendOnline;
}

export function subscribeBackendStatus(listener) {
  statusListeners.add(listener);
  // Initial callback
  listener(isBackendOnline);
  return () => statusListeners.delete(listener);
}

function setBackendStatus(status) {
  if (isBackendOnline !== status) {
    isBackendOnline = status;
    statusListeners.forEach((fn) => fn(status));
  }
}

export async function checkBackendHealth() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal });
    clearTimeout(timeoutId);
    const ok = res.ok;
    setBackendStatus(ok);
    return ok;
  } catch {
    setBackendStatus(false);
    return false;
  }
}

export async function request(endpoint, options = {}) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      signal: options.signal || controller.signal,
      ...options,
    });
    clearTimeout(timeoutId);

    setBackendStatus(true);

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
    setBackendStatus(false);
    console.warn(`[RepoSentinel API] Backend unavailable at ${API_BASE_URL}${endpoint}`);
    return null;
  }
}

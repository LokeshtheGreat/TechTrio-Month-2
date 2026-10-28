/**
 * API service for PhishShift frontend.
 * Communicates with the Flask backend REST API.
 */

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL || '';
const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '');

export async function analyzeMessage(message) {
  const trimmed = (message || '').trim();
  if (!trimmed) {
    throw new Error('Please enter a message to analyze.');
  }

  const endpoint = `${API_BASE_URL}/predict`;

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: trimmed }),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = data?.error || `Server responded with status ${response.status}: ${response.statusText}`;
      throw new Error(errorMsg);
    }

    if (!data || typeof data !== 'object') {
      throw new Error('Received an invalid or malformed response from the backend service.');
    }

    return data;
  } catch (err) {
    // Distinguish between network connection errors and backend rejection
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Unable to connect to the PhishShift backend service. Please check your network connection or verify that the backend server is running and accessible.');
    }
    throw err;
  }
}

/**
 * Checks backend health and reachability with timeout handling.
 * Returns structured health state (checking | online | offline | degraded).
 */
export async function checkBackendHealth(options = {}) {
  const { timeoutMs = 8000, externalSignal } = options;
  const endpoint = `${API_BASE_URL}/health`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  if (externalSignal) {
    if (externalSignal.aborted) {
      clearTimeout(timeoutId);
      return {
        state: 'checking',
        healthy: false,
        modelLoaded: false,
        message: 'Checking...',
      };
    }
    externalSignal.addEventListener('abort', () => controller.abort(), { once: true });
  }

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        state: 'degraded',
        healthy: false,
        modelLoaded: false,
        message: 'Service Degraded',
      };
    }

    const data = await response.json();
    const isHealthy = data && data.status === 'healthy' && Boolean(data.model_loaded);

    if (isHealthy) {
      return {
        state: 'online',
        healthy: true,
        modelLoaded: true,
        version: data.version || '1.0',
        message: 'Online',
      };
    }

    return {
      state: 'degraded',
      healthy: false,
      modelLoaded: Boolean(data?.model_loaded),
      message: 'Service Degraded',
    };
  } catch {
    clearTimeout(timeoutId);
    return {
      state: 'offline',
      healthy: false,
      modelLoaded: false,
      message: 'Offline / Unreachable',
    };
  }
}

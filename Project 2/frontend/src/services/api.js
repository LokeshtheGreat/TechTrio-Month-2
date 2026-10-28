/**
 * API service for PhishShift frontend.
 * Communicates with the Flask backend REST API.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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
      throw new Error('Unable to connect to the PhishShift backend server. Please verify that the Flask service is running on port 5000.');
    }
    throw err;
  }
}

export async function checkBackendHealth() {
  const endpoint = `${API_BASE_URL}/health`;
  try {
    const response = await fetch(endpoint, { method: 'GET' });
    if (!response.ok) return { healthy: false };
    const data = await response.json();
    return {
      healthy: data.status === 'healthy',
      modelLoaded: Boolean(data.model_loaded),
      version: data.version || '1.0',
    };
  } catch {
    return { healthy: false, modelLoaded: false };
  }
}

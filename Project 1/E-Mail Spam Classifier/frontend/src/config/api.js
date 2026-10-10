import axios from 'axios';
import { supabase } from '../lib/supabaseClient.js';

/**
 * Resolves the backend base URL for API requests and OAuth flows.
 * In production (e.g., Vercel), uses VITE_BACKEND_URL.
 * Strips any trailing slashes to prevent malformed double-slash paths (e.g., '//api/...').
 * In local development, falls back cleanly to 'http://localhost:5000'.
 */
export const getBackendUrl = () => {
  const envUrl = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL) || process.env?.VITE_BACKEND_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, '');
  }
  return 'http://localhost:5000';
};

/**
 * Safely retrieves the current Supabase session access token.
 * Validates expiration and attempts automatic session refresh if nearing expiry.
 * Returns null if the user is unauthenticated or the session has expired.
 */
export const getAuthToken = async () => {
  if (!supabase) return null;
  try {
    const { data, error } = await supabase.auth.getSession();
    if (error || !data?.session) {
      return null;
    }
    const session = data.session;
    if (session.expires_at && session.expires_at * 1000 < Date.now() + 30000) {
      const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession();
      if (!refreshError && refreshData?.session?.access_token) {
        return refreshData.session.access_token;
      }
      return null;
    }
    return session.access_token || null;
  } catch (err) {
    console.error('Failed to get Supabase session token:', err);
    return null;
  }
};

/**
 * Constructs Authorization headers with the verified Supabase bearer token.
 */
export const getAuthHeaders = async () => {
  const token = await getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * Initiates the Gmail OAuth flow by requesting the Google authorization URL
 * from the configured backend using the authenticated Supabase access token.
 * 
 * @returns {Promise<string>} The Google authorization URL.
 * @throws {Error} When unauthenticated, session expired, or request fails.
 */
export const initiateGmailConnect = async () => {
  const token = await getAuthToken();
  if (!token) {
    throw new Error('You are not signed in or your session has expired. Please sign in again.');
  }

  const backendUrl = getBackendUrl();
  const res = await axios.get(`${backendUrl}/api/gmail/connect?format=json`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/json',
    },
  });

  if (res.data?.auth_url) {
    return res.data.auth_url;
  }

  throw new Error('No authorization URL returned from the server.');
};

/**
 * Safely fetches the Gmail connection status for the authenticated user.
 * Sends Authorization: Bearer <access_token>.
 *
 * If the user is unauthenticated or the session has not yet restored,
 * returns { connected: false, unauthenticated: true } immediately without
 * sending an unauthenticated request to the backend.
 *
 * @param {string|null} [explicitToken] Optional token to use instead of fetching from session.
 * @returns {Promise<{ connected: boolean, email?: string, unauthenticated?: boolean }>}
 */
export const fetchGmailStatus = async (explicitToken = null) => {
  const token = explicitToken || (await getAuthToken());
  if (!token) {
    return { connected: false, unauthenticated: true };
  }

  try {
    const res = await axios.get(`${getBackendUrl()}/api/gmail/status`, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/json',
      },
    });
    return res.data;
  } catch (err) {
    if (err.response?.status === 401) {
      return { connected: false, unauthenticated: true, error: 'Session expired' };
    }
    throw err;
  }
};


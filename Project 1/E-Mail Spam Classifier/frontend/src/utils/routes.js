/**
 * Routing and recovery parameter helpers for Email Spam Shield.
 * Supports standard pathname navigation (/privacy-policy, /terms, /reset-password)
 * and hash/query fallback navigation for SPAs and Supabase recovery flows.
 */

export function parseRecoveryParams(loc) {
  const target = loc || (typeof window !== 'undefined' ? window.location : null);
  if (!target) {
    return {
      isRecovery: false,
      hasError: false,
      error: null,
      errorCode: null,
      errorDescription: null,
      tokenHash: null,
      code: null,
      type: null,
    };
  }

  const hash = target.hash || '';
  const search = target.search || '';

  // Extract from search parameters
  const searchParams = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);

  // Extract from hash parameters (handles both standard #access_token=... and hash router #/reset-password?...)
  const hashClean = hash.replace(/^#\/?/, '');
  const hashQueryIdx = hashClean.indexOf('?');
  const hashToParse = hashQueryIdx >= 0 ? hashClean.slice(hashQueryIdx + 1) : hashClean;
  const hashParams = new URLSearchParams(hashToParse);

  const error = searchParams.get('error') || hashParams.get('error');
  const errorCode = searchParams.get('error_code') || hashParams.get('error_code');
  const errorDescription = searchParams.get('error_description') || hashParams.get('error_description');

  const type = searchParams.get('type') || hashParams.get('type');
  const code = searchParams.get('code') || hashParams.get('code');
  const tokenHash =
    searchParams.get('token_hash') ||
    searchParams.get('token') ||
    hashParams.get('token_hash') ||
    hashParams.get('token');

  const hasAccessToken = hash.includes('access_token=') || search.includes('access_token=');
  const hasTypeRecovery = type === 'recovery' || hash.includes('type=recovery') || search.includes('type=recovery');

  const isRecovery = Boolean(hasTypeRecovery || tokenHash || code || hasAccessToken || error || errorCode);

  return {
    isRecovery,
    hasError: Boolean(error || errorCode),
    error: error || null,
    errorCode: errorCode || null,
    errorDescription: errorDescription ? decodeURIComponent(errorDescription.replace(/\+/g, ' ')) : null,
    tokenHash: tokenHash || null,
    code: code || null,
    type: type || null,
  };
}

let initialRecoveryParams = null;

export function getInitialRecoveryParams() {
  if (!initialRecoveryParams && typeof window !== 'undefined') {
    initialRecoveryParams = parseRecoveryParams(window.location);
  }
  return initialRecoveryParams || {
    isRecovery: false,
    hasError: false,
    error: null,
    errorCode: null,
    errorDescription: null,
    tokenHash: null,
    code: null,
    type: null,
  };
}

export function getRouteFromUrl(loc) {
  const target = loc || (typeof window !== 'undefined' ? window.location : null);
  if (!target) return 'app';

  const pathname = (target.pathname || '').toLowerCase().replace(/\/+$/, '');
  const hash = (target.hash || '').toLowerCase().replace(/^#\/?/, '').replace(/\/+$/, '');

  if (pathname === '/privacy-policy' || pathname === '/privacy' || hash === 'privacy-policy' || hash === 'privacy') {
    return 'privacy-policy';
  }
  if (pathname === '/terms' || pathname === '/terms-of-service' || hash === 'terms' || hash === 'terms-of-service') {
    return 'terms';
  }

  const isOAuthPending =
    typeof window !== 'undefined' &&
    window.sessionStorage &&
    Boolean(window.sessionStorage.getItem('oauth_in_progress'));

  const recoveryParams = parseRecoveryParams(target);
  if (!isOAuthPending) {
    if (
      pathname === '/reset-password' ||
      hash === 'reset-password' ||
      hash.startsWith('reset-password') ||
      recoveryParams.isRecovery ||
      getInitialRecoveryParams().isRecovery
    ) {
      return 'reset-password';
    }
  } else if (pathname === '/reset-password' || hash === 'reset-password' || hash.startsWith('reset-password')) {
    return 'reset-password';
  }
  return 'app';
}

export function getRoutePath(route) {
  if (route === 'privacy-policy') return '/privacy-policy';
  if (route === 'terms') return '/terms';
  if (route === 'reset-password') return '/reset-password';
  return '/';
}

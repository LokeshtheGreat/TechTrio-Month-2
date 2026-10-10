/**
 * Routing helpers for Email Spam Shield.
 * Supports standard pathname navigation (/privacy-policy, /terms)
 * and hash fallback navigation (#/privacy-policy, #/terms)
 * for SPAs without extra router dependencies.
 */

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
  return 'app';
}

export function getRoutePath(route) {
  if (route === 'privacy-policy') return '/privacy-policy';
  if (route === 'terms') return '/terms';
  return '/';
}

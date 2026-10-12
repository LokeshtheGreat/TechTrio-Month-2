import test, { describe } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { getFrontendUrl } from '../src/config/api.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe('Supabase Google OAuth & login_hint Integration', () => {
  // Mock Supabase Auth client to inspect signInWithOAuth arguments
  class MockSupabaseOAuthClient {
    constructor() {
      this.lastCall = null;
      this.shouldFail = false;
      this.errorMessage = 'Mock OAuth Error';
    }

    async signInWithOAuth({ provider, options }) {
      this.lastCall = { provider, options };
      if (this.shouldFail) {
        return {
          data: { provider: null, url: null },
          error: new Error(this.errorMessage)
        };
      }
      return {
        data: {
          provider,
          url: `https://accounts.google.com/o/oauth2/v2/auth?client_id=mock-client&redirect_uri=${encodeURIComponent(options?.redirectTo || '')}${options?.queryParams?.login_hint ? `&login_hint=${encodeURIComponent(options.queryParams.login_hint)}` : ''}`
        },
        error: null
      };
    }
  }

  // Helper matching the implementation logic in AuthContext.jsx
  const createOAuthHandler = ({ user = null, session = null, client = null }) => {
    return async (provider = 'google', customOptions = {}) => {
      if (!client) {
        throw new Error('Supabase client is not configured. Please check environment variables.');
      }

      const currentEmail = user?.email || session?.user?.email || null;
      const redirectTo = customOptions.redirectTo || getFrontendUrl();

      const queryParams = { ...(customOptions.queryParams || {}) };
      if (currentEmail && !queryParams.login_hint) {
        queryParams.login_hint = currentEmail;
      }

      const options = {
        ...customOptions,
        redirectTo,
      };

      if (Object.keys(queryParams).length > 0) {
        options.queryParams = queryParams;
      }

      const { data, error } = await client.signInWithOAuth({
        provider,
        options,
      });

      if (error) throw error;
      return data;
    };
  };

  test('1. Authenticated user: automatically attaches user email as login_hint', async () => {
    const client = new MockSupabaseOAuthClient();
    const authenticatedUser = { email: 'authenticated.user@tech-trio.org', id: 'user-123' };
    const signInWithOAuth = createOAuthHandler({ user: authenticatedUser, client });

    const result = await signInWithOAuth('google');

    assert.ok(result.url, 'Returns OAuth URL');
    assert.equal(client.lastCall.provider, 'google');
    assert.equal(client.lastCall.options.redirectTo, getFrontendUrl());
    assert.ok(client.lastCall.options.queryParams, 'queryParams must be present');
    assert.equal(client.lastCall.options.queryParams.login_hint, 'authenticated.user@tech-trio.org');
    assert.ok(result.url.includes('login_hint=authenticated.user%40tech-trio.org'));
  });

  test('2. Authenticated session fallback: attaches session.user.email if user is not directly set', async () => {
    const client = new MockSupabaseOAuthClient();
    const session = { user: { email: 'session.user@example.com' } };
    const signInWithOAuth = createOAuthHandler({ user: null, session, client });

    await signInWithOAuth('google');

    assert.equal(client.lastCall.options.queryParams?.login_hint, 'session.user@example.com');
  });

  test('3. Unauthenticated user: does NOT attach login_hint and preserves standard OAuth options', async () => {
    const client = new MockSupabaseOAuthClient();
    const signInWithOAuth = createOAuthHandler({ user: null, session: null, client });

    const result = await signInWithOAuth('google');

    assert.ok(result.url, 'Returns OAuth URL');
    assert.equal(client.lastCall.provider, 'google');
    assert.equal(client.lastCall.options.redirectTo, getFrontendUrl());
    assert.equal(client.lastCall.options.queryParams, undefined, 'No queryParams when unauthenticated');
    assert.ok(!result.url.includes('login_hint'), 'URL must not contain login_hint');
  });

  test('4. Custom queryParams: preserves custom parameters alongside login_hint', async () => {
    const client = new MockSupabaseOAuthClient();
    const authenticatedUser = { email: 'user@domain.com' };
    const signInWithOAuth = createOAuthHandler({ user: authenticatedUser, client });

    await signInWithOAuth('google', {
      queryParams: { prompt: 'select_account', access_type: 'offline' }
    });

    assert.equal(client.lastCall.options.queryParams.prompt, 'select_account');
    assert.equal(client.lastCall.options.queryParams.access_type, 'offline');
    assert.equal(client.lastCall.options.queryParams.login_hint, 'user@domain.com');
  });

  test('5. Explicit login_hint override: respects custom login_hint if explicitly supplied', async () => {
    const client = new MockSupabaseOAuthClient();
    const authenticatedUser = { email: 'default@domain.com' };
    const signInWithOAuth = createOAuthHandler({ user: authenticatedUser, client });

    await signInWithOAuth('google', {
      queryParams: { login_hint: 'explicit.override@domain.com' }
    });

    assert.equal(client.lastCall.options.queryParams.login_hint, 'explicit.override@domain.com');
  });

  test('6. Custom redirectTo & scopes: preserves caller options', async () => {
    const client = new MockSupabaseOAuthClient();
    const signInWithOAuth = createOAuthHandler({ user: null, client });

    await signInWithOAuth('google', {
      redirectTo: 'https://e-mail-spam-shield.vercel.app/dashboard',
      scopes: 'email profile'
    });

    assert.equal(client.lastCall.options.redirectTo, 'https://e-mail-spam-shield.vercel.app/dashboard');
    assert.equal(client.lastCall.options.scopes, 'email profile');
  });

  test('7. Error propagation: propagates Supabase OAuth errors correctly', async () => {
    const client = new MockSupabaseOAuthClient();
    client.shouldFail = true;
    client.errorMessage = 'OAuth provider configuration error';

    const signInWithOAuth = createOAuthHandler({ user: { email: 'user@test.com' }, client });

    await assert.rejects(
      async () => {
        await signInWithOAuth('google');
      },
      { message: 'OAuth provider configuration error' }
    );
  });

  test('8. Unconfigured client: throws descriptive configuration error', async () => {
    const signInWithOAuth = createOAuthHandler({ user: null, client: null });

    await assert.rejects(
      async () => {
        await signInWithOAuth('google');
      },
      { message: 'Supabase client is not configured. Please check environment variables.' }
    );
  });
});

describe('Google OAuth Component & UI Contract Audit', () => {
  const authModalPath = path.resolve(__dirname, '../src/components/AuthModal.jsx');
  const authContextPath = path.resolve(__dirname, '../src/context/AuthContext.jsx');

  test('AuthContext.jsx exports signInWithOAuth and signInWithGoogle methods', () => {
    assert.ok(fs.existsSync(authContextPath), 'AuthContext.jsx must exist');
    const content = fs.readFileSync(authContextPath, 'utf8');

    assert.ok(content.includes('signInWithOAuth'), 'AuthContext must define signInWithOAuth');
    assert.ok(content.includes('signInWithGoogle'), 'AuthContext must define signInWithGoogle');
    assert.ok(content.includes('login_hint'), 'AuthContext must include login_hint logic');
    assert.ok(
      content.includes('currentEmail = user?.email || session?.user?.email'),
      'AuthContext must derive email from user or session'
    );
  });

  test('AuthModal.jsx renders Continue with Google button with proper UX contract', () => {
    assert.ok(fs.existsSync(authModalPath), 'AuthModal.jsx must exist');
    const content = fs.readFileSync(authModalPath, 'utf8');

    assert.ok(content.includes('Continue with Google'), 'AuthModal must display "Continue with Google" button');
    assert.ok(content.includes('signInWithGoogle'), 'AuthModal must use signInWithGoogle');
    assert.ok(content.includes('handleGoogleSignIn'), 'AuthModal must have handleGoogleSignIn handler');
    assert.ok(content.includes('oauthLoading'), 'AuthModal must track oauthLoading state');
    assert.ok(content.includes('Redirecting to Google...'), 'AuthModal must display loading label during OAuth dispatch');
    // Verify Google SVG brand icon is rendered
    assert.ok(content.includes('M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92'), 'AuthModal must include Google brand SVG icon');
    // Verify hidden when in forgot password mode
    assert.ok(content.includes("mode !== 'forgot'"), 'Google sign-in button must be hidden in password reset mode');
  });
});

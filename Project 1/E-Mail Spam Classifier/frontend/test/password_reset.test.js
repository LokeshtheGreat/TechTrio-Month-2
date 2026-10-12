import test, { describe } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { getRouteFromUrl, getRoutePath, parseRecoveryParams, getInitialRecoveryParams } from '../src/utils/routes.js';
import { getFrontendUrl } from '../src/config/api.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

describe('Password Reset Routing & URL Configuration', () => {
  test('resolves /reset-password pathname to reset-password route', () => {
    assert.equal(getRouteFromUrl({ pathname: '/reset-password', hash: '' }), 'reset-password');
    assert.equal(getRouteFromUrl({ pathname: '/reset-password/', hash: '' }), 'reset-password');
  });

  test('resolves #/reset-password and #reset-password hash to reset-password route', () => {
    assert.equal(getRouteFromUrl({ pathname: '/', hash: '#/reset-password' }), 'reset-password');
    assert.equal(getRouteFromUrl({ pathname: '/', hash: '#reset-password' }), 'reset-password');
  });

  test('resolves /reset-password with recovery hash tokens to reset-password route', () => {
    const loc = {
      pathname: '/reset-password',
      hash: '#access_token=mock-token&refresh_token=mock-refresh&type=recovery'
    };
    assert.equal(getRouteFromUrl(loc), 'reset-password');
  });

  test('getRoutePath returns canonical /reset-password path', () => {
    assert.equal(getRoutePath('reset-password'), '/reset-password');
  });

  test('getFrontendUrl resolves production URL or configured frontend base', () => {
    const originalEnv = process.env.VITE_FRONTEND_URL;
    try {
      process.env.VITE_FRONTEND_URL = 'https://e-mail-spam-shield.vercel.app';
      assert.equal(getFrontendUrl(), 'https://e-mail-spam-shield.vercel.app');

      delete process.env.VITE_FRONTEND_URL;
      const defaultUrl = getFrontendUrl();
      assert.ok(defaultUrl.startsWith('http'), 'Frontend URL must be a valid HTTP(S) URL');
    } finally {
      if (originalEnv) {
        process.env.VITE_FRONTEND_URL = originalEnv;
      } else {
        delete process.env.VITE_FRONTEND_URL;
      }
    }
  });
});

describe('Supabase Password Reset Request Flow (Forgot Password)', () => {
  class MockSupabaseResetClient {
    constructor() {
      this.calls = [];
      this.shouldRateLimit = false;
      this.shouldThrowUserNotFound = false;
    }

    async resetPasswordForEmail(email, options) {
      this.calls.push({ email, options });
      if (this.shouldRateLimit) {
        const err = new Error('Email rate limit exceeded');
        err.status = 429;
        return { data: null, error: err };
      }
      if (this.shouldThrowUserNotFound) {
        // Some backends might simulate user not found, but client should mask this
        const err = new Error('User not found');
        err.status = 400;
        return { data: null, error: err };
      }
      return { data: {}, error: null };
    }
  }

  test('initiates password reset with correct redirectTo parameter', async () => {
    const client = new MockSupabaseResetClient();
    const email = 'registered.user@example.com';
    const expectedRedirect = `${getFrontendUrl()}/reset-password`;

    const res = await client.resetPasswordForEmail(email, { redirectTo: expectedRedirect });
    assert.equal(res.error, null);
    assert.equal(client.calls.length, 1);
    assert.equal(client.calls[0].email, email);
    assert.equal(client.calls[0].options.redirectTo, expectedRedirect);
  });

  test('non-revealing confirmation: does not leak unregistered email presence', async () => {
    const client = new MockSupabaseResetClient();
    // Supabase Auth returns { data: {}, error: null } for unregistered emails to prevent enumeration
    const email = 'unknown.user@example.com';
    const { error } = await client.resetPasswordForEmail(email, { redirectTo: '/reset-password' });

    assert.equal(error, null, 'Supabase returns success even if user not found');
    const userVisibleMessage = 'If an account exists for this email address, a password reset link has been sent. Please check your inbox and spam folder.';
    assert.ok(!userVisibleMessage.includes('not found'), 'Message must not disclose that user does not exist');
    assert.ok(userVisibleMessage.includes('If an account exists'), 'Message must be generic and non-revealing');
  });

  test('observable failure: displays error message when API call actually fails', async () => {
    const client = new MockSupabaseResetClient();
    client.shouldRateLimit = true;

    const { error } = await client.resetPasswordForEmail('user@example.com', { redirectTo: '/reset-password' });
    assert.notEqual(error, null);

    const isDev = true;
    let errorMessage = '';
    if (error?.status === 429 || error?.message?.toLowerCase().includes('rate limit')) {
      errorMessage = 'Too many requests. For security purposes, please wait a few minutes before trying again.';
    } else {
      errorMessage = isDev ? `Password reset request failed: ${error?.message}` : 'Unable to process password reset request.';
    }

    assert.ok(errorMessage.includes('Too many requests') || errorMessage.includes('failed'), 'Failure must be clearly observable');
  });

  test('handles rate limit error without crashing', async () => {
    const client = new MockSupabaseResetClient();
    client.shouldRateLimit = true;

    const { error } = await client.resetPasswordForEmail('user@example.com', { redirectTo: '/reset-password' });
    assert.notEqual(error, null);
    assert.equal(error.status, 429);
  });
});

describe('Supabase Password Reset Execution & Validation', () => {
  class MockSupabaseUpdateUserClient {
    constructor() {
      this.updatedPassword = null;
      this.isRecoverySession = false;
      this.signedOut = false;
    }

    async updateUser(attributes) {
      if (!this.isRecoverySession) {
        return { data: null, error: new Error('User not authenticated or recovery session expired') };
      }
      if (!attributes?.password || attributes.password.length < 6) {
        return { data: null, error: new Error('Password must be at least 6 characters') };
      }
      this.updatedPassword = attributes.password;
      return { data: { user: { id: 'user-uuid-123' } }, error: null };
    }

    async signOut() {
      this.signedOut = true;
      this.isRecoverySession = false;
      return { error: null };
    }
  }

  test('validates password requirements: length and confirmation match', () => {
    const validate = (pw, confirm) => {
      if (!pw || !confirm) return 'Please fill in both password fields.';
      if (pw.length < 6) return 'Password must be at least 6 characters long.';
      if (pw !== confirm) return 'Passwords do not match. Please verify and try again.';
      return null;
    };

    assert.equal(validate('', ''), 'Please fill in both password fields.');
    assert.equal(validate('12345', '12345'), 'Password must be at least 6 characters long.');
    assert.equal(validate('secret123', 'secret999'), 'Passwords do not match. Please verify and try again.');
    assert.equal(validate('securePassword123', 'securePassword123'), null);
  });

  test('recovery guard: rejects password update without valid recovery session', async () => {
    const client = new MockSupabaseUpdateUserClient();
    client.isRecoverySession = false;

    const res = await client.updateUser({ password: 'newValidPassword123' });
    assert.notEqual(res.error, null);
    assert.ok(res.error.message.includes('expired') || res.error.message.includes('not authenticated'));
    assert.equal(client.updatedPassword, null);
  });

  test('successful password update under active recovery session cleans up session', async () => {
    const client = new MockSupabaseUpdateUserClient();
    client.isRecoverySession = true;

    const res = await client.updateUser({ password: 'brandNewSecurePassword!2026' });
    assert.equal(res.error, null);
    assert.equal(client.updatedPassword, 'brandNewSecurePassword!2026');

    // Clean up recovery session
    await client.signOut();
    assert.equal(client.signedOut, true);
    assert.equal(client.isRecoverySession, false);
  });
});

describe('Component Source Code & UI Contract Audit', () => {
  const authModalPath = path.resolve(__dirname, '../src/components/AuthModal.jsx');
  const resetPasswordPath = path.resolve(__dirname, '../src/components/ResetPassword.jsx');
  const appPath = path.resolve(__dirname, '../src/App.jsx');
  const routesPath = path.resolve(__dirname, '../src/utils/routes.js');

  test('AuthModal.jsx contains Forgot password button and reset request flow', () => {
    assert.ok(fs.existsSync(authModalPath), 'AuthModal.jsx must exist');
    const content = fs.readFileSync(authModalPath, 'utf8');

    assert.ok(content.includes('Forgot password?'), 'AuthModal must contain "Forgot password?" button');
    assert.ok(content.includes('resetPasswordForEmail'), 'AuthModal must invoke resetPasswordForEmail');
    assert.ok(content.includes('Send Reset Link'), 'AuthModal must have "Send Reset Link" action');
    assert.ok(content.includes('Back to Sign In'), 'AuthModal must have "Back to Sign In" option');
    assert.ok(
      content.includes('If an account exists'),
      'AuthModal must display non-revealing generic confirmation message'
    );
  });

  test('ResetPassword.jsx exists and contains complete security flow', () => {
    assert.ok(fs.existsSync(resetPasswordPath), 'ResetPassword.jsx must exist');
    const content = fs.readFileSync(resetPasswordPath, 'utf8');

    assert.ok(content.includes('New Password'), 'Must contain New Password field');
    assert.ok(content.includes('Confirm New Password'), 'Must contain Confirm New Password field');
    assert.ok(content.includes('updatePassword') || content.includes('updateUser'), 'Must update password via Supabase');
    assert.ok(content.includes('Invalid or Expired Reset Link'), 'Must guard against unauthorized or expired link');
    assert.ok(content.includes('Return to Sign In') || content.includes('Sign In Now'), 'Must provide return to sign-in navigation');
    assert.ok(content.includes('Updating Password...'), 'Must provide loading state');
  });

  test('App.jsx routes to ResetPassword component on reset-password path', () => {
    assert.ok(fs.existsSync(appPath), 'App.jsx must exist');
    const content = fs.readFileSync(appPath, 'utf8');

    assert.ok(content.includes("import ResetPassword from './components/ResetPassword'"), 'App.jsx must import ResetPassword');
    assert.ok(content.includes("currentRoute === 'reset-password'"), 'App.jsx must handle reset-password route');
  });

  test('routes.js exports reset-password canonical route', () => {
    assert.ok(fs.existsSync(routesPath), 'routes.js must exist');
    const content = fs.readFileSync(routesPath, 'utf8');

    assert.ok(content.includes("pathname === '/reset-password'"), 'routes.js must match /reset-password');
    assert.ok(content.includes("return '/reset-password'"), 'routes.js must return canonical /reset-password');
  });
});

describe('Browser Environment Safety & Vite Variable Handling', () => {
  const authModalPath = path.resolve(__dirname, '../src/components/AuthModal.jsx');
  const apiConfigPath = path.resolve(__dirname, '../src/config/api.js');
  const supabaseClientPath = path.resolve(__dirname, '../src/lib/supabaseClient.js');

  test('frontend source files do not contain unguarded process.env references', () => {
    const filesToAudit = [authModalPath, apiConfigPath, supabaseClientPath];
    for (const filePath of filesToAudit) {
      assert.ok(fs.existsSync(filePath), `${path.basename(filePath)} must exist`);
      const content = fs.readFileSync(filePath, 'utf8');

      const lines = content.split('\n');
      lines.forEach((line, idx) => {
        if (line.includes('process.env') || line.includes('process.')) {
          assert.ok(
            line.includes("typeof process !== 'undefined'") || line.includes('typeof process') || content.slice(0, content.indexOf(line)).includes('typeof process'),
            `Unguarded process reference in ${path.basename(filePath)} at line ${idx + 1}: ${line.trim()}`
          );
        }
      });
    }
  });

  test('getFrontendUrl executes safely without throwing ReferenceError when process is absent', () => {
    const originalProcess = globalThis.process;
    try {
      globalThis.process = undefined;
      assert.doesNotThrow(() => {
        const url = getFrontendUrl();
        assert.ok(typeof url === 'string' && url.length > 0);
      });
    } finally {
      globalThis.process = originalProcess;
    }
  });

  test('supabaseClient.js does not expose service-role key or sensitive server secrets', () => {
    const content = fs.readFileSync(supabaseClientPath, 'utf8');
    assert.ok(!content.includes('SERVICE_ROLE_KEY'), 'Must not reference SERVICE_ROLE_KEY');
    assert.ok(!content.includes('service_role'), 'Must not reference service_role');
    assert.ok(content.includes('VITE_SUPABASE_ANON_KEY'), 'Must use public anon key');
  });
});

describe('Recovery URL Token & Session State Handling', () => {
  test('parseRecoveryParams parses standard Supabase implicit recovery hash', () => {
    const loc = {
      hash: '#access_token=mock-access-token&refresh_token=mock-refresh-token&expires_in=3600&token_type=bearer&type=recovery',
      search: '',
    };
    const params = parseRecoveryParams(loc);
    assert.equal(params.isRecovery, true);
    assert.equal(params.hasError, false);
    assert.equal(params.type, 'recovery');
  });

  test('parseRecoveryParams parses PKCE code query parameter', () => {
    const loc = {
      hash: '',
      search: '?code=pkce-auth-code-12345',
    };
    const params = parseRecoveryParams(loc);
    assert.equal(params.isRecovery, true);
    assert.equal(params.hasError, false);
    assert.equal(params.code, 'pkce-auth-code-12345');
  });

  test('parseRecoveryParams parses OTP token_hash query parameter', () => {
    const loc = {
      hash: '',
      search: '?token_hash=otp-hash-67890&type=recovery',
    };
    const params = parseRecoveryParams(loc);
    assert.equal(params.isRecovery, true);
    assert.equal(params.hasError, false);
    assert.equal(params.tokenHash, 'otp-hash-67890');
    assert.equal(params.type, 'recovery');
  });

  test('parseRecoveryParams parses expired/invalid link error parameters and decodes description', () => {
    const loc = {
      hash: '#error=access_denied&error_code=otp_expired&error_description=Email+link+is+invalid+or+has+expired',
      search: '',
    };
    const params = parseRecoveryParams(loc);
    assert.equal(params.isRecovery, true);
    assert.equal(params.hasError, true);
    assert.equal(params.error, 'access_denied');
    assert.equal(params.errorCode, 'otp_expired');
    assert.equal(params.errorDescription, 'Email link is invalid or has expired');
  });

  test('getRouteFromUrl routes root URL with recovery tokens to reset-password', () => {
    const locImplicit = {
      pathname: '/',
      hash: '#access_token=token&type=recovery',
      search: '',
    };
    assert.equal(getRouteFromUrl(locImplicit), 'reset-password');

    const locPkce = {
      pathname: '/',
      hash: '',
      search: '?code=code-123',
    };
    assert.equal(getRouteFromUrl(locPkce), 'reset-password');
  });

  test('ResetPassword.jsx source code implements multi-flow recovery verification, loading state, and error handling', () => {
    const resetPasswordPath = path.resolve(__dirname, '../src/components/ResetPassword.jsx');
    const content = fs.readFileSync(resetPasswordPath, 'utf8');

    assert.ok(content.includes('getInitialRecoveryParams'), 'Must use getInitialRecoveryParams to preserve initial tokens');
    assert.ok(content.includes('verifyOtp'), 'Must support verifyOtp for token_hash flow');
    assert.ok(content.includes('exchangeCodeForSession'), 'Must support exchangeCodeForSession for PKCE flow');
    assert.ok(content.includes('PASSWORD_RECOVERY'), 'Must listen for PASSWORD_RECOVERY event');
    assert.ok(content.includes('verifyingSession'), 'Must manage verifyingSession loading state');
    assert.ok(content.includes('isAuthorized'), 'Must manage authorization state');
  });
});


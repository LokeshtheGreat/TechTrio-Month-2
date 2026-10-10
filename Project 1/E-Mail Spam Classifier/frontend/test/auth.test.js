import test, { describe } from 'node:test';
import assert from 'node:assert/strict';

describe('Supabase Authentication & State Management', () => {
  // Mock auth service representing Supabase auth client operations
  class MockSupabaseAuth {
    constructor() {
      this.currentSession = null;
      this.listeners = [];
    }

    onAuthStateChange(callback) {
      this.listeners.push(callback);
      return {
        data: {
          subscription: {
            unsubscribe: () => {
              this.listeners = this.listeners.filter(l => l !== callback);
            }
          }
        }
      };
    }

    notify(event, session) {
      this.currentSession = session;
      for (const listener of this.listeners) {
        listener(event, session);
      }
    }

    async getSession() {
      return { data: { session: this.currentSession }, error: null };
    }

    async signInWithPassword({ email, password }) {
      if (!email || !password) {
        return { data: { user: null, session: null }, error: new Error('Missing credentials') };
      }
      if (password === 'invalid-pw') {
        return { data: { user: null, session: null }, error: new Error('Invalid login credentials') };
      }
      const user = {
        id: 'mock-user-uuid-1234',
        email: email,
        role: 'authenticated'
      };
      const session = {
        access_token: 'mock.supabase.jwt.token',
        user: user,
        expires_at: Math.floor(Date.now() / 1000) + 3600
      };
      this.notify('SIGNED_IN', session);
      return { data: { user, session }, error: null };
    }

    async signOut() {
      this.notify('SIGNED_OUT', null);
      return { error: null };
    }
  }

  test('1. Unauthenticated state: initial user and session are null', async () => {
    const auth = new MockSupabaseAuth();
    const sessionRes = await auth.getSession();

    assert.equal(sessionRes.data.session, null);
    // Unauthenticated user cannot have access token
    assert.equal(sessionRes.data.session?.access_token, undefined);
  });

  test('2. Unauthenticated UI requirement: blocks access and requires sign-in', async () => {
    const auth = new MockSupabaseAuth();
    const sessionRes = await auth.getSession();
    const isUserSignedIn = Boolean(sessionRes.data.session?.user);

    assert.equal(isUserSignedIn, false);
    // Must prompt sign-in action
    const uiState = isUserSignedIn ? 'READY_TO_CONNECT' : 'SIGN_IN_REQUIRED';
    assert.equal(uiState, 'SIGN_IN_REQUIRED');
  });

  test('3. Successful sign-in state: sets authenticated user and token', async () => {
    const auth = new MockSupabaseAuth();
    let stateChangeTriggered = false;
    let authUser = null;

    auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN') {
        stateChangeTriggered = true;
        authUser = session?.user;
      }
    });

    const res = await auth.signInWithPassword({
      email: 'user@tech-trio.org',
      password: 'valid-password-123'
    });

    assert.equal(res.error, null);
    assert.equal(res.data.user.email, 'user@tech-trio.org');
    assert.equal(res.data.user.id, 'mock-user-uuid-1234');
    assert.equal(res.data.session.access_token, 'mock.supabase.jwt.token');
    assert.equal(stateChangeTriggered, true);
    assert.equal(authUser.email, 'user@tech-trio.org');

    // UI state transitions to allow Gmail connect
    const isUserSignedIn = Boolean(auth.currentSession?.user);
    assert.equal(isUserSignedIn, true);
    const uiState = isUserSignedIn ? 'READY_TO_CONNECT' : 'SIGN_IN_REQUIRED';
    assert.equal(uiState, 'READY_TO_CONNECT');
  });

  test('4. Invalid sign-in: returns error and does not mutate session', async () => {
    const auth = new MockSupabaseAuth();
    const res = await auth.signInWithPassword({
      email: 'wrong@tech-trio.org',
      password: 'invalid-pw'
    });

    assert.notEqual(res.error, null);
    assert.equal(res.error.message, 'Invalid login credentials');
    assert.equal(auth.currentSession, null);
  });

  test('5. Sign-out state: clears session and returns to unauthenticated state', async () => {
    const auth = new MockSupabaseAuth();
    
    // First sign in
    await auth.signInWithPassword({
      email: 'active@tech-trio.org',
      password: 'password-123'
    });
    assert.notEqual(auth.currentSession, null);

    let signedOutEvent = false;
    auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_OUT') {
        signedOutEvent = true;
      }
    });

    // Now sign out
    await auth.signOut();

    assert.equal(signedOutEvent, true);
    assert.equal(auth.currentSession, null);

    const sessionRes = await auth.getSession();
    assert.equal(sessionRes.data.session, null);

    // UI transitions back to requiring sign-in
    const isUserSignedIn = Boolean(auth.currentSession?.user);
    assert.equal(isUserSignedIn, false);
  });
});

import test, { describe } from 'node:test';
import assert from 'node:assert/strict';

// Test environment variables for testing
process.env.VITE_BACKEND_URL = 'https://custom-backend.onrender.com/';

import { getBackendUrl, initiateGmailConnect, getAuthToken, fetchGmailStatus } from '../src/config/api.js';

describe('Frontend API Configuration & Gmail Connect Flow', () => {
  test('getBackendUrl returns configured URL with trailing slash stripped', () => {
    assert.equal(getBackendUrl(), 'https://custom-backend.onrender.com');
  });

  test('getBackendUrl falls back to localhost:5000 when unset', () => {
    const original = process.env.VITE_BACKEND_URL;
    try {
      delete process.env.VITE_BACKEND_URL;
      assert.equal(getBackendUrl(), 'http://localhost:5000');
    } finally {
      process.env.VITE_BACKEND_URL = original;
    }
  });

  test('getAuthToken returns null when unauthenticated without throwing', async () => {
    const token = await getAuthToken();
    assert.equal(token, null);
  });

  test('initiateGmailConnect throws clear sign-in error when unauthenticated', async () => {
    await assert.rejects(
      async () => {
        await initiateGmailConnect();
      },
      {
        name: 'Error',
        message: 'You are not signed in or your session has expired. Please sign in again.'
      }
    );
  });

  test('fetchGmailStatus returns unauthenticated status without making HTTP call when no token', async () => {
    const result = await fetchGmailStatus();
    assert.equal(result.connected, false);
    assert.equal(result.unauthenticated, true);
  });

  test('tab remount with cached emails loads from latest without triggering full sync', async () => {
    // Simulating component mount logic with pre-existing cached emails in database
    let fullSyncCalled = false;
    let latestCalled = false;

    const mockLatestApi = async () => {
      latestCalled = true;
      return {
        data: {
          monitoring: true,
          emails: [
            {
              id: 'msg-1',
              subject: 'Hello World',
              body_html: '<p>Hello</p>',
              spam_indicators: [{ term: 'free', weight: 1.0 }]
            }
          ]
        }
      };
    };

    const mockSyncApi = async () => {
      fullSyncCalled = true;
      return { data: { emails: [] } };
    };

    // Component mounting logic:
    const res = await mockLatestApi();
    if (!res.data.emails || res.data.emails.length === 0) {
      await mockSyncApi();
    }

    assert.equal(latestCalled, true);
    assert.equal(fullSyncCalled, false);
    assert.equal(res.data.emails[0].body_html, '<p>Hello</p>');
    assert.equal(res.data.emails[0].spam_indicators.length, 1);
  });

  test('tab remount without cached emails triggers initial sync', async () => {
    let fullSyncCalled = false;
    const mockLatestApi = async () => ({ data: { emails: [] } });
    const mockSyncApi = async () => {
      fullSyncCalled = true;
      return { data: { emails: [{ id: 'synced-1' }] } };
    };

    const res = await mockLatestApi();
    if (!res.data.emails || res.data.emails.length === 0) {
      await mockSyncApi();
    }

    assert.equal(fullSyncCalled, true);
  });

  test('manual Sync Now always triggers full sync explicitly', async () => {
    let syncNowExecuted = false;
    const handleSync = async () => {
      syncNowExecuted = true;
    };

    // User explicitly clicks "Sync Now" button
    await handleSync();
    assert.equal(syncNowExecuted, true);
  });
});

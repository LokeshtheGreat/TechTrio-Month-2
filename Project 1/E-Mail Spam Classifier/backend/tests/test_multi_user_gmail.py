import os
import sys
import uuid
import time
import json
import pytest
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
import jwt

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, get_user_gmail_service, ensure_user_exists
from models import User, GmailConnection, ClassifiedEmail
from services.gmail_service import GmailService
from utils.encryption import encrypt_credentials, decrypt_credentials, generate_oauth_state

TEST_ENCRYPTION_KEY = Fernet.generate_key().decode('utf-8')
TEST_JWT_SECRET = "super-secret-test-supabase-jwt-key-32chars"


def make_auth_token(user_id=None, email="user@example.com"):
    uid = user_id or str(uuid.uuid4())
    payload = {
        'sub': uid,
        'email': email,
        'aud': 'authenticated',
        'role': 'authenticated',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time())
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm='HS256'), uid


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv('TOKEN_ENCRYPTION_KEY', TEST_ENCRYPTION_KEY)
    monkeypatch.setenv('SUPABASE_JWT_SECRET', TEST_JWT_SECRET)
    monkeypatch.setenv('BACKEND_URL', 'https://spam-shield-api.onrender.com')
    monkeypatch.setenv('FRONTEND_URL', 'https://spam-shield.vercel.app')


def test_gmail_endpoints_require_authentication():
    """Verify that unauthenticated requests to user-scoped endpoints return HTTP 401."""
    with app.test_client() as client:
        assert client.get('/api/gmail/status').status_code == 401
        assert client.get('/api/gmail/connect').status_code == 401
        assert client.post('/api/gmail/sync').status_code == 401
        assert client.post('/api/gmail/disconnect').status_code == 401
        assert client.post('/api/gmail/watch').status_code == 401
        assert client.get('/api/gmail/latest').status_code == 401


def test_oauth_state_validation_missing_and_tampered():
    """Verify that missing, tampered, or invalid state in callback returns HTTP 400."""
    with app.test_client() as client:
        # Missing code and state
        res1 = client.get('/api/gmail/callback')
        assert res1.status_code == 400

        # Tampered state
        res2 = client.get('/api/gmail/callback?code=fake-code&state=not-a-valid-fernet-token')
        assert res2.status_code == 400
        assert "error" in res2.get_json()


def test_oauth_state_session_mismatch_rejected():
    """Verify that if session['oauth_state'] differs from query state, callback is rejected."""
    user_id = str(uuid.uuid4())
    state_a = generate_oauth_state(user_id=user_id, csrf_nonce='csrf-a')
    state_b = generate_oauth_state(user_id=user_id, csrf_nonce='csrf-b')

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['oauth_state'] = state_a

        res = client.get(f'/api/gmail/callback?code=mock_code&state={state_b}')
        assert res.status_code == 400
        assert "Invalid or mismatched OAuth state" in res.get_json()['error']


def test_oauth_callback_binds_initiating_user_and_persists_credentials():
    """Verify callback uses user_id cryptographically embedded in state, not client input."""
    user_id = str(uuid.uuid4())
    state = generate_oauth_state(user_id=user_id, csrf_nonce='csrf-token', code_verifier='verifier-123')

    mock_tokens = {
        'token': 'initial-access-token',
        'refresh_token': 'test-refresh-token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'test-client-id',
        'client_secret': 'test-client-secret',
        'scopes': ['https://www.googleapis.com/auth/gmail.readonly']
    }

    with patch.object(GmailService, 'exchange_code', return_value=mock_tokens) as mock_exchange, \
         patch.object(GmailService, 'get_profile', return_value='testuser@gmail.com'):

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['oauth_state'] = state
                sess['oauth_csrf'] = 'csrf-token'
                sess['oauth_user_id'] = user_id

            res = client.get(f'/api/gmail/callback?code=auth-code-xyz&state={state}')
            assert res.status_code == 302
            assert 'gmail_connected=true' in res.location

            mock_exchange.assert_called_once_with(
                'auth-code-xyz',
                'https://spam-shield-api.onrender.com/api/gmail/callback',
                state=state,
                code_verifier='verifier-123'
            )


def test_multi_user_isolation_user_a_and_user_b():
    """
    Verify complete isolation between two users:
    - User A connects Gmail
    - User B checks status -> Not connected
    - User B attempts sync -> 401 Not connected
    - User B disconnects -> User A remains connected
    """
    token_a, user_a_id = make_auth_token(email="usera@example.com")
    token_b, user_b_id = make_auth_token(email="userb@example.com")

    headers_a = {'Authorization': f'Bearer {token_a}'}
    headers_b = {'Authorization': f'Bearer {token_b}'}

    with app.test_client() as client:
        # Mock get_user_gmail_service so User A has connection, User B does not
        mock_service_a = MagicMock()
        mock_service_a.is_connected.return_value = True
        mock_service_a.get_profile.return_value = 'usera@gmail.com'
        mock_conn_a = MagicMock(gmail_address='usera@gmail.com')

        def fake_get_user_service(uid):
            if uid == user_a_id:
                return mock_service_a, mock_conn_a
            return None, None

        with patch('app.get_user_gmail_service', side_effect=fake_get_user_service):
            # User A status
            res_a = client.get('/api/gmail/status', headers=headers_a)
            assert res_a.status_code == 200
            assert res_a.get_json() == {'connected': True, 'email': 'usera@gmail.com'}

            # User B status is disconnected
            res_b = client.get('/api/gmail/status', headers=headers_b)
            assert res_b.status_code == 200
            assert res_b.get_json() == {'connected': False}

            # User B sync returns 401
            res_b_sync = client.post('/api/gmail/sync', headers=headers_b)
            assert res_b_sync.status_code == 401
            assert "Not connected to Gmail" in res_b_sync.get_json()['error']

            # User B disconnect does not affect User A
            res_b_disc = client.post('/api/gmail/disconnect', headers=headers_b)
            assert res_b_disc.status_code == 200

            # User A is still connected
            res_a_check = client.get('/api/gmail/status', headers=headers_a)
            assert res_a_check.status_code == 200
            assert res_a_check.get_json()['connected'] is True


def test_token_refresh_persistence_logic():
    """Verify that when GmailService refreshes tokens, updated credentials are encrypted and persisted."""
    user_id = str(uuid.uuid4())
    original_creds = {
        'token': 'old-token',
        'refresh_token': 'valid-refresh-token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'cid',
        'client_secret': 'csec',
        'scopes': ['https://www.googleapis.com/auth/gmail.readonly']
    }
    refreshed_creds = {
        **original_creds,
        'token': 'new-refreshed-token'
    }

    mock_conn = MagicMock()
    mock_conn.encrypted_credentials_json = encrypt_credentials(original_creds)

    mock_service = MagicMock()
    mock_service.is_connected.return_value = True
    mock_service.get_credentials_dict.return_value = refreshed_creds

    from app import persist_credentials_if_refreshed
    with patch('app.db.session.commit') as mock_commit:
        persist_credentials_if_refreshed(mock_conn, mock_service, initial_token='old-token')
        assert mock_commit.called
        # Verify the saved string decrypts to the refreshed token
        saved_encrypted = mock_conn.encrypted_credentials_json
        decrypted = decrypt_credentials(saved_encrypted)
        assert decrypted['token'] == 'new-refreshed-token'

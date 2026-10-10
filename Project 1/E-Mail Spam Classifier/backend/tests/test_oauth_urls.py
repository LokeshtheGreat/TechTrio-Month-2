import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, get_backend_url, get_frontend_url
from services.gmail_service import GmailService
from utils.encryption import generate_oauth_state
from cryptography.fernet import Fernet
import uuid
import jwt
import time

TEST_ENCRYPTION_KEY = Fernet.generate_key().decode('utf-8')
TEST_JWT_SECRET = "super-secret-test-supabase-jwt-key-32chars"


def create_test_token(user_id=None):
    uid = user_id or str(uuid.uuid4())
    payload = {
        'sub': uid,
        'email': 'test@example.com',
        'aud': 'authenticated',
        'role': 'authenticated',
        'exp': int(time.time()) + 3600
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm='HS256')


@pytest.fixture(autouse=True)
def setup_oauth_test_env(monkeypatch):
    monkeypatch.setenv('SUPABASE_JWT_SECRET', TEST_JWT_SECRET)


def test_get_backend_url_local_fallback(monkeypatch):
    """When no env vars are set, get_backend_url must cleanly fall back to localhost:5000."""
    monkeypatch.delenv('BACKEND_URL', raising=False)
    monkeypatch.delenv('RENDER_EXTERNAL_URL', raising=False)
    assert get_backend_url() == 'http://localhost:5000'


def test_get_backend_url_configured_production(monkeypatch):
    """When BACKEND_URL is set, get_backend_url must return the production URL."""
    monkeypatch.setenv('BACKEND_URL', 'https://spam-shield-api.onrender.com')
    assert get_backend_url() == 'https://spam-shield-api.onrender.com'


def test_get_backend_url_strips_trailing_slash_and_whitespace(monkeypatch):
    """Ensure trailing slashes and padding are stripped to prevent double-slash redirect URIs."""
    monkeypatch.setenv('BACKEND_URL', '  https://spam-shield-api.onrender.com///  ')
    assert get_backend_url() == 'https://spam-shield-api.onrender.com'


def test_get_backend_url_render_external_url_fallback(monkeypatch):
    """When BACKEND_URL is missing on Render, automatically fall back to RENDER_EXTERNAL_URL."""
    monkeypatch.delenv('BACKEND_URL', raising=False)
    monkeypatch.setenv('RENDER_EXTERNAL_URL', 'https://auto-rendered-app.onrender.com/')
    assert get_backend_url() == 'https://auto-rendered-app.onrender.com'


def test_get_frontend_url_local_fallback(monkeypatch):
    """When FRONTEND_URL is unset, default to Vite's local dev server port 5173."""
    monkeypatch.delenv('FRONTEND_URL', raising=False)
    assert get_frontend_url() == 'http://localhost:5173'


def test_get_frontend_url_configured_production(monkeypatch):
    """When FRONTEND_URL is configured, return the production Vercel frontend URL stripped."""
    monkeypatch.setenv('FRONTEND_URL', 'https://spam-shield.vercel.app/')
    assert get_frontend_url() == 'https://spam-shield.vercel.app'


def test_gmail_connect_constructs_production_redirect_uri(monkeypatch):
    """Verify that /api/gmail/connect passes the production redirect_uri to Google OAuth."""
    monkeypatch.setenv('BACKEND_URL', 'https://spam-shield-api.onrender.com')
    monkeypatch.setenv('TOKEN_ENCRYPTION_KEY', TEST_ENCRYPTION_KEY)
    monkeypatch.setenv('SUPABASE_JWT_SECRET', TEST_JWT_SECRET)

    captured_redirect_uri = None

    def fake_get_auth_url(redirect_uri, state=None, code_verifier=None):
        nonlocal captured_redirect_uri
        captured_redirect_uri = redirect_uri
        return 'https://accounts.google.com/o/oauth2/v2/auth?mock=1', state, code_verifier

    with patch.object(GmailService, 'get_auth_url', side_effect=fake_get_auth_url):
        with app.test_client() as client:
            token = create_test_token()
            res = client.get('/api/gmail/connect', headers={'Authorization': f'Bearer {token}'})
            # Follows 302 redirect to Google auth URL
            assert res.status_code == 302
            assert res.location.startswith('https://accounts.google.com')
            # Confirm redirect_uri passed to Google OAuth was the production URL
            assert captured_redirect_uri == 'https://spam-shield-api.onrender.com/api/gmail/callback'
            assert 'localhost' not in captured_redirect_uri


def test_gmail_connect_json_format_support(monkeypatch):
    """Verify that /api/gmail/connect returns JSON when requested by API clients."""
    monkeypatch.setenv('BACKEND_URL', 'https://spam-shield-api.onrender.com')
    monkeypatch.setenv('TOKEN_ENCRYPTION_KEY', TEST_ENCRYPTION_KEY)
    monkeypatch.setenv('SUPABASE_JWT_SECRET', TEST_JWT_SECRET)

    with patch.object(GmailService, 'get_auth_url', return_value=('https://accounts.google.com/o/oauth2/v2/auth?mock=1', 'state', 'verifier')):
        with app.test_client() as client:
            token = create_test_token()
            res = client.get('/api/gmail/connect?format=json', headers={'Authorization': f'Bearer {token}'})
            assert res.status_code == 200
            data = res.get_json()
            assert 'auth_url' in data
            assert data['auth_url'].startswith('https://accounts.google.com')


def test_gmail_callback_redirects_to_production_frontend(monkeypatch):
    """Verify that /api/gmail/callback redirects the browser to the production Vercel frontend."""
    monkeypatch.setenv('BACKEND_URL', 'https://spam-shield-api.onrender.com')
    monkeypatch.setenv('FRONTEND_URL', 'https://spam-shield.vercel.app')
    monkeypatch.setenv('TOKEN_ENCRYPTION_KEY', TEST_ENCRYPTION_KEY)

    user_id = str(uuid.uuid4())
    valid_state = generate_oauth_state(user_id=user_id, csrf_nonce='mock-csrf', code_verifier='mock-verifier')

    mock_tokens = {
        'token': 'mock-token',
        'refresh_token': 'mock-refresh',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'mock-client-id',
        'client_secret': 'mock-client-secret',
        'scopes': ['https://www.googleapis.com/auth/gmail.readonly']
    }

    with patch.object(GmailService, 'exchange_code', return_value=mock_tokens), \
         patch.object(GmailService, 'get_profile', return_value=f'test-{user_id[:8]}@gmail.com'):
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['oauth_state'] = valid_state
                sess['oauth_csrf'] = 'mock-csrf'
                sess['oauth_user_id'] = user_id

            res = client.get(f'/api/gmail/callback?code=mock_code&state={valid_state}')
            assert res.status_code == 302
            assert res.location == 'https://spam-shield.vercel.app/?gmail_connected=true'
            assert 'localhost' not in res.location


def test_exchange_code_signature_accepts_state_and_verifier():
    """Verify that exchange_code accepts (code, redirect_uri, state, code_verifier) without TypeError."""
    mock_flow = MagicMock()
    mock_flow.credentials.to_json.return_value = '{"token": "xyz"}'

    with patch.object(GmailService, '_get_flow', return_value=mock_flow):
        result = GmailService.exchange_code(
            code='fake-code',
            redirect_uri='https://spam-shield-api.onrender.com/api/gmail/callback',
            state='mock-state',
            code_verifier='mock-verifier'
        )
        assert result == {"token": "xyz"}
        mock_flow.fetch_token.assert_called_once_with(code='fake-code', code_verifier='mock-verifier')


def test_gmail_connect_unauthenticated_returns_401():
    """Verify that accessing /api/gmail/connect without an Authorization header returns 401."""
    with app.test_client() as client:
        res = client.get('/api/gmail/connect?format=json')
        assert res.status_code == 401
        assert res.get_json() == {'error': 'Unauthorized: Missing Authorization header.'}


def test_gmail_connect_invalid_token_returns_401():
    """Verify that accessing /api/gmail/connect with an invalid/expired token returns 401."""
    with app.test_client() as client:
        res = client.get(
            '/api/gmail/connect?format=json',
            headers={'Authorization': 'Bearer invalid.bogus.jwt.token'}
        )
        assert res.status_code == 401
        assert res.get_json() == {'error': 'Unauthorized: Invalid or expired access token.'}


def test_gmail_status_unauthenticated_returns_401():
    """Verify that accessing /api/gmail/status without Authorization header returns 401."""
    with app.test_client() as client:
        res = client.get('/api/gmail/status')
        assert res.status_code == 401
        assert res.get_json() == {'error': 'Unauthorized: Missing Authorization header.'}


def test_gmail_status_invalid_token_returns_401():
    """Verify that accessing /api/gmail/status with invalid token returns 401."""
    with app.test_client() as client:
        res = client.get(
            '/api/gmail/status',
            headers={'Authorization': 'Bearer invalid.bogus.jwt.token'}
        )
        assert res.status_code == 401
        assert res.get_json() == {'error': 'Unauthorized: Invalid or expired access token.'}


def test_gmail_status_authenticated_returns_200():
    """Verify that accessing /api/gmail/status with valid Bearer token returns 200 with connected status."""
    with app.test_client() as client:
        token = create_test_token()
        res = client.get('/api/gmail/status', headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200
        data = res.get_json()
        assert 'connected' in data



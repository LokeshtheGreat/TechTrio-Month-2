import os
import sys
import json
import uuid
import tempfile
from datetime import datetime, timezone, timedelta
import pytest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gmail_service import GmailService
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

MOCK_WEB_CONFIG = {
    "web": {
        "client_id": "test-client-id.apps.googleusercontent.com",
        "project_id": "test-project-123",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "test-client-secret-xyz",
        "redirect_uris": [
            "https://spam-shield-api.onrender.com/api/gmail/callback",
            "http://localhost:5000/api/gmail/callback"
        ]
    }
}


@pytest.fixture(autouse=True)
def isolate_credentials_env(monkeypatch):
    """
    Ensures tests start with a clean credential environment, preventing ambient
    .env or host variables from interfering with discrete or fallback assertions.
    """
    monkeypatch.delenv('GOOGLE_CLIENT_ID', raising=False)
    monkeypatch.delenv('GOOGLE_CLIENT_SECRET', raising=False)
    monkeypatch.delenv('GMAIL_CLIENT_ID', raising=False)
    monkeypatch.delenv('GMAIL_CLIENT_SECRET', raising=False)


# =========================================================================
# 1. RETRIEVAL & PARSING TESTS (JSON & FILE FALLBACKS)
# =========================================================================

def test_get_client_config_from_valid_json_env(monkeypatch):
    """Verify that GOOGLE_CREDENTIALS_JSON containing valid JSON text is parsed in memory."""
    monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', json.dumps(MOCK_WEB_CONFIG))
    config = GmailService._get_client_config()
    assert isinstance(config, dict)
    assert 'web' in config
    assert config['web']['client_id'] == "test-client-id.apps.googleusercontent.com"
    assert config['web']['client_secret'] == "test-client-secret-xyz"


def test_get_client_config_with_surrounding_quotes(monkeypatch):
    """Verify that single or double quotes added by .env parsers are cleanly stripped."""
    json_str = json.dumps(MOCK_WEB_CONFIG)
    # Surrounding single quotes
    monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', f"'{json_str}'")
    config1 = GmailService._get_client_config()
    assert config1['web']['client_id'] == "test-client-id.apps.googleusercontent.com"

    # Surrounding double quotes
    monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', f'"{json_str}"')
    config2 = GmailService._get_client_config()
    assert config2['web']['client_id'] == "test-client-id.apps.googleusercontent.com"


def test_get_client_config_from_file_path_env(monkeypatch):
    """Verify that GOOGLE_CREDENTIALS_JSON pointing to an existing file path loads correctly."""
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as temp_file:
        json.dump(MOCK_WEB_CONFIG, temp_file)
        temp_path = temp_file.name

    try:
        monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', temp_path)
        config = GmailService._get_client_config()
        assert config['web']['client_id'] == "test-client-id.apps.googleusercontent.com"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_get_client_config_fallback_to_credentials_file(monkeypatch):
    """Verify fallback to candidate credentials.json on disk when GOOGLE_CREDENTIALS_JSON is unset."""
    monkeypatch.delenv('GOOGLE_CREDENTIALS_JSON', raising=False)
    monkeypatch.setattr('dotenv.load_dotenv', lambda *args, **kwargs: None)

    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as temp_file:
        json.dump(MOCK_WEB_CONFIG, temp_file)
        temp_path = temp_file.name

    # Patch os.path.exists and open to simulate backend/credentials.json existing
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.modules[GmailService.__module__].__file__)))
    target_path = os.path.normpath(os.path.join(backend_dir, 'credentials.json'))

    orig_exists = os.path.exists

    def mock_exists(p):
        if os.path.normpath(p) == target_path:
            return True
        if os.path.basename(p) == 'credentials.json':
            return False
        return orig_exists(p)

    monkeypatch.setattr(os.path, 'exists', mock_exists)
    with monkeypatch.context() as m:
        orig_open = open
        def mock_open(file, *args, **kwargs):
            if isinstance(file, str) and os.path.normpath(file) == target_path:
                return orig_open(temp_path, *args, **kwargs)
            return orig_open(file, *args, **kwargs)
        m.setattr('builtins.open', mock_open)
        config = GmailService._get_client_config()
        assert config['web']['client_id'] == "test-client-id.apps.googleusercontent.com"

    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_get_client_config_missing_raises_runtime_error(monkeypatch):
    """Verify informative RuntimeError when neither env var nor file is present."""
    monkeypatch.delenv('GOOGLE_CREDENTIALS_JSON', raising=False)
    monkeypatch.setattr('dotenv.dotenv_values', lambda *args, **kwargs: {})
    monkeypatch.setattr(os.path, 'exists', lambda p: False)

    with pytest.raises(RuntimeError, match="Google OAuth credentials not found"):
        GmailService._get_client_config()


def test_get_client_config_malformed_json_raises_value_error(monkeypatch):
    """Verify ValueError when GOOGLE_CREDENTIALS_JSON has malformed JSON."""
    monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', '{bad-json: true')
    with pytest.raises(ValueError, match="Failed to parse GOOGLE_CREDENTIALS_JSON: Invalid JSON"):
        GmailService._get_client_config()


def test_get_client_config_invalid_schema_raises_value_error(monkeypatch):
    """Verify ValueError when JSON is missing 'web' or 'installed' client config dictionary."""
    monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', json.dumps({"other_key": "some_value"}))
    with pytest.raises(ValueError, match="Expected top-level 'web' or 'installed' dictionary"):
        GmailService._get_client_config()


def test_get_flow_in_memory_without_file(monkeypatch):
    """Verify that _get_flow constructs a Flow instance directly in memory without files."""
    monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', json.dumps(MOCK_WEB_CONFIG))

    flow = GmailService._get_flow("https://spam-shield-api.onrender.com/api/gmail/callback")
    assert isinstance(flow, Flow)
    assert flow.redirect_uri == "https://spam-shield-api.onrender.com/api/gmail/callback"
    auth_url, _ = flow.authorization_url()
    assert auth_url.startswith("https://accounts.google.com/o/oauth2/auth")


# =========================================================================
# 2. DISCRETE CONFIGURATION PRECEDENCE & HELPERS
# =========================================================================

def test_get_client_config_discrete_precedence_over_json_and_files(monkeypatch):
    """GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET take strict precedence over GOOGLE_CREDENTIALS_JSON."""
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'discrete-client-id.apps.googleusercontent.com')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'discrete-client-secret-456')
    monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', json.dumps(MOCK_WEB_CONFIG))

    config = GmailService._get_client_config()
    assert isinstance(config, dict)
    assert 'web' in config
    assert config['web']['client_id'] == 'discrete-client-id.apps.googleusercontent.com'
    assert config['web']['client_secret'] == 'discrete-client-secret-456'
    assert 'redirect_uris' in config['web']
    assert len(config['web']['redirect_uris']) > 0
    # Ensure no duplicates in redirect_uris
    assert len(config['web']['redirect_uris']) == len(set(config['web']['redirect_uris']))


def test_get_client_config_discrete_alias_support(monkeypatch):
    """Verify GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET work as discrete configuration aliases."""
    monkeypatch.setenv('GMAIL_CLIENT_ID', 'alias-id.apps.googleusercontent.com')
    monkeypatch.setenv('GMAIL_CLIENT_SECRET', 'alias-secret-789')

    config = GmailService._get_client_config()
    assert config['web']['client_id'] == 'alias-id.apps.googleusercontent.com'
    assert config['web']['client_secret'] == 'alias-secret-789'


def test_get_client_config_discrete_partial_falls_back_to_json(monkeypatch):
    """When only one discrete variable is provided, safely fall back to GOOGLE_CREDENTIALS_JSON."""
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'partial-client-id')
    # GOOGLE_CLIENT_SECRET left unset
    monkeypatch.setenv('GOOGLE_CREDENTIALS_JSON', json.dumps(MOCK_WEB_CONFIG))

    config = GmailService._get_client_config()
    assert config['web']['client_id'] == 'test-client-id.apps.googleusercontent.com'
    assert config['web']['client_secret'] == 'test-client-secret-xyz'


def test_get_active_client_config_safe_when_unconfigured(monkeypatch):
    """get_active_client_config and get_active_client_id_and_secret return None without throwing."""
    monkeypatch.delenv('GOOGLE_CREDENTIALS_JSON', raising=False)
    monkeypatch.setattr('dotenv.load_dotenv', lambda *args, **kwargs: None)
    monkeypatch.setattr(os.path, 'exists', lambda p: False)

    assert GmailService.get_active_client_config() is None
    assert GmailService.get_active_client_id_and_secret() == (None, None)


# =========================================================================
# 3. TOKEN REFRESH RECONCILIATION & MUTATION SAFETY
# =========================================================================

def test_token_refresh_reconciles_active_secret_when_client_id_matches(monkeypatch):
    """When stored client_id matches the active configured client_id, the active client_secret is reconciled."""
    active_cid = "matching-client-id.apps.googleusercontent.com"
    active_csec = "active-new-secret-2026"
    monkeypatch.setenv('GOOGLE_CLIENT_ID', active_cid)
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', active_csec)

    stored_creds = {
        "client_id": active_cid,
        "client_secret": "stale-old-secret-from-database",
        "token": "expired-access-token",
        "refresh_token": "valid-user-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
    }

    refreshed_called = []
    def fake_refresh(creds, request=None):
        refreshed_called.append(True)
        assert creds.client_id == active_cid
        assert creds.client_secret == active_csec
        creds.token = "new-fresh-access-token"
        creds.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)

    with patch.object(Credentials, 'refresh', fake_refresh):
        service = GmailService(stored_creds)
        assert service.is_connected() is True
        assert len(refreshed_called) == 1
        assert service.creds.client_secret == active_csec

        exported = service.get_credentials_dict()
        assert exported['client_secret'] == active_csec
        assert exported['token'] == "new-fresh-access-token"
        assert exported['client_id'] == active_cid

    # Verify input dictionary was not mutated in-place
    assert stored_creds['client_secret'] == "stale-old-secret-from-database"


def test_token_refresh_reconciles_when_client_id_missing_in_stored_payload(monkeypatch):
    """When stored credentials omit client_id, active client_id and client_secret are safely reconciled."""
    active_cid = "repaired-client-id.apps.googleusercontent.com"
    active_csec = "repaired-secret-2026"
    monkeypatch.setenv('GOOGLE_CLIENT_ID', active_cid)
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', active_csec)

    stored_creds_no_cid = {
        "client_secret": "old-unknown-secret",
        "token": "expired-access-token",
        "refresh_token": "valid-user-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
    }

    def fake_refresh(creds, request=None):
        assert creds.client_id == active_cid
        assert creds.client_secret == active_csec
        creds.token = "refreshed-token-from-repaired"
        creds.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)

    with patch.object(Credentials, 'refresh', fake_refresh):
        service = GmailService(stored_creds_no_cid)
        assert service.is_connected() is True
        assert service.creds.client_id == active_cid
        assert service.creds.client_secret == active_csec
        exported = service.get_credentials_dict()
        assert exported['client_id'] == active_cid
        assert exported['client_secret'] == active_csec
        assert exported['token'] == "refreshed-token-from-repaired"


def test_token_refresh_prevents_reconciliation_when_client_id_mismatches(monkeypatch):
    """When stored client_id belongs to a different client, do NOT mutate or overwrite client_secret."""
    active_cid = "client-alpha.apps.googleusercontent.com"
    active_csec = "secret-alpha-active"
    monkeypatch.setenv('GOOGLE_CLIENT_ID', active_cid)
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', active_csec)

    stored_foreign_creds = {
        "client_id": "client-beta.apps.googleusercontent.com",
        "client_secret": "secret-beta-original",
        "token": "valid-token-for-beta",
        "refresh_token": "beta-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
    }

    refresh_called = []
    def fake_refresh(creds, request=None):
        refresh_called.append(True)
        # Verify that refresh attempted using the original client_id and client_secret
        assert creds.client_id == "client-beta.apps.googleusercontent.com"
        assert creds.client_secret == "secret-beta-original"
        creds.token = "refreshed-beta-token"
        creds.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)

    with patch.object(Credentials, 'refresh', fake_refresh):
        service = GmailService(stored_foreign_creds)
        assert service.is_connected() is True
        assert service.creds.client_id == "client-beta.apps.googleusercontent.com"
        assert service.creds.client_secret == "secret-beta-original"
        assert stored_foreign_creds['client_secret'] == "secret-beta-original"
        assert len(refresh_called) == 1


def test_refresh_credentials_method_reconciles_and_refreshes(monkeypatch):
    """Explicit refresh_credentials method reconciles compatible client secrets and updates token."""
    active_cid = "refresh-method-cid.apps.googleusercontent.com"
    active_csec = "refresh-method-new-sec"
    monkeypatch.setenv('GOOGLE_CLIENT_ID', active_cid)
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', active_csec)

    future_expiry = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=2)).isoformat()
    creds_dict = {
        "client_id": active_cid,
        "client_secret": "refresh-method-old-sec",
        "token": "current-tok",
        "refresh_token": "rt-method",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "expiry": future_expiry
    }

    # Start with valid token (not refreshed during __init__)
    service = GmailService(creds_dict)
    assert service.is_connected() is True

    def fake_refresh(creds, request=None):
        assert creds.client_secret == active_csec
        creds.token = "token-after-explicit-refresh"
        creds.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)

    with patch.object(Credentials, 'refresh', fake_refresh):
        ok = service.refresh_credentials()
        assert ok is True
        assert service.creds.client_secret == active_csec
        assert service.creds.token == "token-after-explicit-refresh"


def test_malformed_credentials_handled_gracefully_without_crash():
    """Invalid, empty, or non-dict credentials payloads do not crash GmailService."""
    assert GmailService(None).is_connected() is False
    assert GmailService("").is_connected() is False
    assert GmailService("{not-valid-json").is_connected() is False
    assert GmailService(42).is_connected() is False
    assert GmailService({"some_random_key": "val"}).is_connected() is False


# =========================================================================
# 4. WATCH RENEWAL INTEGRATION WITH RECONCILED CREDENTIALS
# =========================================================================

def test_watch_renewal_flow_with_reconciled_credentials(monkeypatch):
    """End-to-end watch renewal flow succeeds when stored credentials are reconciled with active secret."""
    from cryptography.fernet import Fernet
    from app import app, get_user_gmail_service
    from models import GmailConnection
    from utils.encryption import encrypt_credentials, decrypt_credentials

    test_key = Fernet.generate_key().decode('utf-8')
    monkeypatch.setenv('TOKEN_ENCRYPTION_KEY', test_key)

    active_cid = "watch-renewal-cid.apps.googleusercontent.com"
    active_csec = "watch-renewal-new-sec"
    monkeypatch.setenv('GOOGLE_CLIENT_ID', active_cid)
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', active_csec)

    user_id = str(uuid.uuid4())
    stale_stored_creds = {
        "client_id": active_cid,
        "client_secret": "watch-renewal-stale-secret",
        "token": "expired-pre-watch-token",
        "refresh_token": "valid-user-watch-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
    }

    mock_conn = MagicMock(spec=GmailConnection)
    mock_conn.user_id = user_id
    mock_conn.encrypted_credentials_json = encrypt_credentials(stale_stored_creds)
    mock_conn.monitoring_status = 'pending'

    def fake_refresh(creds, request=None):
        assert creds.client_secret == active_csec
        creds.token = "refreshed-watch-access-token"
        creds.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)

    mock_watch_res = {'historyId': '987654321', 'expiration': '1744384000000'}

    with app.app_context():
        with patch('models.GmailConnection.query') as mock_query, \
             patch('app.db.session.commit') as mock_commit, \
             patch.object(Credentials, 'refresh', fake_refresh):

            mock_filter = MagicMock()
            mock_filter.first.return_value = mock_conn
            mock_query.filter_by.return_value = mock_filter

            service, conn = get_user_gmail_service(user_id)
            assert service is not None
            assert service.is_connected() is True
            assert mock_commit.called

            # Verify that encrypted_credentials_json was updated with new token & secret
            updated_creds = decrypt_credentials(conn.encrypted_credentials_json)
            assert updated_creds['token'] == "refreshed-watch-access-token"
            assert updated_creds['client_secret'] == active_csec

            # Now execute watch on this refreshed service
            mock_api = MagicMock()
            mock_api.users().watch().execute.return_value = mock_watch_res
            with patch('services.gmail_service.build', return_value=mock_api):
                res = service.start_watch("projects/test-project/topics/test-topic")
                assert res['historyId'] == '987654321'

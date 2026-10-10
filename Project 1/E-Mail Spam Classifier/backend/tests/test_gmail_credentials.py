import os
import sys
import json
import tempfile
import pytest

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gmail_service import GmailService
from google_auth_oauthlib.flow import Flow

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

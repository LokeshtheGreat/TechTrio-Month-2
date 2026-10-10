import os
import pytest
from utils.encryption import encrypt_credentials, decrypt_credentials, get_cipher

def test_missing_encryption_key_fails_securely():
    """Verify that get_cipher raises RuntimeError when TOKEN_ENCRYPTION_KEY is unset."""
    old_key = os.environ.pop('TOKEN_ENCRYPTION_KEY', None)
    try:
        with pytest.raises(RuntimeError, match="TOKEN_ENCRYPTION_KEY environment variable is missing"):
            get_cipher()
    finally:
        if old_key is not None:
            os.environ['TOKEN_ENCRYPTION_KEY'] = old_key

def test_invalid_encryption_key_format_fails():
    """Verify that invalid Fernet keys raise ValueError."""
    os.environ['TOKEN_ENCRYPTION_KEY'] = 'not-a-valid-fernet-key'
    with pytest.raises(ValueError, match="Invalid TOKEN_ENCRYPTION_KEY format"):
        get_cipher()

def test_encryption_decryption_roundtrip():
    """Verify clean encryption and decryption of OAuth credential payloads."""
    os.environ['TOKEN_ENCRYPTION_KEY'] = 'V-KjP7a2_8W_TjN7Q4_X6L9mN2Y3q9L4P2k7X9v1w3o='
    
    mock_creds = {
        "token": "mock_access_token_abc123",
        "refresh_token": "mock_refresh_token_xyz789",
        "expiry": "2030-01-01T00:00:00Z"
    }
    
    encrypted = encrypt_credentials(mock_creds)
    assert encrypted != str(mock_creds)
    assert isinstance(encrypted, str)
    
    decrypted = decrypt_credentials(encrypted)
    assert decrypted['token'] == "mock_access_token_abc123"
    assert decrypted['refresh_token'] == "mock_refresh_token_xyz789"

def test_decrypt_empty():
    os.environ['TOKEN_ENCRYPTION_KEY'] = 'V-KjP7a2_8W_TjN7Q4_X6L9mN2Y3q9L4P2k7X9v1w3o='
    assert decrypt_credentials(None) is None
    assert decrypt_credentials("") is None

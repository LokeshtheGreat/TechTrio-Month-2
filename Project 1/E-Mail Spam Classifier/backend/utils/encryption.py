import os
import json
import secrets
import time
from cryptography.fernet import Fernet, InvalidToken

def get_cipher():
    """
    Retrieves the Fernet cipher instance using TOKEN_ENCRYPTION_KEY.
    Fails securely if the key is missing or invalid.
    Never uses a hardcoded fallback key.
    """
    key_str = os.environ.get('TOKEN_ENCRYPTION_KEY')
    if not key_str:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY environment variable is missing. "
            "A valid 32-byte URL-safe base64-encoded Fernet key is strictly required "
            "for encrypting credentials at rest."
        )

    if isinstance(key_str, str):
        key_bytes = key_str.strip().encode('utf-8')
    else:
        key_bytes = key_str

    try:
        return Fernet(key_bytes)
    except Exception as e:
        raise ValueError(f"Invalid TOKEN_ENCRYPTION_KEY format: {str(e)}")


def encrypt_credentials(creds_dict):
    """
    Serializes and encrypts an OAuth credentials dictionary.
    """
    if not creds_dict:
        raise ValueError("Cannot encrypt empty credentials dictionary.")
    cipher = get_cipher()
    json_str = json.dumps(creds_dict)
    encrypted_bytes = cipher.encrypt(json_str.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_credentials(encrypted_str):
    """
    Decrypts and deserializes an encrypted credentials string back into a dictionary.
    Returns None if input is empty or None.
    """
    if not encrypted_str:
        return None
    cipher = get_cipher()
    decrypted_bytes = cipher.decrypt(encrypted_str.encode('utf-8'))
    return json.loads(decrypted_bytes.decode('utf-8'))


def generate_oauth_state(user_id, csrf_nonce=None, code_verifier=None):
    """
    Cryptographically binds user_id, CSRF nonce, and optional PKCE code_verifier
    into a tamper-proof state string encrypted with TOKEN_ENCRYPTION_KEY.
    Includes an expiration timestamp (10 minutes).
    """
    if not user_id:
        raise ValueError("Cannot generate OAuth state without a user_id.")
    payload = {
        'user_id': str(user_id),
        'csrf': csrf_nonce or secrets.token_urlsafe(16),
        'code_verifier': code_verifier,
        'exp': int(time.time()) + 600
    }
    return encrypt_credentials(payload)


def verify_oauth_state(state_str, expected_csrf=None, expected_user_id=None):
    """
    Decrypts and validates the OAuth state string.
    Verifies:
      - Valid encryption signature (tamper-proof)
      - Expiration (rejects if expired)
      - CSRF nonce matches expected_csrf if provided
      - user_id matches expected_user_id if provided
    Returns the unpacked dict containing user_id, csrf, and code_verifier.
    Raises ValueError on missing, malformed, expired, or mismatched state.
    """
    if not state_str:
        raise ValueError("Missing OAuth state parameter.")

    try:
        data = decrypt_credentials(state_str)
    except Exception as e:
        raise ValueError(f"Invalid or tampered OAuth state: {str(e)}")

    if not isinstance(data, dict):
        raise ValueError("Malformed OAuth state payload.")

    exp = data.get('exp', 0)
    if time.time() > exp:
        raise ValueError("OAuth state has expired. Please initiate connection again.")

    user_id = data.get('user_id')
    if not user_id:
        raise ValueError("OAuth state missing user_id.")

    csrf = data.get('csrf')
    if expected_csrf and csrf != expected_csrf:
        raise ValueError("OAuth CSRF state mismatch.")

    if expected_user_id and user_id != str(expected_user_id):
        raise ValueError("OAuth user mismatch.")

    return data


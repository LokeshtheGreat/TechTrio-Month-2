import os
import time
import uuid
import jwt
import pytest
from flask import Flask, jsonify, g
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from utils.supabase_auth import (
    verify_supabase_token,
    require_supabase_auth,
    get_supabase_config,
    ALLOWED_ALGORITHMS
)

TEST_JWT_SECRET = "super-secret-test-supabase-jwt-key-32chars"


def create_mock_supabase_token(user_id=None, email="test@example.com", expires_in=3600, aud="authenticated", iss=None, secret=TEST_JWT_SECRET, alg="HS256", headers=None):
    user_uuid = user_id or str(uuid.uuid4())
    payload = {
        "sub": user_uuid,
        "email": email,
        "aud": aud,
        "role": "authenticated",
        "exp": int(time.time()) + expires_in,
        "iat": int(time.time()),
    }
    if iss:
        payload["iss"] = iss
    return jwt.encode(payload, secret, algorithm=alg, headers=headers)


def test_supabase_config_helper():
    """Verify get_supabase_config retrieves without crashing."""
    config = get_supabase_config()
    assert isinstance(config, dict)
    assert 'url' in config
    assert 'jwt_secret' in config


def test_allowed_algorithms_whitelist():
    """Verify that only expected algorithms are whitelisted."""
    assert 'HS256' in ALLOWED_ALGORITHMS
    assert 'RS256' in ALLOWED_ALGORITHMS
    assert 'ES256' in ALLOWED_ALGORITHMS
    assert 'none' not in ALLOWED_ALGORITHMS
    assert 'HS384' not in ALLOWED_ALGORITHMS
    assert 'HS512' not in ALLOWED_ALGORITHMS


def test_verify_valid_hs256_token():
    """Verify valid mock HS256 token returns user_id and email."""
    uid = str(uuid.uuid4())
    token = create_mock_supabase_token(user_id=uid, email="hello@supabase.io")
    result = verify_supabase_token(token, jwt_secret=TEST_JWT_SECRET)
    assert result['user_id'] == uid
    assert result['email'] == "hello@supabase.io"
    assert result['role'] == "authenticated"


def test_verify_valid_rs256_token_with_mocked_jwks():
    """Verify valid mock RS256 token verified via mocked JWKS client."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    uid = str(uuid.uuid4())
    token = create_mock_supabase_token(
        user_id=uid,
        email="asymmetric@supabase.io",
        secret=private_key,
        alg="RS256",
        headers={"kid": "mock-key-id"}
    )

    class MockSigningKey:
        def __init__(self, key):
            self.key = key

    class MockJWKClient:
        def get_signing_key_from_jwt(self, raw_token):
            return MockSigningKey(public_key)

    mock_client = MockJWKClient()
    result = verify_supabase_token(token, jwk_client=mock_client)
    assert result['user_id'] == uid
    assert result['email'] == "asymmetric@supabase.io"


def test_unsupported_algorithm_none_rejected():
    """Verify algorithm 'none' is rejected with InvalidAlgorithmError."""
    # Construct an unverified token with alg='none'
    header = {"alg": "none", "typ": "JWT"}
    payload = {
        "sub": str(uuid.uuid4()),
        "aud": "authenticated",
        "exp": int(time.time()) + 3600
    }
    raw_token = f"{jwt.utils.base64url_encode(json_bytes(header)).decode('utf-8')}.{jwt.utils.base64url_encode(json_bytes(payload)).decode('utf-8')}."
    with pytest.raises(jwt.InvalidAlgorithmError, match="not permitted"):
        verify_supabase_token(raw_token, jwt_secret=TEST_JWT_SECRET)


def test_unsupported_algorithm_hs384_rejected():
    """Verify unsupported algorithm HS384 is rejected."""
    token = create_mock_supabase_token(alg="HS384")
    with pytest.raises(jwt.InvalidAlgorithmError, match="not permitted"):
        verify_supabase_token(token, jwt_secret=TEST_JWT_SECRET)


def test_asymmetric_token_without_jwks_config_fails_securely():
    """Verify RS256 token fails if server has no SUPABASE_URL and no JWKS client."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = create_mock_supabase_token(
        secret=private_key,
        alg="RS256",
        headers={"kid": "mock-kid"}
    )
    with pytest.raises(RuntimeError, match="SUPABASE_URL is required to resolve asymmetric"):
        verify_supabase_token(token, supabase_url=None, jwk_client=None)


def test_jwks_resolution_failure_fails_closed():
    """Verify failure to resolve key from JWKS raises PyJWTError and fails closed."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = create_mock_supabase_token(
        secret=private_key,
        alg="RS256",
        headers={"kid": "nonexistent-kid"}
    )

    class FailingJWKClient:
        def get_signing_key_from_jwt(self, raw_token):
            raise jwt.PyJWKClientError("Key ID not found in JWKS")

    with pytest.raises(jwt.PyJWTError, match="Unable to resolve public key from JWKS"):
        verify_supabase_token(token, jwk_client=FailingJWKClient())


def test_verify_token_expired():
    """Verify expired token raises ExpiredSignatureError."""
    token = create_mock_supabase_token(expires_in=-10)
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_supabase_token(token, jwt_secret=TEST_JWT_SECRET)


def test_verify_token_invalid_signature():
    """Verify token signed with wrong secret raises InvalidSignatureError."""
    token = create_mock_supabase_token(secret="wrong-secret-key-that-does-not-match")
    with pytest.raises(jwt.InvalidSignatureError):
        verify_supabase_token(token, jwt_secret=TEST_JWT_SECRET)


def test_verify_token_invalid_audience():
    """Verify token with wrong audience raises InvalidAudienceError."""
    token = create_mock_supabase_token(aud="not-authenticated")
    with pytest.raises(jwt.InvalidAudienceError):
        verify_supabase_token(token, jwt_secret=TEST_JWT_SECRET)


def test_verify_token_wrong_issuer():
    """Verify token with unexpected issuer raises InvalidIssuerError."""
    token = create_mock_supabase_token(iss="https://malicious.supabase.co/auth/v1")
    with pytest.raises(jwt.InvalidIssuerError):
        verify_supabase_token(token, jwt_secret=TEST_JWT_SECRET, supabase_url="https://valid.supabase.co")


def test_verify_token_missing_sub():
    """Verify token missing sub claim raises ValueError."""
    payload = {
        "email": "no-sub@example.com",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
    with pytest.raises((jwt.PyJWTError, ValueError)):
        verify_supabase_token(token, jwt_secret=TEST_JWT_SECRET)


def test_verify_token_invalid_uuid_sub():
    """Verify non-UUID subject raises ValueError."""
    token = create_mock_supabase_token(user_id="not-a-valid-uuid-123")
    with pytest.raises(ValueError, match="Invalid user UUID"):
        verify_supabase_token(token, jwt_secret=TEST_JWT_SECRET)


def test_missing_server_secret_raises_runtime_error():
    """Verify missing secret raises RuntimeError."""
    old_secret = os.environ.pop('SUPABASE_JWT_SECRET', None)
    try:
        token = create_mock_supabase_token()
        with pytest.raises(RuntimeError, match="SUPABASE_JWT_SECRET is not configured"):
            verify_supabase_token(token, jwt_secret=None)
    finally:
        if old_secret is not None:
            os.environ['SUPABASE_JWT_SECRET'] = old_secret


def test_require_supabase_auth_generic_401_no_token_leakage():
    """Verify Flask decorator returns generic 401 without exposing token or internal traces."""
    test_app = Flask(__name__)
    os.environ['SUPABASE_JWT_SECRET'] = TEST_JWT_SECRET

    @test_app.route('/protected')
    @require_supabase_auth
    def protected():
        return jsonify({"user_id": g.user_id, "email": g.user_email})

    with test_app.test_client() as client:
        # 1. Missing Authorization header
        res = client.get('/protected')
        assert res.status_code == 401
        assert res.get_json()['error'] == 'Unauthorized: Missing Authorization header.'

        # 2. Malformed Authorization header
        res = client.get('/protected', headers={'Authorization': 'Token 123'})
        assert res.status_code == 401
        assert "Invalid Authorization header format" in res.get_json()['error']

        # 3. Invalid signature token -> generic 401, no stack trace or key leakage
        bad_token = create_mock_supabase_token(secret="bogus-key")
        res = client.get('/protected', headers={'Authorization': f'Bearer {bad_token}'})
        assert res.status_code == 401
        assert res.get_json() == {'error': 'Unauthorized: Invalid or expired access token.'}
        # Ensure token is never in response
        assert bad_token not in res.get_data(as_text=True)

        # 4. Valid token -> 200 with user_id and email
        uid = str(uuid.uuid4())
        valid_token = create_mock_supabase_token(user_id=uid, email="authed@user.com")
        res = client.get('/protected', headers={'Authorization': f'Bearer {valid_token}'})
        assert res.status_code == 200
        assert res.get_json()['user_id'] == uid
        assert res.get_json()['email'] == "authed@user.com"


def json_bytes(obj):
    import json
    return json.dumps(obj).encode('utf-8')

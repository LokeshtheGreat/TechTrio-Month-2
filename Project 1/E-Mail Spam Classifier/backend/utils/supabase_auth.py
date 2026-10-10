import os
import uuid
from functools import wraps
import jwt
from flask import request, jsonify, g

# Strict whitelist of cryptographically approved Supabase token signing algorithms
ALLOWED_ALGORITHMS = {'HS256', 'RS256', 'ES256'}

_jwks_clients = {}

def get_jwks_client(jwks_url):
    """
    Returns a cached PyJWKClient instance for the given JWKS URL.
    Manages key set caching and key rotation with 5-minute lifespan.
    """
    client = _jwks_clients.get(jwks_url)
    if client is None:
        client = jwt.PyJWKClient(
            jwks_url,
            cache_keys=True,
            max_cached_keys=16,
            cache_jwk_set=True,
            lifespan=300,
            timeout=10
        )
        _jwks_clients[jwks_url] = client
    return client

def get_supabase_config():
    """
    Safely retrieves and validates Supabase backend configuration.
    Never exposes service-role keys or passwords.
    """
    url = os.environ.get('SUPABASE_URL')
    jwt_secret = os.environ.get('SUPABASE_JWT_SECRET')
    return {
        'url': url.rstrip('/') if url else None,
        'jwt_secret': jwt_secret
    }

def verify_supabase_token(token_string, jwt_secret=None, supabase_url=None, jwk_client=None):
    """
    Verifies a Supabase-issued JWT access token.
    Strictly verifies:
      - Valid and whitelisted algorithm (HS256, RS256, ES256)
      - Key resolution matching the specified algorithm
      - Cryptographic signature
      - Token expiry (`exp`)
      - Audience (`aud='authenticated'`)
      - Issuer (`iss`) if supabase_url is provided
      - Subject (`sub`) presence and RFC 4122 UUID format

    Returns dict containing verified user_id, email, role, and raw claims.
    Raises jwt.PyJWTError or ValueError on verification failure.
    """
    if not token_string or not isinstance(token_string, str):
        raise ValueError("Missing or invalid token string.")

    config = get_supabase_config()
    secret = jwt_secret or config.get('jwt_secret')
    url = supabase_url or config.get('url')

    try:
        unverified_header = jwt.get_unverified_header(token_string)
    except Exception as e:
        raise jwt.DecodeError(f"Malformed JWT header: {str(e)}")

    alg = unverified_header.get('alg')
    if not alg or alg not in ALLOWED_ALGORITHMS:
        raise jwt.InvalidAlgorithmError(
            f"Algorithm '{alg}' is not permitted. Allowed algorithms: {sorted(list(ALLOWED_ALGORITHMS))}"
        )

    # Resolve signing key based on algorithm
    if alg == 'HS256':
        if not secret:
            raise RuntimeError("SUPABASE_JWT_SECRET is not configured on the server for HS256 verification.")
        key = secret
    elif alg in ('RS256', 'ES256'):
        # Asymmetric signing: resolve public key from JWKS
        if jwk_client:
            client = jwk_client
        elif url:
            jwks_url = f"{url}/auth/v1/.well-known/jwks.json"
            client = get_jwks_client(jwks_url)
        else:
            raise RuntimeError("SUPABASE_URL is required to resolve asymmetric signing keys from JWKS.")

        try:
            signing_key = client.get_signing_key_from_jwt(token_string)
            key = signing_key.key
        except Exception as e:
            raise jwt.PyJWTError(f"Unable to resolve public key from JWKS: {str(e)}")
    else:
        raise jwt.InvalidAlgorithmError(f"Unsupported algorithm: {alg}")

    decode_kwargs = {
        'algorithms': [alg],
        'audience': 'authenticated',
        'options': {
            'verify_signature': True,
            'verify_exp': True,
            'verify_aud': True,
            'require': ['exp', 'sub']
        }
    }

    if url:
        expected_issuer = f"{url}/auth/v1"
        decode_kwargs['issuer'] = expected_issuer
        decode_kwargs['options']['verify_iss'] = True

    claims = jwt.decode(token_string, key, **decode_kwargs)

    user_id = claims.get('sub')
    if not user_id:
        raise ValueError("Token missing 'sub' (subject) claim.")

    # Validate UUID format (RFC 4122)
    try:
        parsed_uuid = uuid.UUID(str(user_id))
    except (ValueError, TypeError, AttributeError):
        raise ValueError(f"Invalid user UUID in token 'sub': {user_id}")

    return {
        'user_id': str(parsed_uuid),
        'email': claims.get('email'),
        'role': claims.get('role'),
        'claims': claims
    }

def require_supabase_auth(f):
    """
    Flask route decorator that validates Supabase JWT from the Authorization header.
    Attaches verified `g.user_id` and `g.user_email` to the request context.
    Returns generic 401 response without leaking token strings or parser details.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = None
        if auth_header:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({'error': 'Unauthorized: Invalid Authorization header format. Expected "Bearer <token>".'}), 401
            token = parts[1]
        else:
            token = request.args.get('token')
            if not token and request.is_json:
                token = request.json.get('token')

        if not token:
            return jsonify({'error': 'Unauthorized: Missing Authorization header.'}), 401

        try:
            verified = verify_supabase_token(token)
            g.user_id = verified['user_id']
            g.user_email = verified['email']
        except RuntimeError:
            # Server configuration issue
            return jsonify({'error': 'Authentication service configuration error.'}), 503
        except (jwt.PyJWTError, ValueError):
            # Generic client error; never echo raw token, signing keys, or internal parser traces
            return jsonify({'error': 'Unauthorized: Invalid or expired access token.'}), 401

        return f(*args, **kwargs)
    return decorated_function

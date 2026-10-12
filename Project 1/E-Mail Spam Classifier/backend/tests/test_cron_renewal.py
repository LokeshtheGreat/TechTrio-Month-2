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

from app import app, db
from models import User, GmailConnection, ClassifiedEmail
from utils.encryption import encrypt_credentials

TEST_ENCRYPTION_KEY = Fernet.generate_key().decode('utf-8')
TEST_JWT_SECRET = "super-secret-test-supabase-jwt-key-32chars"
TEST_CRON_SECRET = "test-cron-secret-xyz-987"
VALID_TOPIC = "projects/my-gcp-project/topics/gmail-watch-prod"


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
    monkeypatch.setenv('CRON_SECRET', TEST_CRON_SECRET)
    monkeypatch.setenv('PUBSUB_TOPIC_NAME', VALID_TOPIC)
    monkeypatch.setenv('BACKEND_URL', 'https://e-mail-spam-shield.onrender.com')
    monkeypatch.setenv('FRONTEND_URL', 'https://e-mail-spam-shield.vercel.app')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dummy:dummy@localhost:5432/testdb'


# =========================================================================
# 1. CRON AUTHENTICATION & REJECTION TESTS
# =========================================================================

def test_cron_renew_rejects_when_cron_secret_unset_on_server(monkeypatch):
    """Missing or empty CRON_SECRET on server must cause a secure 401 rejection."""
    monkeypatch.delenv('CRON_SECRET', raising=False)
    with app.test_client() as client:
        res = client.post('/api/gmail/cron/renew?secret=some-secret')
        assert res.status_code == 401
        data = res.get_json()
        assert "Unauthorized" in data.get('error', '')


def test_cron_renew_rejects_missing_secret():
    """Request without secret parameter or auth header must be rejected with 401."""
    with app.test_client() as client:
        res = client.post('/api/gmail/cron/renew')
        assert res.status_code == 401
        data = res.get_json()
        assert data.get('error') == "Unauthorized"


def test_cron_renew_rejects_invalid_secret_query_param():
    """Request with incorrect secret in query string must be rejected with 401."""
    with app.test_client() as client:
        res = client.post('/api/gmail/cron/renew?secret=wrong-secret-value')
        assert res.status_code == 401
        data = res.get_json()
        assert data.get('error') == "Unauthorized"
        # Secret must never be leaked in response
        assert "wrong-secret-value" not in str(data)
        assert TEST_CRON_SECRET not in str(data)


def test_cron_renew_rejects_invalid_bearer_token():
    """Request with incorrect Bearer token in Authorization header must be rejected with 401."""
    with app.test_client() as client:
        res = client.post(
            '/api/gmail/cron/renew',
            headers={'Authorization': 'Bearer wrong-bearer-token'}
        )
        assert res.status_code == 401
        data = res.get_json()
        assert data.get('error') == "Unauthorized"


def test_cron_renew_rejects_invalid_x_cron_secret():
    """Request with incorrect X-Cron-Secret header must be rejected with 401."""
    with app.test_client() as client:
        res = client.post(
            '/api/gmail/cron/renew',
            headers={'X-Cron-Secret': 'wrong-header-token'}
        )
        assert res.status_code == 401
        data = res.get_json()
        assert data.get('error') == "Unauthorized"


def test_cron_renew_rejects_invalid_json_body():
    """Request with incorrect secret in JSON body must be rejected with 401."""
    with app.test_client() as client:
        res = client.post(
            '/api/gmail/cron/renew',
            json={'secret': 'wrong-json-token'}
        )
        assert res.status_code == 401
        data = res.get_json()
        assert data.get('error') == "Unauthorized"


# =========================================================================
# 2. CONFIGURATION SAFETY & PREREQUISITES
# =========================================================================

def test_cron_renew_fails_when_pubsub_topic_unconfigured(monkeypatch):
    """Missing or dummy PUBSUB_TOPIC_NAME must return 500 error."""
    monkeypatch.setenv('PUBSUB_TOPIC_NAME', '')
    with app.test_client() as client:
        res = client.post(f'/api/gmail/cron/renew?secret={TEST_CRON_SECRET}')
        assert res.status_code == 500
        data = res.get_json()
        assert data.get('success') is False
        assert "PUBSUB_TOPIC_NAME" in data.get('error', '')


def test_cron_renew_fails_when_db_not_configured():
    """Missing database configuration must return 503 error."""
    original_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = None
        with app.test_client() as client:
            res = client.post(f'/api/gmail/cron/renew?secret={TEST_CRON_SECRET}')
            assert res.status_code == 503
            data = res.get_json()
            assert data.get('success') is False
            assert "Database not configured" in data.get('error', '')
    finally:
        app.config['SQLALCHEMY_DATABASE_URI'] = original_uri


# =========================================================================
# 3. MULTI-USER RENEWAL & ISOLATION TESTS
# =========================================================================

def test_cron_renew_empty_state_returns_clean_success():
    """When no eligible connections exist, returns 200 with total_eligible=0."""
    with app.app_context():
        with app.test_client() as client:
            with patch.object(GmailConnection, 'query') as mock_query:
                mock_filter = MagicMock()
                mock_filter.all.return_value = []
                mock_query.filter.return_value = mock_filter

                res = client.post(f'/api/gmail/cron/renew?secret={TEST_CRON_SECRET}')
                assert res.status_code == 200
                data = res.get_json()
                assert data.get('success') is True
                assert data.get('total_eligible') == 0
                assert data.get('renewed') == 0
                assert data.get('failed') == 0
                assert data.get('failures') == []


def test_cron_renew_renews_all_eligible_users_with_isolation():
    """
    Verifies that cron renews watches for ALL eligible connected users (User A, User B, User C),
    preserving individual user scoping and persisting updated expirations.
    """
    user_a_id = 'user-uuid-1111'
    user_b_id = 'user-uuid-2222'
    user_c_id = 'user-uuid-3333'

    conn_a = MagicMock(
        user_id=user_a_id,
        gmail_address='user_a@gmail.com',
        monitoring_status='active',
        encrypted_credentials_json='enc-a',
        watch_expiration=1700000000000,
        history_id='hist-a-old'
    )
    conn_b = MagicMock(
        user_id=user_b_id,
        gmail_address='user_b@gmail.com',
        monitoring_status='failed',  # Previously failed, should be retried!
        encrypted_credentials_json='enc-b',
        watch_expiration=None,
        history_id=None
    )
    conn_c = MagicMock(
        user_id=user_c_id,
        gmail_address='user_c@gmail.com',
        monitoring_status='active',
        encrypted_credentials_json='enc-c',
        watch_expiration=1700000000000,
        history_id='hist-c-old'
    )

    mock_service_a = MagicMock()
    mock_service_a.is_connected.return_value = True
    mock_service_a.start_watch.return_value = {'historyId': 'hist-a-new', 'expiration': '1744384000000'}

    mock_service_b = MagicMock()
    mock_service_b.is_connected.return_value = True
    mock_service_b.start_watch.return_value = {'historyId': 'hist-b-new', 'expiration': '1744384000000'}

    mock_service_c = MagicMock()
    mock_service_c.is_connected.return_value = True
    mock_service_c.start_watch.return_value = {'historyId': 'hist-c-new', 'expiration': '1744384000000'}

    def fake_get_service(uid):
        if uid == user_a_id:
            return mock_service_a, conn_a
        elif uid == user_b_id:
            return mock_service_b, conn_b
        elif uid == user_c_id:
            return mock_service_c, conn_c
        return None, None

    with app.app_context():
        with app.test_client() as client:
            with patch.object(GmailConnection, 'query') as mock_query, \
                 patch('app.get_user_gmail_service', side_effect=fake_get_service), \
                 patch('app.persist_credentials_if_refreshed') as mock_persist, \
                 patch.object(db.session, 'commit') as mock_commit:

                mock_filter = MagicMock()
                mock_filter.all.return_value = [conn_a, conn_b, conn_c]
                mock_query.filter.return_value = mock_filter

                # Test using Authorization: Bearer header
                res = client.post(
                    '/api/gmail/cron/renew',
                    headers={'Authorization': f'Bearer {TEST_CRON_SECRET}'}
                )
                assert res.status_code == 200
                data = res.get_json()

                assert data.get('success') is True
                assert data.get('total_eligible') == 3
                assert data.get('renewed') == 3
                assert data.get('failed') == 0
                assert data.get('failures') == []

                # Verify each user's watch was renewed with correct topic
                mock_service_a.start_watch.assert_called_once_with(VALID_TOPIC)
                mock_service_b.start_watch.assert_called_once_with(VALID_TOPIC)
                mock_service_c.start_watch.assert_called_once_with(VALID_TOPIC)

                # Verify state mutations on connections
                assert conn_a.monitoring_status == 'active'
                assert conn_a.watch_expiration == 1744384000000
                assert conn_a.history_id == 'hist-a-new'

                assert conn_b.monitoring_status == 'active'
                assert conn_b.watch_expiration == 1744384000000
                assert conn_b.history_id == 'hist-b-new'

                assert conn_c.monitoring_status == 'active'
                assert conn_c.watch_expiration == 1744384000000
                assert conn_c.history_id == 'hist-c-new'

                # Verify credential persistence check was called for all 3 users
                assert mock_persist.call_count == 3
                mock_commit.assert_called_once()


# =========================================================================
# 4. RENEWAL FAILURES & ERROR REPORTING TESTS
# =========================================================================

def test_cron_renew_reports_failures_clearly_when_all_fail():
    """
    When all renewals fail (e.g. Google API error), returns HTTP 500 with success=False
    and detailed failure information, rather than silently claiming success.
    """
    user_id = 'user-uuid-fail'
    conn = MagicMock(
        user_id=user_id,
        gmail_address='failing_user@example.com',
        monitoring_status='active',
        encrypted_credentials_json='enc-fail',
        watch_expiration=1700000000000
    )

    mock_service = MagicMock()
    mock_service.is_connected.return_value = True
    mock_service.start_watch.side_effect = Exception("403 Forbidden: Gmail API watch quota exceeded")

    with app.app_context():
        with app.test_client() as client:
            with patch.object(GmailConnection, 'query') as mock_query, \
                 patch('app.get_user_gmail_service', return_value=(mock_service, conn)), \
                 patch.object(db.session, 'commit') as mock_commit:

                mock_filter = MagicMock()
                mock_filter.all.return_value = [conn]
                mock_query.filter.return_value = mock_filter

                res = client.post(
                    '/api/gmail/cron/renew',
                    headers={'X-Cron-Secret': TEST_CRON_SECRET}
                )
                assert res.status_code == 500
                data = res.get_json()

                # Must not silently appear successful
                assert data.get('success') is False
                assert data.get('total_eligible') == 1
                assert data.get('renewed') == 0
                assert data.get('failed') == 1
                assert len(data.get('failures')) == 1
                assert "403 Forbidden" in data['failures'][0]['error']
                assert data['failures'][0]['user_id'] == user_id

                # Connection must be marked as failed
                assert conn.monitoring_status == 'failed'
                mock_commit.assert_called_once()


def test_cron_renew_partial_success_reports_both_successes_and_failures():
    """
    When one user succeeds and another fails, returns HTTP 207 (Multi-Status)
    with success=False, partial_success=True, and failure breakdown.
    """
    user_good_id = 'user-good'
    user_bad_id = 'user-bad'

    conn_good = MagicMock(user_id=user_good_id, gmail_address='good@ex.com', monitoring_status='active')
    conn_bad = MagicMock(user_id=user_bad_id, gmail_address='bad@ex.com', monitoring_status='active')

    mock_service_good = MagicMock()
    mock_service_good.is_connected.return_value = True
    mock_service_good.start_watch.return_value = {'historyId': 'hist-good', 'expiration': '1744384000000'}

    mock_service_bad = MagicMock()
    mock_service_bad.is_connected.return_value = False  # disconnected / revoked credentials

    def fake_get_service(uid):
        if uid == user_good_id:
            return mock_service_good, conn_good
        return mock_service_bad, conn_bad

    with app.app_context():
        with app.test_client() as client:
            with patch.object(GmailConnection, 'query') as mock_query, \
                 patch('app.get_user_gmail_service', side_effect=fake_get_service), \
                 patch.object(db.session, 'commit'):

                mock_filter = MagicMock()
                mock_filter.all.return_value = [conn_good, conn_bad]
                mock_query.filter.return_value = mock_filter

                res = client.post(f'/api/gmail/cron/renew?secret={TEST_CRON_SECRET}')
                assert res.status_code == 207
                data = res.get_json()

                assert data.get('success') is False
                assert data.get('partial_success') is True
                assert data.get('total_eligible') == 2
                assert data.get('renewed') == 1
                assert data.get('failed') == 1
                assert len(data.get('failures')) == 1
                assert data['failures'][0]['user_id'] == user_bad_id
                assert "disconnected" in data['failures'][0]['error'].lower()

                assert conn_good.monitoring_status == 'active'
                assert conn_bad.monitoring_status == 'failed'


# =========================================================================
# 5. USER-INITIATED RENEWAL ENDPOINT: POST /api/gmail/renew-watch
# =========================================================================

def test_user_renew_watch_unauthenticated_rejected():
    """POST /api/gmail/renew-watch must reject unauthenticated requests with 401."""
    with app.test_client() as client:
        res = client.post('/api/gmail/renew-watch')
        assert res.status_code == 401


def test_user_renew_watch_success():
    """Authenticated user successfully renews watch and updates database."""
    token, user_id = make_auth_token()
    headers = {'Authorization': f'Bearer {token}'}

    conn = MagicMock(user_id=user_id, monitoring_status='inactive', watch_expiration=None)
    mock_service = MagicMock()
    mock_service.is_connected.return_value = True
    mock_service.start_watch.return_value = {'historyId': 'hist-manual-123', 'expiration': '1744384000000'}

    with app.app_context():
        with app.test_client() as client:
            with patch('app.get_user_gmail_service', return_value=(mock_service, conn)), \
                 patch('app.persist_credentials_if_refreshed') as mock_persist, \
                 patch.object(db.session, 'commit') as mock_commit:

                res = client.post('/api/gmail/renew-watch', headers=headers)
                assert res.status_code == 200
                data = res.get_json()

                assert data.get('success') is True
                assert data.get('historyId') == 'hist-manual-123'
                assert data.get('expiration') == 1744384000000

                assert conn.monitoring_status == 'active'
                assert conn.watch_expiration == 1744384000000
                assert conn.history_id == 'hist-manual-123'
                mock_persist.assert_called_once()
                mock_commit.assert_called_once()


def test_user_renew_watch_failure_reports_clear_error():
    """Failure during user renewal marks status as failed and returns 400 with message."""
    token, user_id = make_auth_token()
    headers = {'Authorization': f'Bearer {token}'}

    conn = MagicMock(user_id=user_id, monitoring_status='active', watch_expiration=1700000000000)
    mock_service = MagicMock()
    mock_service.is_connected.return_value = True
    mock_service.start_watch.side_effect = Exception("Google Cloud PubSub topic access denied")

    with app.app_context():
        with app.test_client() as client:
            with patch('app.get_user_gmail_service', return_value=(mock_service, conn)), \
                 patch.object(db.session, 'commit') as mock_commit:

                res = client.post('/api/gmail/renew-watch', headers=headers)
                assert res.status_code == 400
                data = res.get_json()

                assert "Failed to renew Gmail watch" in data.get('error', '')
                assert "access denied" in data.get('error', '')
                assert conn.monitoring_status == 'failed'
                mock_commit.assert_called_once()


# =========================================================================
# 6. PASSIVE RENEWAL IN GET /api/gmail/latest
# =========================================================================

def test_latest_passive_renewal_triggers_when_expiration_near():
    """
    When watch expiration is less than 24 hours (86,400,000 ms) away,
    GET /api/gmail/latest passively triggers renewal and persists credentials.
    """
    token, user_id = make_auth_token()
    headers = {'Authorization': f'Bearer {token}'}

    now_ms = int(time.time() * 1000)
    # Expiration is in 2 hours (< 24 hours)
    expiring_soon_ms = now_ms + (2 * 3600 * 1000)

    conn = MagicMock(
        user_id=user_id,
        monitoring_status='active',
        watch_expiration=expiring_soon_ms,
        history_id='old-hist'
    )
    mock_service = MagicMock()
    mock_service.is_connected.return_value = True
    mock_service.start_watch.return_value = {'historyId': 'new-passive-hist', 'expiration': '1744384000000'}

    with app.app_context():
        with app.test_client() as client:
            with patch('app.get_user_gmail_service', return_value=(mock_service, conn)), \
                 patch('app.persist_credentials_if_refreshed') as mock_persist, \
                 patch('app.ingest_new_emails_for_user'), \
                 patch.object(ClassifiedEmail, 'query') as mock_email_query, \
                 patch.object(db.session, 'commit') as mock_commit:

                mock_filter = MagicMock()
                mock_order = MagicMock()
                mock_limit = MagicMock()
                mock_limit.all.return_value = []
                mock_email_query.filter_by.return_value = mock_filter
                mock_filter.order_by.return_value = mock_order
                mock_order.limit.return_value = mock_limit

                res = client.get('/api/gmail/latest', headers=headers)
                assert res.status_code == 200

                # Passive renewal should have triggered
                mock_service.start_watch.assert_called_once_with(VALID_TOPIC)
                mock_persist.assert_called_once()
                assert conn.watch_expiration == 1744384000000
                assert conn.history_id == 'new-passive-hist'
                mock_commit.assert_called()


# =========================================================================
# 7. TRANSIENT RETRY STRATEGY & PERMANENT ERROR SAFEGUARD TESTS
# =========================================================================

def _make_http_error(status_code, reason="Error"):
    from googleapiclient.errors import HttpError
    from unittest.mock import Mock
    mock_resp = Mock()
    mock_resp.status = status_code
    mock_resp.reason = reason
    return HttpError(mock_resp, b'{"error": "mock_error"}')


def test_is_transient_gmail_error_classification():
    """Verify that transient HTTP statuses and network exceptions are retryable, and permanent ones are not."""
    import socket
    import ssl
    from services.gmail_service import is_transient_gmail_error

    # Retryable HTTP status codes
    for status in [429, 500, 502, 503, 504]:
        err = _make_http_error(status)
        assert is_transient_gmail_error(err) is True, f"HTTP {status} must be classified as transient"

    # Non-retryable HTTP status codes
    for status in [400, 401, 403, 404]:
        err = _make_http_error(status)
        assert is_transient_gmail_error(err) is False, f"HTTP {status} must be classified as non-retryable permanent error"

    # Supported network/timeout exceptions
    assert is_transient_gmail_error(socket.timeout("Socket timed out")) is True
    assert is_transient_gmail_error(TimeoutError("Operation timed out")) is True
    assert is_transient_gmail_error(ConnectionResetError("Connection reset by peer")) is True
    assert is_transient_gmail_error(ssl.SSLError("SSL handshake error")) is True

    # Generic string checks
    assert is_transient_gmail_error(Exception("503 Backend Error")) is True
    assert is_transient_gmail_error(Exception("403 Forbidden: insufficient permissions")) is False


def test_start_watch_retries_transient_error_and_succeeds():
    """start_watch must retry up to 2 times for transient errors with bounded backoff and succeed."""
    from services.gmail_service import GmailService

    service_instance = GmailService()
    service_instance.creds = MagicMock()
    service_instance.is_connected = MagicMock(return_value=True)

    mock_execute = MagicMock()
    transient_err = _make_http_error(503, "Backend Error")
    success_resp = {'historyId': 'hist-recovered', 'expiration': '1744384000000'}
    # 1st call fails with 503, 2nd call succeeds
    mock_execute.side_effect = [transient_err, success_resp]

    mock_watch = MagicMock()
    mock_watch.execute = mock_execute
    mock_users = MagicMock()
    mock_users.watch.return_value = mock_watch
    mock_api = MagicMock()
    mock_api.users.return_value = mock_users

    sleep_calls = []
    fake_sleep = lambda delay: sleep_calls.append(delay)

    with patch('services.gmail_service.build', return_value=mock_api):
        res = service_instance.start_watch(
            VALID_TOPIC,
            max_retries=2,
            initial_backoff=0.2,
            sleep_fn=fake_sleep
        )

        assert res == success_resp
        assert mock_execute.call_count == 2
        assert len(sleep_calls) == 1
        # Bounded backoff with jitter: around 0.2 + jitter
        assert 0.1 <= sleep_calls[0] <= 1.0


def test_start_watch_permanent_error_fails_immediately_without_retry():
    """start_watch must NOT retry permanent errors (e.g. 403 Forbidden) and must fail on the 1st attempt."""
    from services.gmail_service import GmailService
    from googleapiclient.errors import HttpError

    service_instance = GmailService()
    service_instance.creds = MagicMock()
    service_instance.is_connected = MagicMock(return_value=True)

    mock_execute = MagicMock()
    perm_err = _make_http_error(403, "Forbidden")
    mock_execute.side_effect = perm_err

    mock_watch = MagicMock()
    mock_watch.execute = mock_execute
    mock_users = MagicMock()
    mock_users.watch.return_value = mock_watch
    mock_api = MagicMock()
    mock_api.users.return_value = mock_users

    sleep_calls = []
    fake_sleep = lambda delay: sleep_calls.append(delay)

    with patch('services.gmail_service.build', return_value=mock_api):
        with pytest.raises(HttpError) as exc_info:
            service_instance.start_watch(
                VALID_TOPIC,
                max_retries=2,
                sleep_fn=fake_sleep
            )

        assert exc_info.value.resp.status == 403
        assert mock_execute.call_count == 1
        assert len(sleep_calls) == 0  # Zero retries, zero sleep calls


def test_start_watch_exhausted_retries_raises_after_max_attempts():
    """start_watch must attempt at most 3 times (1 initial + 2 retries) when transient errors persist."""
    from services.gmail_service import GmailService
    from googleapiclient.errors import HttpError

    service_instance = GmailService()
    service_instance.creds = MagicMock()
    service_instance.is_connected = MagicMock(return_value=True)

    mock_execute = MagicMock()
    transient_500 = _make_http_error(500, "Internal Server Error")
    mock_execute.side_effect = transient_500

    mock_watch = MagicMock()
    mock_watch.execute = mock_execute
    mock_users = MagicMock()
    mock_users.watch.return_value = mock_watch
    mock_api = MagicMock()
    mock_api.users.return_value = mock_users

    sleep_calls = []
    fake_sleep = lambda delay: sleep_calls.append(delay)

    with patch('services.gmail_service.build', return_value=mock_api):
        with pytest.raises(HttpError) as exc_info:
            service_instance.start_watch(
                VALID_TOPIC,
                max_retries=2,
                initial_backoff=0.1,
                sleep_fn=fake_sleep
            )

        assert exc_info.value.resp.status == 500
        # 1 initial + 2 retries = 3 calls total
        assert mock_execute.call_count == 3
        assert len(sleep_calls) == 2


def test_cron_renew_multi_user_isolation_with_transient_and_permanent_failures():
    """
    Verify multi-user isolation during cron renewal when:
    - User A succeeds after a transient retry
    - User B fails on a permanent error
    - User C succeeds immediately on first attempt
    Returns HTTP 207 Multi-Status, records user B failure without impacting A and C.
    """
    user_a_id = 'user-uuid-transient'
    user_b_id = 'user-uuid-permanent'
    user_c_id = 'user-uuid-clean'

    conn_a = MagicMock(user_id=user_a_id, gmail_address='transient@ex.com', monitoring_status='failed', watch_expiration=None)
    conn_b = MagicMock(user_id=user_b_id, gmail_address='permanent@ex.com', monitoring_status='active', watch_expiration=1700000000000)
    conn_c = MagicMock(user_id=user_c_id, gmail_address='clean@ex.com', monitoring_status='active', watch_expiration=1700000000000)

    mock_service_a = MagicMock()
    mock_service_a.is_connected.return_value = True
    # User A succeeds
    mock_service_a.start_watch.return_value = {'historyId': 'hist-a', 'expiration': '1744384000000'}

    mock_service_b = MagicMock()
    mock_service_b.is_connected.return_value = True
    # User B encounters permanent failure
    mock_service_b.start_watch.side_effect = Exception("403 Forbidden: OAuth scope revoked")

    mock_service_c = MagicMock()
    mock_service_c.is_connected.return_value = True
    # User C succeeds
    mock_service_c.start_watch.return_value = {'historyId': 'hist-c', 'expiration': '1744384000000'}

    def fake_get_service(uid):
        if uid == user_a_id:
            return mock_service_a, conn_a
        elif uid == user_b_id:
            return mock_service_b, conn_b
        elif uid == user_c_id:
            return mock_service_c, conn_c
        return None, None

    with app.app_context():
        with app.test_client() as client:
            with patch.object(GmailConnection, 'query') as mock_query, \
                 patch('app.get_user_gmail_service', side_effect=fake_get_service), \
                 patch('app.persist_credentials_if_refreshed') as mock_persist, \
                 patch.object(db.session, 'commit') as mock_commit:

                mock_filter = MagicMock()
                mock_filter.all.return_value = [conn_a, conn_b, conn_c]
                mock_query.filter.return_value = mock_filter

                res = client.post(
                    '/api/gmail/cron/renew',
                    headers={'Authorization': f'Bearer {TEST_CRON_SECRET}'}
                )

                assert res.status_code == 207
                data = res.get_json()

                assert data.get('success') is False
                assert data.get('partial_success') is True
                assert data.get('total_eligible') == 3
                assert data.get('renewed') == 2
                assert data.get('failed') == 1

                # User A recovered to active
                assert conn_a.monitoring_status == 'active'
                assert conn_a.watch_expiration == 1744384000000
                assert conn_a.history_id == 'hist-a'

                # User B marked as failed
                assert conn_b.monitoring_status == 'failed'

                # User C remained active
                assert conn_c.monitoring_status == 'active'
                assert conn_c.watch_expiration == 1744384000000
                assert conn_c.history_id == 'hist-c'

                # Verify persistence and commit were called
                assert mock_persist.call_count == 2  # for users A and C
                mock_commit.assert_called_once()


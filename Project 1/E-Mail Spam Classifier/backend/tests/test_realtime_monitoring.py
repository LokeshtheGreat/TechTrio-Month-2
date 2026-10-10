import os
import sys
import uuid
import time
import json
import base64
import pytest
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
import jwt

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, ingest_new_emails_for_user
from models import User, GmailConnection, ClassifiedEmail
from services.gmail_service import GmailService
from utils.encryption import encrypt_credentials

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
    monkeypatch.setenv('PUBSUB_VERIFICATION_TOKEN', 'test-pubsub-token-xyz')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dummy:dummy@localhost:5432/testdb'


def test_latest_emails_orders_newest_first_regardless_of_insertion():
    """
    Verify that /api/gmail/latest always returns emails in newest-first order
    based on the actual message timestamp/internal_date, fixing the inversion regression.
    """
    token, user_id = make_auth_token()
    headers = {'Authorization': f'Bearer {token}'}

    with app.app_context():
        with app.test_client() as client:
            mock_service = MagicMock()
            mock_service.is_connected.return_value = True
            mock_conn = MagicMock(
                user_id=user_id,
                monitoring_status='inactive',
                watch_expiration=None,
                history_id='100'
            )

            mock_r1 = MagicMock(
                message_id='msg-newest',
                sender='a@ex.com',
                subject='Newest',
                snippet='newest',
                body='Body 1',
                body_html='<p>Body 1</p>',
                prediction='HAM',
                strength='Strong',
                timestamp='Sat, 10 Oct 2026 12:00:00 +0000',
                internal_date=1728550000000,
                spam_indicators='[]',
                created_at=None
            )
            mock_r2 = MagicMock(
                message_id='msg-middle',
                sender='b@ex.com',
                subject='Middle',
                snippet='middle',
                body='Body 2',
                body_html='<p>Body 2</p>',
                prediction='HAM',
                strength='Moderate',
                timestamp='Fri, 9 Oct 2026 12:00:00 +0000',
                internal_date=1728500000000,
                spam_indicators='[]',
                created_at=None
            )
            mock_r3 = MagicMock(
                message_id='msg-oldest',
                sender='c@ex.com',
                subject='Oldest',
                snippet='oldest',
                body='Body 3',
                body_html='<p>Body 3</p>',
                prediction='SPAM',
                strength='Strong',
                timestamp='Thu, 8 Oct 2026 12:00:00 +0000',
                internal_date=1728400000000,
                spam_indicators='[]',
                created_at=None
            )

            with patch('app.get_user_gmail_service', return_value=(mock_service, mock_conn)), \
                 patch.object(ClassifiedEmail, 'query') as mock_query:

                mock_filter = MagicMock()
                mock_order = MagicMock()
                mock_limit = MagicMock()
                mock_limit.all.return_value = [mock_r3, mock_r1, mock_r2]  # returned out of order

                mock_query.filter_by.return_value = mock_filter
                mock_filter.order_by.return_value = mock_order
                mock_order.limit.return_value = mock_limit

                res = client.get('/api/gmail/latest', headers=headers)
                assert res.status_code == 200
                data = res.get_json()
                emails = data['emails']

                assert len(emails) == 3
                assert emails[0]['id'] == 'msg-newest'
                assert emails[1]['id'] == 'msg-middle'
                assert emails[2]['id'] == 'msg-oldest'


def test_latest_emails_rich_payload_serialization():
    """
    Verify /api/gmail/latest provides body, body_html, and parsed spam_indicators list,
    preventing email rendering breakage when monitoring is active.
    """
    token, user_id = make_auth_token()
    headers = {'Authorization': f'Bearer {token}'}

    with app.app_context():
        with app.test_client() as client:
            mock_service = MagicMock()
            mock_service.is_connected.return_value = True
            mock_conn = MagicMock(
                user_id=user_id,
                monitoring_status='inactive',
                watch_expiration=None,
                history_id='100'
            )

            indicators = [{'term': 'free', 'weight': 2.5}, {'term': 'prize', 'weight': 1.8}]
            mock_record = MagicMock(
                message_id='msg-rich-1',
                sender='sender@test.com',
                subject='Special Offer',
                snippet='Click here for your prize...',
                body='Plain text version of email',
                body_html='<div style="font-family:sans-serif"><h1>Exclusive Offer</h1><img src="test.jpg" /></div>',
                prediction='SPAM',
                strength='Strong',
                timestamp='Sat, 10 Oct 2026 14:00:00 +0000',
                internal_date=1728560000000,
                spam_indicators=json.dumps(indicators),
                created_at=None
            )

            with patch('app.get_user_gmail_service', return_value=(mock_service, mock_conn)), \
                 patch.object(ClassifiedEmail, 'query') as mock_query:

                mock_filter = MagicMock()
                mock_order = MagicMock()
                mock_limit = MagicMock()
                mock_limit.all.return_value = [mock_record]

                mock_query.filter_by.return_value = mock_filter
                mock_filter.order_by.return_value = mock_order
                mock_order.limit.return_value = mock_limit

                res = client.get('/api/gmail/latest', headers=headers)
                assert res.status_code == 200
                emails = res.get_json()['emails']

                assert len(emails) == 1
                e = emails[0]
                assert e['body'] == 'Plain text version of email'
                assert '<div style="font-family:sans-serif">' in e['body_html']
                assert isinstance(e['spam_indicators'], list)
                assert len(e['spam_indicators']) == 2
                assert e['spam_indicators'][0]['term'] == 'free'


def test_ingest_new_emails_processes_only_new_changes():
    """
    Verify that ingest_new_emails_for_user queries Gmail history checkpoint,
    classifies only new messages, stores rich payload, and updates history checkpoint.
    """
    mock_conn = MagicMock()
    mock_conn.user_id = str(uuid.uuid4())
    mock_conn.history_id = '300000'

    mock_service = MagicMock()
    mock_service.is_connected.return_value = True
    mock_service.fetch_history.return_value = (['new-msg-456'], '300050')
    mock_service.fetch_message_by_id.return_value = {
        'id': 'new-msg-456',
        'sender': 'boss@work.com',
        'subject': 'Project Update',
        'snippet': 'Please review the attached project schedule.',
        'body': 'Please review the attached project schedule.',
        'body_html': '<p>Please review the attached project schedule.</p>',
        'timestamp': 'Sat, 10 Oct 2026 14:30:00 +0000',
        'internal_date': 1728561000000
    }

    with app.app_context():
        with patch.object(ClassifiedEmail, 'query') as mock_query, \
             patch('app.db.session') as mock_session:

            mock_query.filter_by.return_value.first.return_value = None

            count = ingest_new_emails_for_user(mock_conn, mock_service, force=True)

            assert count == 1
            assert mock_conn.history_id == '300050'
            assert mock_session.add.called
            added_record = mock_session.add.call_args[0][0]
            assert added_record.message_id == 'new-msg-456'
            assert added_record.body_html == '<p>Please review the attached project schedule.</p>'
            assert added_record.internal_date == 1728561000000
            assert mock_session.commit.called


def test_ingest_new_emails_deduplication_and_retry_safety():
    """
    Verify that if a message ID is already stored (retry / duplicate notification),
    ingestion skips it without creating a duplicate record.
    """
    mock_conn = MagicMock()
    mock_conn.user_id = str(uuid.uuid4())
    mock_conn.history_id = '300000'

    mock_service = MagicMock()
    mock_service.is_connected.return_value = True
    mock_service.fetch_history.return_value = (['existing-msg-789'], '300050')

    with app.app_context():
        with patch.object(ClassifiedEmail, 'query') as mock_query, \
             patch('app.db.session') as mock_session:

            mock_query.filter_by.return_value.first.return_value = MagicMock(message_id='existing-msg-789')

            count = ingest_new_emails_for_user(mock_conn, mock_service, force=True)

            assert count == 0
            assert not mock_service.fetch_message_by_id.called
            assert not mock_session.add.called
            assert mock_conn.history_id == '300050'


def test_user_isolation_in_latest_emails():
    """
    Verify that User A cannot see User B's classified emails.
    """
    token_a, user_a_id = make_auth_token(email="usera@test.com")
    token_b, user_b_id = make_auth_token(email="userb@test.com")

    headers_b = {'Authorization': f'Bearer {token_b}'}

    with app.app_context():
        with app.test_client() as client:
            mock_service_b = MagicMock()
            mock_service_b.is_connected.return_value = True
            mock_conn_b = MagicMock(user_id=user_b_id, monitoring_status='inactive', watch_expiration=None)

            with patch('app.get_user_gmail_service', return_value=(mock_service_b, mock_conn_b)), \
                 patch.object(ClassifiedEmail, 'query') as mock_query:

                mock_filter = MagicMock()
                mock_order = MagicMock()
                mock_limit = MagicMock()
                mock_limit.all.return_value = []

                mock_query.filter_by.return_value = mock_filter
                mock_filter.order_by.return_value = mock_order
                mock_order.limit.return_value = mock_limit

                res_b = client.get('/api/gmail/latest', headers=headers_b)
                assert res_b.status_code == 200
                assert len(res_b.get_json()['emails']) == 0

                mock_query.filter_by.assert_called_with(user_id=user_b_id)


def test_pubsub_webhook_token_verification_and_unauthorized_rejection():
    """
    Verify that /api/gmail/pubsub enforces PUBSUB_VERIFICATION_TOKEN when configured:
    - 401 when token is missing or mismatched
    - 200 and calls ingestion when token matches
    """
    with app.app_context():
        with app.test_client() as client:
            # 1. Missing token
            res1 = client.post('/api/gmail/pubsub', json={'message': {'data': 'abc'}})
            assert res1.status_code == 401

            # 2. Invalid token
            res2 = client.post('/api/gmail/pubsub?token=wrong-token', json={'message': {'data': 'abc'}})
            assert res2.status_code == 401

            # 3. Valid token with valid Pub/Sub message
            fake_pubsub_data = json.dumps({'emailAddress': 'test@gmail.com', 'historyId': '55555'})
            b64_data = base64.b64encode(fake_pubsub_data.encode('utf-8')).decode('utf-8')

            with patch('app.GmailConnection.query') as mock_conn_query, \
                 patch('app.get_user_gmail_service') as mock_get_svc, \
                 patch('app.ingest_new_emails_for_user') as mock_ingest:

                mock_conn = MagicMock(user_id='uid-123')
                mock_conn_query.filter_by.return_value.first.return_value = mock_conn
                mock_svc = MagicMock()
                mock_svc.is_connected.return_value = True
                mock_get_svc.return_value = (mock_svc, mock_conn)

                res3 = client.post(
                    '/api/gmail/pubsub?token=test-pubsub-token-xyz',
                    json={'message': {'data': b64_data}}
                )
                assert res3.status_code == 200
                assert mock_ingest.called

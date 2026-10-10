from flask import Flask, request, jsonify, redirect, session, g
from flask_cors import CORS
import sys
import uuid
import urllib.parse
from datetime import datetime
from flask_jwt_extended import JWTManager
from models import db, User, GmailConnection, ClassifiedEmail
from flask_migrate import Migrate
from routes.auth import auth_bp
from utils.supabase_auth import require_supabase_auth
from utils.encryption import encrypt_credentials, decrypt_credentials, generate_oauth_state, verify_oauth_state

from services.classifier import SpamClassifier
from services.gmail_service import GmailService
import os
import json
import time
import base64
try:
    from dotenv import load_dotenv
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        load_dotenv()
except ImportError:
    pass


app = Flask(__name__)
# Enable CORS for all routes, allowing credentials if needed.
CORS(app, supports_credentials=True)

# Database Configuration (PostgreSQL only - SQLite is strictly prohibited)
def configure_database(app_instance, db_url=None):
    raw_url = db_url or os.environ.get('DATABASE_URL')
    if not raw_url:
        app_instance.config['SQLALCHEMY_DATABASE_URI'] = None
        return False
    if 'sqlite' in raw_url.lower():
        raise ValueError("SQLite is not supported. PostgreSQL is strictly required.")
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    app_instance.config['SQLALCHEMY_DATABASE_URI'] = raw_url
    return True

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'fallback-dev-key')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'fallback-flask-key')

has_database = configure_database(app)
if has_database:
    db.init_app(app)

migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
migrate = Migrate(app, db, directory=migrations_dir)

jwt = JWTManager(app)

@app.before_request
def check_database_availability():
    if request.endpoint and request.endpoint.startswith('auth.'):
        if not app.config.get('SQLALCHEMY_DATABASE_URI'):
            return jsonify({
                "error": "Database not configured. PostgreSQL DATABASE_URL is required."
            }), 503

app.register_blueprint(auth_bp, url_prefix='/api/auth')

classifier = SpamClassifier()
# Note: gmail_service singleton is deprecated and will be removed in Stage 2. 
# Keeping it temporarily to avoid instantly breaking the existing endpoints during Stage 1 setup.
gmail_service = GmailService()

# Global state for Live Monitor
monitoring_state = {
    'monitoring': False,
    'historyId': None,
    'expiration': None,
    'renewal_status': 'active', # active, renewing, failed
    'emails': []
}


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "Email Spam Shield backend is running."}), 200

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "No message provided"}), 400

    message = data['message']
    result = classifier.predict(message)
    return jsonify(result), 200

@app.route('/api/stats', methods=['GET'])
def stats():
    # Return static stats from PRD for now, but in reality we might want to blend these.
    # The PRD requires Phase 4A to calculate stats dynamically from fetched emails in Live Monitor.
    # We will let the frontend calculate total/spam/ham for the live monitor.
    return jsonify({
        "uci_performance": {
            "accuracy": "98.35%",
            "precision": 0.94,
            "recall": 0.92,
            "f1": 0.93,
            "false_positives": 7,
            "false_negatives": 10
        },
        "indian_performance": {
            "accuracy": "98.54%",
            "precision": 0.97,
            "recall": 0.99,
            "f1": 0.98,
            "false_positives": 5,
            "false_negatives": 1
        }
    }), 200

# ---- GMAIL HELPERS & MULTI-USER SERVICES ----

def ensure_user_exists(user_id, email=None):
    """
    Ensures that the corresponding User row exists in PostgreSQL.
    Creates it if missing using user_id as PK, adhering to per-user isolation.
    """
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        return None
    user = User.query.get(user_id)
    if not user:
        user = User(
            id=user_id,
            email=email or f"{user_id}@supabase.auth"
        )
        db.session.add(user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            user = User.query.get(user_id)
    return user


def persist_credentials_if_refreshed(conn, service, initial_token=None):
    """
    Checks if GmailService automatically refreshed its OAuth tokens.
    If so, encrypts and persists the new credentials to PostgreSQL.
    """
    if not conn or not service or not service.is_connected():
        return
    updated_dict = service.get_credentials_dict()
    if updated_dict and updated_dict.get('token') and updated_dict.get('token') != initial_token:
        try:
            conn.encrypted_credentials_json = encrypt_credentials(updated_dict)
            conn.updated_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            print(f"Failed to persist refreshed credentials: {e}")
            db.session.rollback()


def get_user_gmail_service(user_id):
    """
    Retrieves and decrypts the Gmail credentials for user_id.
    Initializes a scoped GmailService instance for the user.
    Persists refreshed credentials if changed during initialization.
    Returns (service, conn).
    """
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        return None, None

    conn = GmailConnection.query.filter_by(user_id=user_id).first()
    if not conn or not conn.encrypted_credentials_json:
        return None, None

    try:
        creds_dict = decrypt_credentials(conn.encrypted_credentials_json)
        if not creds_dict:
            return None, conn
    except Exception as e:
        print(f"Error decrypting credentials for user {user_id}: {e}")
        return None, conn

    initial_token = creds_dict.get('token')
    service = GmailService(creds_dict)
    if not service.is_connected():
        return None, conn

    persist_credentials_if_refreshed(conn, service, initial_token)
    return service, conn


def get_backend_url():
    """
    Resolves the base backend URL for OAuth redirects and callbacks.
    Prioritizes BACKEND_URL, then RENDER_EXTERNAL_URL (automatically provided by Render),
    falling back to http://localhost:5000 for local development.
    Always strips trailing slashes to prevent malformed redirect URIs.
    """
    raw = os.environ.get('BACKEND_URL') or os.environ.get('RENDER_EXTERNAL_URL') or 'http://localhost:5000'
    return raw.strip().rstrip('/')


def get_frontend_url():
    """
    Resolves the base frontend URL for post-OAuth browser redirection.
    Prioritizes FRONTEND_URL, falling back to http://localhost:5173 for local development.
    Always strips trailing slashes.
    """
    raw = os.environ.get('FRONTEND_URL') or 'http://localhost:5173'
    return raw.strip().rstrip('/')


# ---- GMAIL ROUTES ----

@app.route('/api/gmail/status', methods=['GET'])
@require_supabase_auth
def gmail_status():
    service, conn = get_user_gmail_service(g.user_id)
    if service and service.is_connected():
        email = conn.gmail_address if (conn and conn.gmail_address) else service.get_profile()
        return jsonify({"connected": True, "email": email}), 200
    return jsonify({"connected": False}), 200


@app.route('/api/gmail/connect', methods=['GET'])
@require_supabase_auth
def gmail_connect():
    backend_url = get_backend_url()
    redirect_uri = f'{backend_url}/api/gmail/callback'
    try:
        import string, secrets
        chars = string.ascii_letters + string.digits + "-._~"
        code_verifier = ''.join(secrets.choice(chars) for _ in range(128))
        csrf_nonce = secrets.token_urlsafe(16)

        state = generate_oauth_state(user_id=g.user_id, csrf_nonce=csrf_nonce, code_verifier=code_verifier)
        session['oauth_state'] = state
        session['oauth_csrf'] = csrf_nonce
        session['oauth_user_id'] = g.user_id

        auth_url, _, _ = GmailService.get_auth_url(redirect_uri, state=state, code_verifier=code_verifier)

        if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({"auth_url": auth_url}), 200
        return redirect(auth_url)
    except Exception as e:
        return jsonify({"error": "Failed to initiate Gmail authorization."}), 400


@app.route('/api/gmail/callback', methods=['GET'])
def gmail_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    backend_url = get_backend_url()
    frontend_url = get_frontend_url()
    redirect_uri = f'{backend_url}/api/gmail/callback'

    if error:
        return redirect(f'{frontend_url}/?error=access_denied')

    if not code or not state:
        return jsonify({"error": "Missing authorization code or state parameter."}), 400

    expected_csrf = session.get('oauth_csrf')
    session_user_id = session.get('oauth_user_id')
    stored_state = session.get('oauth_state')

    if stored_state and stored_state != state:
        return jsonify({"error": "Invalid or mismatched OAuth state."}), 400

    try:
        state_data = verify_oauth_state(state, expected_csrf=expected_csrf, expected_user_id=session_user_id)
        user_id = state_data['user_id']
        code_verifier = state_data.get('code_verifier')

        tokens_dict = GmailService.exchange_code(code, redirect_uri, state=state, code_verifier=code_verifier)
        encrypted_creds = encrypt_credentials(tokens_dict)

        # Retrieve user's email address
        temp_service = GmailService(tokens_dict)
        gmail_address = temp_service.get_profile()

        if app.config.get('SQLALCHEMY_DATABASE_URI'):
            ensure_user_exists(user_id)

            # Handle unique constraint on gmail_address if re-linked to a new user record
            if gmail_address:
                existing_by_email = GmailConnection.query.filter_by(gmail_address=gmail_address).first()
                if existing_by_email and existing_by_email.user_id != user_id:
                    db.session.delete(existing_by_email)
                    db.session.flush()

            conn = GmailConnection.query.filter_by(user_id=user_id).first()
            if not conn:
                conn = GmailConnection(user_id=user_id)
                db.session.add(conn)

            conn.gmail_address = gmail_address
            conn.encrypted_credentials_json = encrypted_creds
            conn.updated_at = datetime.utcnow()
            db.session.commit()

        # Clean up session
        session.pop('oauth_state', None)
        session.pop('oauth_csrf', None)
        session.pop('oauth_user_id', None)

        return redirect(f'{frontend_url}/?gmail_connected=true')
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return jsonify({"error": "Failed to complete Gmail connection."}), 400


@app.route('/api/gmail/disconnect', methods=['POST'])
@require_supabase_auth
def gmail_disconnect():
    service, conn = get_user_gmail_service(g.user_id)
    if conn:
        try:
            if service:
                service.stop_watch()
        except Exception as e:
            print(f"Error stopping watch during disconnect for user {g.user_id}: {e}")

        db.session.delete(conn)
        db.session.commit()
    return jsonify({"success": True}), 200


@app.route('/api/gmail/sync', methods=['POST'])
@require_supabase_auth
def gmail_sync():
    service, conn = get_user_gmail_service(g.user_id)
    if not service or not service.is_connected():
        return jsonify({"error": "Not connected to Gmail"}), 401

    try:
        raw_emails = service.fetch_recent_emails(limit=20)
        persist_credentials_if_refreshed(conn, service)

        # Classify each email
        for email in raw_emails:
            text_to_classify = email['body'] if email['body'] else email['subject'] + " " + email['snippet']
            try:
                prediction_result = classifier.predict(text_to_classify)
                email['prediction'] = prediction_result.get('prediction', 'UNKNOWN')
                email['classification_strength'] = prediction_result.get('strength', 'Unknown')
                email['spam_indicators'] = prediction_result.get('indicators', [])
            except Exception as e:
                print(f"Error classifying email {email['id']}: {e}")
                email['prediction'] = 'ERROR'
                email['classification_strength'] = 'None'
                email['spam_indicators'] = []

            # Persist classified email to database for this user
            if app.config.get('SQLALCHEMY_DATABASE_URI'):
                existing_email = ClassifiedEmail.query.filter_by(
                    user_id=g.user_id,
                    message_id=email['id']
                ).first()
                indicators_json = json.dumps(email.get('spam_indicators', []))
                if not existing_email:
                    new_email_record = ClassifiedEmail(
                        user_id=g.user_id,
                        message_id=email['id'],
                        sender=(email.get('sender') or '')[:255],
                        subject=email.get('subject') or '',
                        snippet=email.get('snippet') or '',
                        body=email.get('body') or '',
                        body_html=email.get('body_html') or '',
                        spam_indicators=indicators_json,
                        internal_date=email.get('internal_date'),
                        prediction=email.get('prediction') or '',
                        strength=email.get('classification_strength') or '',
                        timestamp=str(email.get('timestamp') or '')[:100]
                    )
                    db.session.add(new_email_record)
                else:
                    if not existing_email.body_html and email.get('body_html'):
                        existing_email.body_html = email.get('body_html')
                    if not existing_email.body and email.get('body'):
                        existing_email.body = email.get('body')
                    if not existing_email.spam_indicators and email.get('spam_indicators'):
                        existing_email.spam_indicators = indicators_json
                    if not existing_email.internal_date and email.get('internal_date'):
                        existing_email.internal_date = email.get('internal_date')

        if app.config.get('SQLALCHEMY_DATABASE_URI'):
            db.session.commit()

        return jsonify({"emails": raw_emails}), 200
    except Exception as e:
        return jsonify({"error": "Failed to synchronize emails."}), 500


@app.route('/api/gmail/watch', methods=['POST'])
@require_supabase_auth
def start_watch():
    service, conn = get_user_gmail_service(g.user_id)
    if not service or not service.is_connected():
        return jsonify({"error": "Not connected"}), 401

    topic = os.environ.get('PUBSUB_TOPIC_NAME')
    if not topic or 'dummy' in topic:
        return jsonify({"error": "PUBSUB_TOPIC_NAME environment variable is not configured for production."}), 500
    try:
        res = service.start_watch(topic)
        persist_credentials_if_refreshed(conn, service)
        conn.monitoring_status = 'active'
        conn.history_id = res.get('historyId')
        expiration = int(res.get('expiration', 0)) if res.get('expiration') else None
        conn.watch_expiration = expiration
        conn.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"success": True, "historyId": res.get('historyId'), "expiration": expiration}), 200
    except Exception as e:
        conn.monitoring_status = 'failed'
        db.session.commit()
        return jsonify({"error": "Failed to start Gmail watch."}), 400


@app.route('/api/gmail/stop-watch', methods=['POST'])
@require_supabase_auth
def stop_watch():
    service, conn = get_user_gmail_service(g.user_id)
    if not service or not service.is_connected():
        return jsonify({"error": "Not connected"}), 401
    try:
        service.stop_watch()
        conn.monitoring_status = 'inactive'
        conn.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": "Failed to stop Gmail watch."}), 500


@app.route('/api/gmail/renew-watch', methods=['POST'])
@require_supabase_auth
def renew_watch():
    service, conn = get_user_gmail_service(g.user_id)
    if not service or not service.is_connected():
        return jsonify({"error": "Not connected"}), 401
    topic = os.environ.get('PUBSUB_TOPIC_NAME')
    if not topic or 'dummy' in topic:
        return jsonify({"error": "PUBSUB_TOPIC_NAME environment variable is not configured for production."}), 500
    try:
        res = service.start_watch(topic)
        persist_credentials_if_refreshed(conn, service)
        conn.monitoring_status = 'active'
        conn.history_id = res.get('historyId')
        expiration = int(res.get('expiration', 0)) if res.get('expiration') else None
        conn.watch_expiration = expiration
        conn.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"success": True, "historyId": res.get('historyId'), "expiration": expiration}), 200
    except Exception as e:
        conn.monitoring_status = 'failed'
        db.session.commit()
        return jsonify({"error": "Failed to renew Gmail watch."}), 400


last_history_poll = {}

def ingest_new_emails_for_user(conn, service, target_history_id=None, force=False):
    """
    Ingests newly received emails for a user by querying Gmail History API.
    Used both by the Pub/Sub push webhook and by local automatic polling.
    Guarantees:
      - Only processes new changes since conn.history_id.
      - Extracts and stores rich payload (body, body_html, spam_indicators, internal_date).
      - Classifies new messages using SpamClassifier.
      - Deduplicates messages using message_id and unique constraints.
      - Updates conn.history_id safely.
      - Preserves per-user isolation.
    """
    if not conn or not service or not service.is_connected() or not conn.history_id:
        return 0

    user_id = conn.user_id
    now = time.time()

    # Throttle polling unless forced (e.g. Pub/Sub push notification or test)
    if not force and not target_history_id:
        last_time = last_history_poll.get(user_id, 0)
        if now - last_time < 3.0:
            return 0
    last_history_poll[user_id] = now

    start_history_id = conn.history_id
    new_msg_ids, new_history_id = service.fetch_history(start_history_id)

    # If history is outdated/expired or unavailable, update checkpoint if target provided
    if new_msg_ids is None:
        if target_history_id:
            conn.history_id = target_history_id
            conn.updated_at = datetime.utcnow()
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        return 0

    ingested_count = 0
    if new_msg_ids:
        for msg_id in new_msg_ids:
            # Deduplication: check if already in DB for this user
            existing = ClassifiedEmail.query.filter_by(user_id=user_id, message_id=msg_id).first()
            if existing:
                continue

            email_data = service.fetch_message_by_id(msg_id)
            if not email_data:
                continue

            text_to_classify = email_data.get('body') if email_data.get('body') else (email_data.get('subject', '') + " " + email_data.get('snippet', ''))
            try:
                prediction_result = classifier.predict(text_to_classify)
                email_data['prediction'] = prediction_result.get('prediction', 'UNKNOWN')
                email_data['classification_strength'] = prediction_result.get('strength', 'Unknown')
                email_data['spam_indicators'] = prediction_result.get('indicators', [])
            except Exception as e:
                print(f"Error classifying email {msg_id}: {e}")
                email_data['prediction'] = 'ERROR'
                email_data['classification_strength'] = 'None'
                email_data['spam_indicators'] = []

            indicators_json = json.dumps(email_data.get('spam_indicators', []))
            new_record = ClassifiedEmail(
                user_id=user_id,
                message_id=msg_id,
                sender=(email_data.get('sender') or '')[:255],
                subject=email_data.get('subject') or '',
                snippet=email_data.get('snippet') or '',
                body=email_data.get('body') or '',
                body_html=email_data.get('body_html') or '',
                spam_indicators=indicators_json,
                internal_date=email_data.get('internal_date'),
                prediction=email_data.get('prediction') or '',
                strength=email_data.get('classification_strength') or '',
                timestamp=str(email_data.get('timestamp') or '')[:100]
            )
            db.session.add(new_record)
            ingested_count += 1

    if new_history_id:
        conn.history_id = new_history_id
    elif target_history_id:
        conn.history_id = target_history_id

    conn.updated_at = datetime.utcnow()
    try:
        db.session.commit()
    except Exception as e:
        print(f"Database error during ingestion commit: {e}")
        db.session.rollback()

    return ingested_count


@app.route('/api/gmail/pubsub', methods=['POST'])
def pubsub_webhook():
    expected_token = os.environ.get('PUBSUB_VERIFICATION_TOKEN')
    if expected_token and request.args.get('token') != expected_token:
        return 'Unauthorized', 401

    data = request.get_json()
    if not data or 'message' not in data:
        return 'Bad Request', 400

    pubsub_message = data['message']
    if 'data' in pubsub_message:
        try:
            decoded_data = base64.b64decode(pubsub_message['data']).decode('utf-8')
            msg_data = json.loads(decoded_data)
            email_address = msg_data.get('emailAddress')
            history_id = msg_data.get('historyId')

            if email_address and app.config.get('SQLALCHEMY_DATABASE_URI'):
                conn = GmailConnection.query.filter_by(gmail_address=email_address).first()
                if conn:
                    service, _ = get_user_gmail_service(conn.user_id)
                    if service and service.is_connected():
                        ingest_new_emails_for_user(conn, service, target_history_id=history_id, force=True)
        except Exception as e:
            print(f"Error processing pubsub message: {e}")

    return '', 200


@app.route('/api/gmail/latest', methods=['GET'])
@require_supabase_auth
def get_latest_emails():
    service, conn = get_user_gmail_service(g.user_id)
    current_time_ms = int(time.time() * 1000)

    if not conn:
        return jsonify({
            "monitoring": False,
            "expiration": None,
            "renewal_status": 'inactive',
            "emails": [],
            "current_time": current_time_ms
        }), 200

    # If monitoring is active, trigger automatic ingestion of new incoming emails
    if conn.monitoring_status == 'active' and service and service.is_connected() and conn.history_id:
        try:
            ingest_new_emails_for_user(conn, service)
        except Exception as e:
            print(f"Error during polling ingestion for user {g.user_id}: {e}")

    if conn.monitoring_status == 'active' and conn.watch_expiration:
        time_left_ms = conn.watch_expiration - current_time_ms
        if time_left_ms < 86400000 and service:
            topic = os.environ.get('PUBSUB_TOPIC_NAME')
            if topic and 'dummy' not in topic:
                try:
                    res = service.start_watch(topic)
                    conn.watch_expiration = int(res.get('expiration', 0)) if res.get('expiration') else None
                    conn.history_id = res.get('historyId')
                    conn.monitoring_status = 'active'
                    conn.updated_at = datetime.utcnow()
                    db.session.commit()
                except Exception as e:
                    print(f"Auto-renewal failed for user {g.user_id}: {e}")
                    conn.monitoring_status = 'failed'
                    db.session.commit()

    records = ClassifiedEmail.query.filter_by(user_id=g.user_id).order_by(
        ClassifiedEmail.internal_date.desc().nullslast(),
        ClassifiedEmail.created_at.desc()
    ).limit(50).all()

    # Robust python fallback sort to ensure newest is always first even for legacy rows without internal_date
    def get_sort_timestamp(r):
        if r.internal_date:
            return r.internal_date
        if r.timestamp:
            try:
                import email.utils
                return int(email.utils.parsedate_to_datetime(r.timestamp).timestamp() * 1000)
            except Exception:
                pass
        if r.created_at:
            return int(r.created_at.timestamp() * 1000)
        return 0

    sorted_records = sorted(records, key=get_sort_timestamp, reverse=True)

    user_emails = []
    for r in sorted_records:
        indicators = []
        if r.spam_indicators:
            try:
                indicators = json.loads(r.spam_indicators)
            except Exception:
                indicators = []

        user_emails.append({
            'id': r.message_id,
            'sender': r.sender,
            'subject': r.subject,
            'snippet': r.snippet,
            'body': r.body or '',
            'body_html': r.body_html or '',
            'prediction': r.prediction,
            'classification_strength': r.strength,
            'timestamp': r.timestamp,
            'spam_indicators': indicators
        })

    return jsonify({
        "monitoring": conn.monitoring_status == 'active',
        "expiration": conn.watch_expiration,
        "renewal_status": conn.monitoring_status,
        "emails": user_emails,
        "current_time": current_time_ms
    }), 200


@app.route('/api/gmail/cron/renew', methods=['POST', 'GET'])
def cron_renew_watch():
    expected_secret = os.environ.get('CRON_SECRET')
    if expected_secret and request.args.get('secret') != expected_secret:
        return jsonify({"error": "Unauthorized"}), 401

    topic = os.environ.get('PUBSUB_TOPIC_NAME')
    if not topic or 'dummy' in topic:
        return jsonify({"error": "PUBSUB_TOPIC_NAME environment variable is not configured for production."}), 500

    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        return jsonify({"error": "Database not configured."}), 503

    active_conns = GmailConnection.query.filter_by(monitoring_status='active').all()
    renewed_count = 0
    for conn in active_conns:
        service, _ = get_user_gmail_service(conn.user_id)
        if service and service.is_connected():
            try:
                res = service.start_watch(topic)
                conn.watch_expiration = int(res.get('expiration', 0)) if res.get('expiration') else None
                conn.history_id = res.get('historyId')
                renewed_count += 1
            except Exception as e:
                print(f"Cron renewal failed for user {conn.user_id}: {e}")
                conn.monitoring_status = 'failed'
    db.session.commit()
    return jsonify({"success": True, "renewed": renewed_count}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

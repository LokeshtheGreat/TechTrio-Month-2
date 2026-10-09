from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
from services.classifier import SpamClassifier
from services.gmail_service import GmailService
import os

import time
import base64
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
# Enable CORS for all routes, allowing credentials if needed.
CORS(app, supports_credentials=True)

classifier = SpamClassifier()
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

# ---- GMAIL ROUTES ----

@app.route('/api/gmail/status', methods=['GET'])
def gmail_status():
    if gmail_service.is_connected():
        email = gmail_service.get_profile()
        return jsonify({"connected": True, "email": email}), 200
    return jsonify({"connected": False}), 200

@app.route('/api/gmail/connect', methods=['GET'])
def gmail_connect():
    backend_url = os.environ.get('BACKEND_URL', 'http://localhost:5000').rstrip('/')
    redirect_uri = f'{backend_url}/api/gmail/callback'
    try:
        auth_url, state, code_verifier = gmail_service.get_auth_url(redirect_uri)
        session['oauth_state'] = state
        if code_verifier:
            session['code_verifier'] = code_verifier
        return redirect(auth_url)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/gmail/callback', methods=['GET'])
def gmail_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    backend_url = os.environ.get('BACKEND_URL', 'http://localhost:5000').rstrip('/')
    redirect_uri = f'{backend_url}/api/gmail/callback'

    if not code:
        return jsonify({"error": "No code provided"}), 400

    code_verifier = session.pop('code_verifier', None)

    try:
        gmail_service.exchange_code(code, redirect_uri, state, code_verifier)
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        return redirect(f'{frontend_url}/')
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/gmail/disconnect', methods=['POST'])
def gmail_disconnect():
    gmail_service.disconnect()
    return jsonify({"success": True}), 200

@app.route('/api/gmail/sync', methods=['POST'])
def gmail_sync():
    if not gmail_service.is_connected():
        return jsonify({"error": "Not connected to Gmail"}), 401

    try:
        raw_emails = gmail_service.fetch_recent_emails(limit=20)

        # Classify each email
        for email in raw_emails:
            # We use the body for classification, or snippet if body is empty
            text_to_classify = email['body'] if email['body'] else email['subject'] + " " + email['snippet']

            # Temporary diagnostics
            print(f"Diagnostics [Sync] ID={email['id']}: body_length={len(email['body'])}, body_found={bool(email['body'])}, text_to_classify_length={len(text_to_classify)}")

            if not email['body']:
                print(f"Warning [Sync] ID={email['id']}: Body missing or extraction failed. Falling back to subject + snippet.")

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

        monitoring_state['emails'] = raw_emails
        return jsonify({"emails": raw_emails}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/gmail/watch', methods=['POST'])
def start_watch():
    if not gmail_service.is_connected():
        return jsonify({"error": "Not connected"}), 401

    topic = os.environ.get('PUBSUB_TOPIC_NAME')
    if not topic or 'dummy' in topic:
        return jsonify({"error": "PUBSUB_TOPIC_NAME environment variable is not configured for production."}), 500
    try:
        res = gmail_service.start_watch(topic)
        monitoring_state['monitoring'] = True
        monitoring_state['historyId'] = res.get('historyId')
        monitoring_state['expiration'] = int(res.get('expiration', 0)) if res.get('expiration') else None
        monitoring_state['renewal_status'] = 'active'
        return jsonify({"success": True, "historyId": res.get('historyId'), "expiration": monitoring_state['expiration']}), 200
    except Exception as e:
        import traceback
        from googleapiclient.errors import HttpError
        import json

        err_msg = str(e)
        if isinstance(e, HttpError):
            try:
                error_details = json.loads(e.content.decode('utf-8'))
                err_msg = error_details.get('error', {}).get('message', str(e))
                status = error_details.get('error', {}).get('status', 'ERROR')
                print(f"Watch Error [HTTP {e.resp.status}]: {err_msg} ({status})")
            except Exception:
                print(f"Watch Error: {e}")
        else:
            print(f"Watch Error: {e}")
            traceback.print_exc()

        return jsonify({"error": err_msg}), 400

@app.route('/api/gmail/stop-watch', methods=['POST'])
def stop_watch():
    if not gmail_service.is_connected():
        return jsonify({"error": "Not connected"}), 401
    try:
        gmail_service.stop_watch()
        monitoring_state['monitoring'] = False
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/gmail/renew-watch', methods=['POST'])
def renew_watch():
    if not gmail_service.is_connected():
        return jsonify({"error": "Not connected"}), 401
    topic = os.environ.get('PUBSUB_TOPIC_NAME')
    if not topic or 'dummy' in topic:
        return jsonify({"error": "PUBSUB_TOPIC_NAME environment variable is not configured for production."}), 500
    try:
        res = gmail_service.start_watch(topic)
        monitoring_state['monitoring'] = True
        monitoring_state['historyId'] = res.get('historyId')
        monitoring_state['expiration'] = int(res.get('expiration', 0)) if res.get('expiration') else None
        monitoring_state['renewal_status'] = 'active'
        return jsonify({"success": True, "historyId": res.get('historyId'), "expiration": monitoring_state['expiration']}), 200
    except Exception as e:
        import traceback
        from googleapiclient.errors import HttpError
        import json

        err_msg = str(e)
        if isinstance(e, HttpError):
            try:
                error_details = json.loads(e.content.decode('utf-8'))
                err_msg = error_details.get('error', {}).get('message', str(e))
                status = error_details.get('error', {}).get('status', 'ERROR')
                print(f"Watch Error [HTTP {e.resp.status}]: {err_msg} ({status})")
            except Exception:
                print(f"Watch Error: {e}")
        else:
            print(f"Watch Error: {e}")
            traceback.print_exc()

        return jsonify({"error": err_msg}), 400

@app.route('/api/gmail/pubsub', methods=['POST'])
def pubsub_webhook():
    # Validate Pub/Sub push request token if configured
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
            history_id = msg_data.get('historyId')

            if history_id and monitoring_state['historyId']:
                # Fetch new messages
                new_msg_ids, new_history_id = gmail_service.fetch_history(monitoring_state['historyId'])
                if new_msg_ids is not None:
                    for msg_id in new_msg_ids:
                        email_data = gmail_service.fetch_message_by_id(msg_id)
                        if email_data:
                            # Classify it
                            text_to_classify = email_data['body'] if email_data['body'] else email_data['subject'] + " " + email_data['snippet']

                            # Temporary diagnostics
                            print(f"Diagnostics [Webhook] ID={msg_id}: body_length={len(email_data['body'])}, body_found={bool(email_data['body'])}, text_to_classify_length={len(text_to_classify)}")

                            if not email_data['body']:
                                print(f"Warning [Webhook] ID={msg_id}: Body missing or extraction failed. Falling back to subject + snippet.")

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

                            # Prepend to our list
                            # Check for duplicates
                            if not any(e['id'] == msg_id for e in monitoring_state['emails']):
                                monitoring_state['emails'].insert(0, email_data)

                    if new_history_id:
                        monitoring_state['historyId'] = new_history_id
                else:
                    print("History fetch failed, doing recovery sync")
                    raw_emails = gmail_service.fetch_recent_emails(limit=10)
                    for msg in raw_emails:
                        if not any(e['id'] == msg['id'] for e in monitoring_state['emails']):
                            text_to_classify = msg['body'] if msg['body'] else msg['subject'] + " " + msg['snippet']

                            # Temporary diagnostics
                            print(f"Diagnostics [Recovery] ID={msg['id']}: body_length={len(msg['body'])}, body_found={bool(msg['body'])}, text_to_classify_length={len(text_to_classify)}")

                            if not msg['body']:
                                print(f"Warning [Recovery] ID={msg['id']}: Body missing or extraction failed. Falling back to subject + snippet.")

                            try:
                                prediction_result = classifier.predict(text_to_classify)
                                msg['prediction'] = prediction_result.get('prediction', 'UNKNOWN')
                                msg['classification_strength'] = prediction_result.get('strength', 'Unknown')
                                msg['spam_indicators'] = prediction_result.get('indicators', [])
                            except Exception as e:
                                msg['prediction'] = 'ERROR'
                                msg['classification_strength'] = 'None'
                                msg['spam_indicators'] = []
                            monitoring_state['emails'].insert(0, msg)
                    # Update historyId to the one provided by the webhook to recover
                    monitoring_state['historyId'] = history_id

        except Exception as e:
            print(f"Error processing pubsub message: {e}")

    # Always return 200 to acknowledge Pub/Sub
    return '', 200

@app.route('/api/gmail/latest', methods=['GET'])
def get_latest_emails():
    # Auto-renew logic
    current_time_ms = int(time.time() * 1000)

    if monitoring_state['monitoring'] and monitoring_state['expiration']:
        time_left_ms = monitoring_state['expiration'] - current_time_ms
        # Renew if less than 24 hours (86400000 ms) left
        if time_left_ms < 86400000 and monitoring_state['renewal_status'] != 'renewing':
            monitoring_state['renewal_status'] = 'renewing'
            topic = os.environ.get('PUBSUB_TOPIC_NAME')
    if not topic or 'dummy' in topic:
        return jsonify({"error": "PUBSUB_TOPIC_NAME environment variable is not configured for production."}), 500
            try:
                res = gmail_service.start_watch(topic)
                monitoring_state['expiration'] = int(res.get('expiration', 0)) if res.get('expiration') else None
                monitoring_state['renewal_status'] = 'active'
            except Exception as e:
                print(f"Auto-renewal failed: {e}")
                monitoring_state['renewal_status'] = 'failed'

    monitoring_state['emails'] = monitoring_state['emails'][:50]
    return jsonify({
        "monitoring": monitoring_state['monitoring'],
        "expiration": monitoring_state['expiration'],
        "renewal_status": monitoring_state['renewal_status'],
        "emails": monitoring_state['emails'],
        "current_time": current_time_ms
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)


@app.route('/api/gmail/cron/renew', methods=['POST', 'GET'])
def cron_renew_watch():
    expected_secret = os.environ.get('CRON_SECRET')
    if expected_secret and request.args.get('secret') != expected_secret:
        return jsonify({"error": "Unauthorized"}), 401

    if not gmail_service.is_connected():
        return jsonify({"error": "Not connected to Gmail"}), 401

    topic = os.environ.get('PUBSUB_TOPIC_NAME')
    if not topic or 'dummy' in topic:
        return jsonify({"error": "PUBSUB_TOPIC_NAME environment variable is not configured for production."}), 500

    try:
        res = gmail_service.start_watch(topic)
        monitoring_state['monitoring'] = True
        monitoring_state['expiration'] = int(res.get('expiration', 0)) if res.get('expiration') else None
        monitoring_state['renewal_status'] = 'active'
        return jsonify({"success": True, "expiration": monitoring_state['expiration']}), 200
    except Exception as e:
        monitoring_state['renewal_status'] = 'failed'
        return jsonify({"error": str(e)}), 500

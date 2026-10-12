import os
import base64
import time
import random
import socket
import ssl
import http.client
import urllib.error
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import json

TRANSIENT_HTTP_STATUSES = {429, 500, 502, 503, 504}
PERMANENT_HTTP_STATUSES = {400, 401, 403, 404}
TRANSIENT_NETWORK_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    socket.timeout,
    ssl.SSLError,
    http.client.RemoteDisconnected,
    http.client.ResponseNotReady,
    urllib.error.URLError,
)


def is_transient_gmail_error(exc):
    """
    Determines whether an error encountered during a Gmail API call is transient and safe to retry.
    Retryable: HTTP 429, 500, 502, 503, 504, plus temporary connection/timeout exceptions.
    Non-retryable: HTTP 400, 401, 403, 404, invalid grants, authentication/authorization failures.
    """
    if isinstance(exc, HttpError):
        status = getattr(exc.resp, 'status', None) if hasattr(exc, 'resp') else getattr(exc, 'status_code', None)
        if status is not None:
            try:
                status_int = int(status)
                if status_int in TRANSIENT_HTTP_STATUSES:
                    return True
                if status_int in PERMANENT_HTTP_STATUSES:
                    return False
            except (ValueError, TypeError):
                pass
        err_str = str(exc).lower()
        for perm in ('400', '401', '403', '404', 'invalid_grant', 'permissiondenied'):
            if perm in err_str:
                return False
        for trans in ('429', '500', '502', '503', '504', 'ratelimitexceeded', 'backenderror'):
            if trans in err_str:
                return True
        return False

    if isinstance(exc, TRANSIENT_NETWORK_EXCEPTIONS):
        return True

    # Generic or wrapped exceptions
    err_str = str(exc).lower()
    for perm in ('400', '401', '403', '404', 'invalid_grant', 'forbidden', 'unauthorized', 'permission'):
        if perm in err_str:
            return False
    for trans in ('429', '500', '502', '503', '504', 'timeout', 'timed out', 'connection reset', 'connection refused', 'remote disconnected'):
        if trans in err_str:
            return True

    return False


try:
    from dotenv import load_dotenv
    # Ensure backend/.env or root .env is loaded if credentials are not already present in environment
    _has_creds = (
        (os.environ.get('GOOGLE_CLIENT_ID') and os.environ.get('GOOGLE_CLIENT_SECRET')) or
        (os.environ.get('GMAIL_CLIENT_ID') and os.environ.get('GMAIL_CLIENT_SECRET')) or
        os.environ.get('GOOGLE_CREDENTIALS_JSON')
    )
    if not _has_creds:
        _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for _env_candidate in [
            os.path.join(_backend_dir, '.env'),
            os.path.join(os.path.dirname(_backend_dir), '.env'),
            os.path.join(os.getcwd(), '.env'),
            os.path.join(os.getcwd(), 'backend', '.env')
        ]:
            if os.path.exists(_env_candidate):
                load_dotenv(_env_candidate)
                if (
                    (os.environ.get('GOOGLE_CLIENT_ID') and os.environ.get('GOOGLE_CLIENT_SECRET')) or
                    (os.environ.get('GMAIL_CLIENT_ID') and os.environ.get('GMAIL_CLIENT_SECRET')) or
                    os.environ.get('GOOGLE_CREDENTIALS_JSON')
                ):
                    break
except ImportError:
    pass

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def _resolve_default_redirect_uris():
    """
    Safely constructs a deduplicated list of OAuth redirect callback URLs.
    Preserves BACKEND_URL, RENDER_EXTERNAL_URL, and local development endpoints.
    """
    explicit = (os.environ.get('GOOGLE_REDIRECT_URI') or os.environ.get('GMAIL_REDIRECT_URI') or '').strip()
    uris = []
    if explicit:
        uris.append(explicit)

    backend_url = (os.environ.get('BACKEND_URL') or os.environ.get('RENDER_EXTERNAL_URL') or '').strip().rstrip('/')
    if backend_url:
        uris.append(f"{backend_url}/api/gmail/callback")

    uris.append("https://e-mail-spam-shield.onrender.com/api/gmail/callback")
    uris.append("http://localhost:5000/api/gmail/callback")

    seen = set()
    deduped = []
    for u in uris:
        if u and u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


class GmailService:
    def __init__(self, creds_dict=None):
        self.creds = None
        if creds_dict:
            if isinstance(creds_dict, str):
                try:
                    creds_dict = json.loads(creds_dict)
                except Exception:
                    creds_dict = None
            if not isinstance(creds_dict, dict):
                return

            effective_creds = dict(creds_dict)
            active_id, active_secret = self.get_active_client_id_and_secret()
            stored_id = effective_creds.get('client_id')

            # Reconcile client credentials safely:
            # Only update client_secret if active credentials exist AND
            # stored client_id matches active client_id (or stored client_id is missing/empty).
            # Do NOT mutate or overwrite if stored client_id explicitly mismatches active client_id.
            if active_id and active_secret:
                if not stored_id or str(stored_id).strip() == str(active_id).strip():
                    if not stored_id:
                        effective_creds['client_id'] = active_id
                    effective_creds['client_secret'] = active_secret

            try:
                self.creds = Credentials.from_authorized_user_info(effective_creds, SCOPES)
            except Exception as e:
                print("Error initializing credentials:", e)
                self.creds = None

            if self.creds and (self.creds.expired or not self.creds.valid) and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print("Error refreshing token:", e)
                    self.creds = None

    def refresh_credentials(self, request=None):
        """
        Explicitly refreshes expired credentials using the active Request.
        Reconciles active client credentials before refresh if compatible.
        Returns True if refreshed successfully, False otherwise.
        """
        if not self.creds or not self.creds.refresh_token:
            return False

        active_id, active_secret = self.get_active_client_id_and_secret()
        if active_id and active_secret:
            stored_id = getattr(self.creds, 'client_id', None)
            if not stored_id or str(stored_id).strip() == str(active_id).strip():
                self.creds._client_id = active_id
                self.creds._client_secret = active_secret

        try:
            req = request or Request()
            self.creds.refresh(req)
            return self.is_connected()
        except Exception as e:
            print("Error refreshing token:", e)
            return False

    def is_connected(self):
        return self.creds is not None and self.creds.valid

    def get_credentials_dict(self):
        if self.is_connected():
            return json.loads(self.creds.to_json())
        return None

    def disconnect(self):
        try:
            self.stop_watch()
        except Exception:
            pass
        self.creds = None

    @classmethod
    def get_active_client_config(cls):
        """
        Safely retrieves the active client configuration without throwing if unconfigured.
        Returns the parsed dictionary, or None.
        """
        try:
            return cls._get_client_config()
        except Exception:
            return None

    @classmethod
    def get_active_client_id_and_secret(cls):
        """
        Extracts (client_id, client_secret) from the active client configuration.
        Returns (client_id, client_secret) or (None, None).
        """
        # Fast path from discrete environment variables
        client_id = (os.environ.get('GOOGLE_CLIENT_ID') or os.environ.get('GMAIL_CLIENT_ID') or '').strip()
        client_secret = (os.environ.get('GOOGLE_CLIENT_SECRET') or os.environ.get('GMAIL_CLIENT_SECRET') or '').strip()
        if client_id and client_secret:
            return client_id, client_secret

        config = cls.get_active_client_config()
        if not config:
            return None, None
        app_config = config.get('web') or config.get('installed') or {}
        cid = (app_config.get('client_id') or '').strip() or None
        csec = (app_config.get('client_secret') or '').strip() or None
        return cid, csec

    @staticmethod
    def _get_client_config():
        """
        Safely retrieves and parses the Google OAuth client configuration.
        Prioritizes discrete environment variables GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
        (with GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET aliases).
        Falls back to GOOGLE_CREDENTIALS_JSON (direct JSON string or file path),
        and local candidate files (backend/credentials.json or root credentials.json).
        Returns the parsed dictionary.
        Raises ValueError or RuntimeError if credentials cannot be resolved or parsed.
        """
        # 1. Preferred Production Configuration: discrete client ID and secret
        client_id = (os.environ.get('GOOGLE_CLIENT_ID') or os.environ.get('GMAIL_CLIENT_ID') or '').strip()
        client_secret = (os.environ.get('GOOGLE_CLIENT_SECRET') or os.environ.get('GMAIL_CLIENT_SECRET') or '').strip()

        if client_id and client_secret:
            return {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": _resolve_default_redirect_uris()
                }
            }

        # 2. Backward-compatible fallback: GOOGLE_CREDENTIALS_JSON or candidate files
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')

        # If not present in os.environ, attempt loading backend/.env if available
        if not creds_json:
            try:
                from dotenv import load_dotenv
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                env_file = os.path.join(backend_dir, '.env')
                if os.path.exists(env_file):
                    load_dotenv(env_file)
                    # Re-check discrete variables if loaded from .env
                    client_id = (os.environ.get('GOOGLE_CLIENT_ID') or os.environ.get('GMAIL_CLIENT_ID') or '').strip()
                    client_secret = (os.environ.get('GOOGLE_CLIENT_SECRET') or os.environ.get('GMAIL_CLIENT_SECRET') or '').strip()
                    if client_id and client_secret:
                        return {
                            "web": {
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                                "redirect_uris": _resolve_default_redirect_uris()
                            }
                        }
                    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            except ImportError:
                pass

        client_config = None

        if creds_json and str(creds_json).strip():
            raw = str(creds_json).strip()

            # Strip possible surrounding single or double quotes from .env parsing
            if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
                raw = raw[1:-1].strip()

            # Case A: JSON string
            if raw.startswith('{'):
                try:
                    client_config = json.loads(raw)
                except json.JSONDecodeError as e:
                    # Attempt unescaping if string had escaped characters
                    try:
                        unescaped = raw.encode('utf-8').decode('unicode_escape')
                        client_config = json.loads(unescaped)
                    except Exception:
                        raise ValueError(f"Failed to parse GOOGLE_CREDENTIALS_JSON: Invalid JSON ({str(e)})")

            # Case B: File path specified in GOOGLE_CREDENTIALS_JSON
            elif os.path.exists(raw):
                try:
                    with open(raw, 'r', encoding='utf-8') as f:
                        client_config = json.load(f)
                except Exception as e:
                    raise ValueError(f"Failed to load credentials from file specified in GOOGLE_CREDENTIALS_JSON: {str(e)}")

        # Fallback: check standard candidate file locations on disk
        if not client_config:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate_files = [
                os.path.join(backend_dir, 'credentials.json'),
                os.path.join(os.path.dirname(backend_dir), 'credentials.json'),
                os.path.join(os.getcwd(), 'credentials.json'),
                os.path.join(os.getcwd(), 'backend', 'credentials.json'),
            ]
            for c_path in candidate_files:
                if os.path.exists(c_path):
                    try:
                        with open(c_path, 'r', encoding='utf-8') as f:
                            client_config = json.load(f)
                        if client_config:
                            break
                    except Exception as e:
                        raise ValueError(f"Failed to read credentials file at {c_path}: {str(e)}")

        if not client_config:
            raise RuntimeError(
                "Google OAuth credentials not found. "
                "Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET, "
                "or GOOGLE_CREDENTIALS_JSON with your OAuth client credentials JSON, "
                "or place a credentials.json file in the backend directory."
            )

        if not isinstance(client_config, dict) or not ('web' in client_config or 'installed' in client_config):
            raise ValueError(
                "Invalid Google OAuth client configuration. Expected top-level 'web' or 'installed' dictionary."
            )

        return client_config

    @staticmethod
    def _get_flow(redirect_uri):
        client_config = GmailService._get_client_config()
        return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)

    @staticmethod
    def get_auth_url(redirect_uri, state=None, code_verifier=None):
        try:
            flow = GmailService._get_flow(redirect_uri)
        except (ValueError, RuntimeError) as e:
            raise Exception(f"Failed to parse credentials: {str(e)}")
            
        if code_verifier:
            flow.code_verifier = code_verifier

        kwargs = {'prompt': 'consent', 'access_type': 'offline'}
        if state:
            kwargs['state'] = state
            
        auth_url, generated_state = flow.authorization_url(**kwargs)
        if not code_verifier:
            code_verifier = getattr(flow, 'code_verifier', None)
        return auth_url, generated_state, code_verifier
        
    @staticmethod
    def exchange_code(code, redirect_uri, state=None, code_verifier=None):
        try:
            flow = GmailService._get_flow(redirect_uri)
        except (ValueError, RuntimeError) as e:
            raise Exception(f"Failed to parse credentials: {str(e)}")
            
        if code_verifier:
            flow.fetch_token(code=code, code_verifier=code_verifier)
        else:
            flow.fetch_token(code=code)
            
        return json.loads(flow.credentials.to_json())
        
    def get_profile(self):
        if not self.is_connected():
            return None
        service = build('gmail', 'v1', credentials=self.creds)
        profile = service.users().getProfile(userId='me').execute()
        return profile.get('emailAddress')

    def fetch_recent_emails(self, limit=20):
        if not self.is_connected():
            raise Exception("Not connected to Gmail")
            
        service = build('gmail', 'v1', credentials=self.creds)
        results = service.users().messages().list(userId='me', maxResults=limit).execute()
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            try:
                msg_details = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                extracted = self._extract_email_data(msg_details)
                emails.append(extracted)
            except Exception as e:
                print(f"Error fetching email {msg['id']}: {e}")
            
        return emails
        
    def _extract_email_data(self, msg_details):
        payload = msg_details.get('payload', {})
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown Date')
        
        body = self._get_body(payload)
        body_html = self._get_html_body(payload)

        internal_date = None
        if msg_details.get('internalDate'):
            try:
                internal_date = int(msg_details['internalDate'])
            except (ValueError, TypeError):
                internal_date = None
        if not internal_date and date and date != 'Unknown Date':
            try:
                import email.utils
                parsed_dt = email.utils.parsedate_to_datetime(date)
                internal_date = int(parsed_dt.timestamp() * 1000)
            except Exception:
                internal_date = None

        return {
            'id': msg_details['id'],
            'sender': sender,
            'subject': subject,
            'timestamp': date,
            'internal_date': internal_date,
            'snippet': msg_details.get('snippet', ''),
            'body': body,
            'body_html': body_html
        }
        
    def _get_body(self, payload):
        body_data = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    continue
                if part['mimeType'] == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body_data += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html' and not body_data:
                    data = part.get('body', {}).get('data', '')
                    if data:
                        html_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        import re
                        body_data += re.sub('<[^<]+>', ' ', html_text)
                elif 'parts' in part:
                    body_data += self._get_body(part)
        elif 'body' in payload and 'data' in payload['body']:
            data = payload['body']['data']
            decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            if payload.get('mimeType') == 'text/html':
                import re
                decoded = re.sub('<[^<]+>', ' ', decoded)
            body_data = decoded
            
        return body_data

    def _get_html_body(self, payload):
        html_data = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    continue
                if part['mimeType'] == 'text/html':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        html_data += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif 'parts' in part:
                    html_data += self._get_html_body(part)
        elif payload.get('mimeType') == 'text/html':
            data = payload.get('body', {}).get('data', '')
            if data:
                html_data = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                
        return html_data

    def start_watch(self, topic_name, max_retries=2, initial_backoff=0.5, max_backoff=2.0, sleep_fn=time.sleep):
        """
        Registers a Gmail push watch for INBOX with bounded exponential backoff on transient errors.
        Retries up to max_retries times (max 3 total attempts) on HTTP 429, 500, 502, 503, 504 and network errors.
        Does not retry permanent errors such as 400, 401, 403, 404.
        """
        if not self.is_connected():
            raise Exception("Not connected to Gmail")
        service = build('gmail', 'v1', credentials=self.creds)
        request = {
            'labelIds': ['INBOX'],
            'labelFilterBehavior': 'INCLUDE',
            'topicName': topic_name
        }

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                res = service.users().watch(userId='me', body=request).execute()
                return res
            except Exception as e:
                last_error = e
                if attempt < max_retries and is_transient_gmail_error(e):
                    backoff = min(max_backoff, initial_backoff * (2 ** attempt))
                    jitter = random.uniform(0.05, 0.25)
                    delay = backoff + jitter
                    if sleep_fn:
                        sleep_fn(delay)
                    continue
                raise last_error

        raise last_error


    def stop_watch(self):
        if not self.is_connected():
            return
        service = build('gmail', 'v1', credentials=self.creds)
        service.users().stop(userId='me').execute()

    def fetch_history(self, start_history_id):
        if not self.is_connected():
            raise Exception("Not connected")
        service = build('gmail', 'v1', credentials=self.creds)
        try:
            res = service.users().history().list(userId='me', startHistoryId=start_history_id).execute()
            
            new_message_ids = []
            if 'history' in res:
                for record in res['history']:
                    if 'messagesAdded' in record:
                        for added in record['messagesAdded']:
                            msg_id = added['message']['id']
                            if msg_id not in new_message_ids:
                                new_message_ids.append(msg_id)
            return new_message_ids, res.get('historyId')
        except Exception as e:
            print(f"Error fetching history: {e}")
            return None, None
            
    def fetch_message_by_id(self, msg_id):
        if not self.is_connected():
            return None
        service = build('gmail', 'v1', credentials=self.creds)
        try:
            msg_details = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            return self._extract_email_data(msg_details)
        except Exception as e:
            print(f"Error fetching specific message {msg_id}: {e}")
            return None

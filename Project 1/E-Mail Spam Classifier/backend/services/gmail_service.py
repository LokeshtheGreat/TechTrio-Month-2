import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import json

try:
    from dotenv import load_dotenv
    # Ensure backend/.env or root .env is loaded if environment variables are not already present
    if not os.environ.get('GOOGLE_CREDENTIALS_JSON'):
        _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for _env_candidate in [
            os.path.join(_backend_dir, '.env'),
            os.path.join(os.path.dirname(_backend_dir), '.env'),
            os.path.join(os.getcwd(), '.env'),
            os.path.join(os.getcwd(), 'backend', '.env')
        ]:
            if os.path.exists(_env_candidate):
                load_dotenv(_env_candidate)
                if os.environ.get('GOOGLE_CREDENTIALS_JSON'):
                    break
except ImportError:
    pass

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    def __init__(self, creds_dict=None):
        self.creds = None
        if creds_dict:
            self.creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print("Error refreshing token:", e)
                    self.creds = None

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

    @staticmethod
    def _get_client_config():
        """
        Safely retrieves and parses the Google OAuth client configuration.
        Prioritizes the GOOGLE_CREDENTIALS_JSON environment variable (used in production on Render
        and local development).
        Supports:
          1. Direct JSON string in GOOGLE_CREDENTIALS_JSON (safe parsing, handling quotes/escapes).
          2. File path in GOOGLE_CREDENTIALS_JSON pointing to credentials file.
          3. Local file fallbacks (backend/credentials.json or root credentials.json).
        Returns the parsed dictionary.
        Raises ValueError or RuntimeError if credentials cannot be resolved or parsed.
        """
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')

        # If not present in os.environ, attempt loading backend/.env if available
        if not creds_json:
            try:
                from dotenv import load_dotenv
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                env_file = os.path.join(backend_dir, '.env')
                if os.path.exists(env_file):
                    load_dotenv(env_file)
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
                "Please configure the GOOGLE_CREDENTIALS_JSON environment variable with your OAuth client credentials JSON, "
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

    def start_watch(self, topic_name):
        if not self.is_connected():
            raise Exception("Not connected to Gmail")
        service = build('gmail', 'v1', credentials=self.creds)
        request = {
            'labelIds': ['INBOX'],
            'labelFilterBehavior': 'INCLUDE',
            'topicName': topic_name
        }
        res = service.users().watch(userId='me', body=request).execute()
        return res

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

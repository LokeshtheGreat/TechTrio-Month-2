import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.credentials_path = os.path.join(self.base_dir, 'credentials.json')
        self.token_path = os.path.join(self.base_dir, 'token.json')
        
        self.creds = None
        self._load_credentials()

    def _load_credentials(self):
        if os.path.exists(self.token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                print("Error loading token:", e)
                
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())
            except Exception as e:
                print("Error refreshing token:", e)
                self.creds = None

    def is_connected(self):
        return self.creds is not None and self.creds.valid

    def _get_flow(self, redirect_uri):
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            import json
            client_config = json.loads(creds_json)
            return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)
        else:
            if not os.path.exists(self.credentials_path):
                raise Exception("credentials.json not found and GOOGLE_CREDENTIALS_JSON env var is missing.")
            return Flow.from_client_secrets_file(self.credentials_path, scopes=SCOPES, redirect_uri=redirect_uri)

    def get_auth_url(self, redirect_uri):
        try:
            flow = self._get_flow(redirect_uri)
        except ValueError as e:
            raise Exception(f"Failed to parse credentials: {str(e)}")
            
        auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')
        code_verifier = getattr(flow, 'code_verifier', None)
        return auth_url, state, code_verifier
        
    def exchange_code(self, code, redirect_uri, state=None, code_verifier=None):
        try:
            flow = self._get_flow(redirect_uri)
        except ValueError as e:
            raise Exception(f"Failed to parse credentials: {str(e)}")
            
        if code_verifier:
            flow.fetch_token(code=code, code_verifier=code_verifier)
        else:
            flow.fetch_token(code=code)
            
        self.creds = flow.credentials
        
        with open(self.token_path, 'w') as token:
            token.write(self.creds.to_json())
            
    def disconnect(self):
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
        self.creds = None
        
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
        
        return {
            'id': msg_details['id'],
            'sender': sender,
            'subject': subject,
            'timestamp': date,
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

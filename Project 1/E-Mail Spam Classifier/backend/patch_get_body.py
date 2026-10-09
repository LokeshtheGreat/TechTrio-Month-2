import re

with open('services/gmail_service.py', 'r') as f:
    content = f.read()

get_body_new = """
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
"""
content = re.sub(r'    def _get_body\(self, payload\):[\s\S]+?return body_data', get_body_new.strip('\n'), content)

with open('services/gmail_service.py', 'w') as f:
    f.write(content)

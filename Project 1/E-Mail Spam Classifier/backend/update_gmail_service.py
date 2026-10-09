import re

with open('services/gmail_service.py', 'r') as f:
    content = f.read()

import_json = "import json\n"
if "import json" not in content:
    content = content.replace("import base64", "import base64\nimport json")

new_methods = """
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
"""

if "def start_watch" not in content:
    content += new_methods
    
with open('services/gmail_service.py', 'w') as f:
    f.write(content)

print("Updated gmail_service.py")

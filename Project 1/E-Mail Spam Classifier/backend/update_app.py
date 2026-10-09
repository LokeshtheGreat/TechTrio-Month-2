import os
import json

app_path = 'app.py'
with open(app_path, 'r') as f:
    content = f.read()

new_imports = """
import time
import base64
from dotenv import load_dotenv

load_dotenv()
"""
if "import time" not in content:
    content = content.replace("import os", "import os\n" + new_imports)

# We need a global state to store fetched emails and historyId
global_state = """
# Global state for Live Monitor
monitoring_state = {
    'monitoring': False,
    'historyId': None,
    'emails': []
}
"""
if "monitoring_state = {" not in content:
    content = content.replace("gmail_service = GmailService()", "gmail_service = GmailService()\n" + global_state)


new_routes = """
@app.route('/api/gmail/watch', methods=['POST'])
def start_watch():
    if not gmail_service.is_connected():
        return jsonify({"error": "Not connected"}), 401
    
    topic = os.environ.get('PUBSUB_TOPIC_NAME', 'projects/dummy/topics/dummy')
    try:
        res = gmail_service.start_watch(topic)
        monitoring_state['monitoring'] = True
        monitoring_state['historyId'] = res.get('historyId')
        return jsonify({"success": True, "historyId": res.get('historyId')}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

@app.route('/api/gmail/pubsub', methods=['POST'])
def pubsub_webhook():
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
        except Exception as e:
            print(f"Error processing pubsub message: {e}")
            
    # Always return 200 to acknowledge Pub/Sub
    return '', 200

@app.route('/api/gmail/latest', methods=['GET'])
def get_latest_emails():
    # Frontend can poll this endpoint to get the latest state
    # Limit to 50 for memory
    monitoring_state['emails'] = monitoring_state['emails'][:50]
    return jsonify({
        "monitoring": monitoring_state['monitoring'],
        "emails": monitoring_state['emails']
    }), 200
"""

if "def start_watch(" not in content:
    content = content.replace("if __name__ == '__main__':", new_routes + "\nif __name__ == '__main__':")

with open(app_path, 'w') as f:
    f.write(content)
print("Updated app.py")

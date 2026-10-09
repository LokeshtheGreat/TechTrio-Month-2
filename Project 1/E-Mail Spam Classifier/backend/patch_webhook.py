import re

with open('app.py', 'r') as f:
    content = f.read()

webhook_replacement = """
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
                else:
                    print("History fetch failed, doing recovery sync")
                    raw_emails = gmail_service.fetch_recent_emails(limit=10)
                    for msg in raw_emails:
                        if not any(e['id'] == msg['id'] for e in monitoring_state['emails']):
                            text_to_classify = msg['body'] if msg['body'] else msg['subject'] + " " + msg['snippet']
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
"""

content = re.sub(r'@app\.route\(\'/api/gmail/pubsub\', methods=\[\'POST\'\]\)[\s\S]+?return \'\', 200', webhook_replacement.strip(), content)

with open('app.py', 'w') as f:
    f.write(content)

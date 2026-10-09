import re

with open('app.py', 'r') as f:
    content = f.read()

# For gmail_sync
sync_pattern = r'text_to_classify = email\[\'body\'\] if email\[\'body\'\] else email\[\'subject\'\] \+ " " \+ email\[\'snippet\'\]\s+try:\s+prediction_result = classifier\.predict\(text_to_classify\)'
sync_replacement = """text_to_classify = email['body'] if email['body'] else email['subject'] + " " + email['snippet']
            
            # Temporary diagnostics
            print(f"Diagnostics [Sync] ID={email['id']}: body_length={len(email['body'])}, body_found={bool(email['body'])}, text_to_classify_length={len(text_to_classify)}")
            
            if not email['body']:
                print(f"Warning [Sync] ID={email['id']}: Body missing or extraction failed. Falling back to subject + snippet.")
                
            try:
                prediction_result = classifier.predict(text_to_classify)"""
content = re.sub(sync_pattern, sync_replacement, content)

# For pubsub_webhook
pubsub_pattern = r'text_to_classify = email_data\[\'body\'\] if email_data\[\'body\'\] else email_data\[\'subject\'\] \+ " " \+ email_data\[\'snippet\'\]\s+try:\s+prediction_result = classifier\.predict\(text_to_classify\)'
pubsub_replacement = """text_to_classify = email_data['body'] if email_data['body'] else email_data['subject'] + " " + email_data['snippet']
                            
                            # Temporary diagnostics
                            print(f"Diagnostics [Webhook] ID={msg_id}: body_length={len(email_data['body'])}, body_found={bool(email_data['body'])}, text_to_classify_length={len(text_to_classify)}")
                            
                            if not email_data['body']:
                                print(f"Warning [Webhook] ID={msg_id}: Body missing or extraction failed. Falling back to subject + snippet.")
                                
                            try:
                                prediction_result = classifier.predict(text_to_classify)"""
content = re.sub(pubsub_pattern, pubsub_replacement, content)

# For pubsub_webhook recovery sync loop
recovery_pattern = r'text_to_classify = msg\[\'body\'\] if msg\[\'body\'\] else msg\[\'subject\'\] \+ " " \+ msg\[\'snippet\'\]\s+try:\s+prediction_result = classifier\.predict\(text_to_classify\)'
recovery_replacement = """text_to_classify = msg['body'] if msg['body'] else msg['subject'] + " " + msg['snippet']
                            
                            # Temporary diagnostics
                            print(f"Diagnostics [Recovery] ID={msg['id']}: body_length={len(msg['body'])}, body_found={bool(msg['body'])}, text_to_classify_length={len(text_to_classify)}")
                            
                            if not msg['body']:
                                print(f"Warning [Recovery] ID={msg['id']}: Body missing or extraction failed. Falling back to subject + snippet.")
                                
                            try:
                                prediction_result = classifier.predict(text_to_classify)"""
content = re.sub(recovery_pattern, recovery_replacement, content)

with open('app.py', 'w') as f:
    f.write(content)

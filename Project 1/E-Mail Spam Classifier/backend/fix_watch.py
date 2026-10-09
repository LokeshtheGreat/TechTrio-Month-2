with open('backend/app.py', 'r') as f:
    content = f.read()

import re

# 1. Update monitoring_state definition
state_replacement = """
monitoring_state = {
    'monitoring': False,
    'historyId': None,
    'expiration': None,
    'renewal_status': 'active', # active, renewing, failed
    'emails': []
}
"""
content = re.sub(r'monitoring_state = \{[^}]+\}', state_replacement.strip(), content)

# 2. Update start_watch to save expiration
start_watch_replacement = """
    try:
        res = gmail_service.start_watch(topic)
        monitoring_state['monitoring'] = True
        monitoring_state['historyId'] = res.get('historyId')
        monitoring_state['expiration'] = int(res.get('expiration', 0)) if res.get('expiration') else None
        monitoring_state['renewal_status'] = 'active'
        return jsonify({"success": True, "historyId": res.get('historyId'), "expiration": monitoring_state['expiration']}), 200
"""
content = re.sub(r'    try:\n        res = gmail_service\.start_watch\(topic\)\n        monitoring_state\[\'monitoring\'\] = True\n        monitoring_state\[\'historyId\'\] = res\.get\(\'historyId\'\)\n        return jsonify\(\{"success": True, "historyId": res\.get\(\'historyId\'\)\}\), 200', start_watch_replacement.strip(), content)

# 3. Add a renew endpoint
renew_endpoint = """
@app.route('/api/gmail/renew-watch', methods=['POST'])
def renew_watch():
    if not gmail_service.is_connected():
        return jsonify({"error": "Not connected"}), 401
    topic = os.environ.get('PUBSUB_TOPIC_NAME', 'projects/dummy/topics/dummy')
    try:
        res = gmail_service.start_watch(topic)
        monitoring_state['monitoring'] = True
        monitoring_state['expiration'] = int(res.get('expiration', 0)) if res.get('expiration') else None
        monitoring_state['renewal_status'] = 'active'
        return jsonify({"success": True, "expiration": monitoring_state['expiration']}), 200
    except Exception as e:
        monitoring_state['renewal_status'] = 'failed'
        return jsonify({"error": str(e)}), 500
"""
if "/api/gmail/renew-watch" not in content:
    content = content.replace("@app.route('/api/gmail/pubsub'", renew_endpoint + "\n@app.route('/api/gmail/pubsub'")

# 4. Auto-renew logic in latest endpoint
latest_replacement = """
@app.route('/api/gmail/latest', methods=['GET'])
def get_latest_emails():
    # Auto-renew logic
    current_time_ms = int(time.time() * 1000)
    
    if monitoring_state['monitoring'] and monitoring_state['expiration']:
        time_left_ms = monitoring_state['expiration'] - current_time_ms
        # Renew if less than 24 hours (86400000 ms) left
        if time_left_ms < 86400000 and monitoring_state['renewal_status'] != 'renewing':
            monitoring_state['renewal_status'] = 'renewing'
            topic = os.environ.get('PUBSUB_TOPIC_NAME', 'projects/dummy/topics/dummy')
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
"""
content = re.sub(r'@app\.route\(\'/api/gmail/latest\', methods=\[\'GET\'\]\)[\s\S]+?return jsonify\(\{.*?\}\), 200', latest_replacement.strip(), content, flags=re.DOTALL)

with open('backend/app.py', 'w') as f:
    f.write(content)

import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace the start_watch exception handling
start_watch_replacement = """
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
"""
content = re.sub(r'    try:\n        res = gmail_service\.start_watch\(topic\)[\s\S]+?return jsonify\(\{"error": str\(e\)\}\), 500', start_watch_replacement.strip('\n'), content)

with open('app.py', 'w') as f:
    f.write(content)

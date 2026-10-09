with open('app.py', 'r') as f:
    content = f.read()

target = 'return jsonify({"emails": raw_emails}), 200'
replacement = '''monitoring_state['emails'] = raw_emails
        return jsonify({"emails": raw_emails}), 200'''

if "monitoring_state['emails'] = raw_emails" not in content:
    content = content.replace(target, replacement)

with open('app.py', 'w') as f:
    f.write(content)

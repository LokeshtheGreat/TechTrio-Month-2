from services.gmail_service import GmailService
import json

g = GmailService()
emails = g.fetch_recent_emails(limit=20)
for e in emails:
    if "Google" not in e['sender'] and e.get('body_html'):
        with open('other_email.html', 'w', encoding='utf-8') as f:
            f.write(e['body_html'])
        break

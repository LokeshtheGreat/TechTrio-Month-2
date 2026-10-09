from services.gmail_service import GmailService
import json

g = GmailService()
emails = g.fetch_recent_emails(limit=20)
for e in emails:
    if "Google" in e['sender'] or "Google" in e['subject']:
        print("Found Google email:", e['subject'])
        with open('google_email.html', 'w', encoding='utf-8') as f:
            f.write(e.get('body_html', ''))
        break
else:
    print("No Google email found")

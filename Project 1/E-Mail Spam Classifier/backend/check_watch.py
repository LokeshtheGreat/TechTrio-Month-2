import os
from services.gmail_service import GmailService
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

gmail_service = GmailService()
topic = os.environ.get('PUBSUB_TOPIC_NAME', 'projects/dummy/topics/dummy')
print(f"Topic configured: {topic}")

try:
    gmail_service.start_watch(topic)
    print("Watch started successfully.")
except HttpError as e:
    print(f"HttpError caught! Status: {e.resp.status}")
    print(f"Content: {e.content}")
except Exception as e:
    print(f"General exception: {type(e)} - {e}")

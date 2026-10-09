# Production Deployment Requirements

## 1. Backend Environment Variables (Render)
Ensure the following are set in the Render dashboard:
*   `GOOGLE_CREDENTIALS_JSON`: The full JSON string of your `credentials.json` (do not commit the file).
*   `FRONTEND_URL`: The deployed Vercel URL (e.g., `https://email-spam-shield.vercel.app`).
*   `BACKEND_URL`: The deployed Render URL (e.g., `https://email-spam-shield-api.onrender.com`).
*   `PUBSUB_TOPIC_NAME`: The fully qualified Google Cloud Pub/Sub topic string.
*   `FLASK_SECRET_KEY`: A strong random string for encrypting OAuth PKCE state in Flask sessions.
*   `PUBSUB_VERIFICATION_TOKEN`: (Optional) Secret token for validating incoming webhook push notifications to `/api/gmail/pubsub`.
*   `CRON_SECRET`: (Optional) Secret token for securing the `/api/gmail/cron/renew` endpoint from unauthorized access.
*   **[CRITICAL] `DATABASE_URL`**: Render's filesystem is ephemeral. A PostgreSQL database connection string is fundamentally required to persist the OAuth `token.json` credentials across server restarts. The application currently logs a heavy warning and defaults to a local file, which will wipe your login status on every deploy.

## 2. Frontend Environment Variables (Vercel)
Ensure the following are set in the Vercel dashboard:
*   `VITE_BACKEND_URL`: The deployed Render URL (e.g., `https://email-spam-shield-api.onrender.com`). Used by all Axios requests.

## 3. External Google Cloud Setup
*   **Google OAuth Authorized Redirect URIs**: You must add `https://<your-render-url>/api/gmail/callback` to your Google Cloud Console OAuth Authorized Redirect URIs.
*   **Pub/Sub Topic Permissions**: Ensure `gmail-api-push@system.gserviceaccount.com` has the `Pub/Sub Publisher` role on your topic.
*   **Cron Job Setup**: The Gmail watch expires after 7 days. Configure an external cron job (e.g., cron-job.org or Google Cloud Scheduler) to hit `POST https://<your-render-url>/api/gmail/cron/renew?secret=<your-cron-secret>` every 3 days.

## 4. Tests and Builds
*   The frontend production build (`npm run build`) runs successfully with no errors.
*   The backend prediction pipeline has remained completely untouched and continues to function exactly as designed.
*   *Note on End-to-End Tests*: Cannot run an automated end-to-end Pub/Sub push notification test without valid Google Cloud credentials or a live ngrok tunnel.

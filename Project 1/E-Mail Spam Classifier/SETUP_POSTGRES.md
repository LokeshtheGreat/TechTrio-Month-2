# PostgreSQL Database Setup Guide

## Local Development
1. Install PostgreSQL on your local machine.
2. Open `psql` or pgAdmin and create a new database:
   ```sql
   CREATE DATABASE spam_classifier;
   CREATE USER spam_user WITH ENCRYPTED PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE spam_classifier TO spam_user;
   ```
3. Copy `.env.example` to `.env` in the `backend/` directory.
4. Update `DATABASE_URL` in `.env` to match your local setup:
   `DATABASE_URL=postgresql://spam_user:your_password@localhost:5432/spam_classifier`
5. Run database migrations:
   ```bash
   cd backend
   flask db upgrade
   ```

## Production (Render)
1. In your Render Dashboard, click **New +** and select **PostgreSQL**.
2. Name the database (e.g., `spam-classifier-db`) and provision it.
3. Once provisioned, copy the **Internal Database URL**.
4. Go to your backend Web Service settings on Render -> Environment Variables.
5. Add `DATABASE_URL` and paste the Internal Database URL.
6. (Optional but recommended) Run migrations automatically on deploy by setting the Build Command to:
   `pip install -r requirements.txt && flask db upgrade`

*Note: The application will fundamentally refuse to start if `DATABASE_URL` is missing or if it points to an SQLite database (`sqlite://`). Persistent storage is mandatory.*

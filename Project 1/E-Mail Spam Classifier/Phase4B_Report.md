# Phase 4B: Real-Time Gmail Monitoring & OAuth Strategy

## Overview
Phase 4B implements real-time Gmail monitoring via Google Cloud Pub/Sub pushes, complete with robust backend-driven watch expiration handling, auto-renewal, and frontend monitoring status visualization. The architecture anticipates production deployment and correctly accounts for Google OAuth testing constraints.

## 1. Watch Expiration & Auto-Renewal
Gmail watches expire 7 days after creation. To guarantee continuous service without manual intervention:
- **Backend Auto-Renewal**: The Flask `/api/gmail/latest` polling endpoint actively tracks watch expiration time. When the watch enters a 24-hour expiration window, the backend transparently triggers a silent renewal by calling `start_watch()` again against the Gmail API.
- **Frontend Visibility**: `LiveMonitor.jsx` calculates the remaining time from the server's timestamps, rendering contextual UI:
    - `"Real-time monitoring active"` (Standard)
    - `"Monitoring expires in X hours (auto-renewing...)"` (Within 24h grace period)
    - `"Real-time monitoring paused (expired)"` (If renewal fails entirely)
    - `"Monitoring renewal failed"` (With a manual **"Renew Monitoring"** fallback button).

## 2. OAuth Testing & Deployment Requirements
The backend relies on the strictly restricted `https://www.googleapis.com/auth/gmail.readonly` scope. 

Currently, the Google Cloud OAuth Consent Screen is configured for **External + Testing** mode. This imposes several critical constraints that the architecture correctly accommodates:
1. **Disconnected/Demo Experience**: The dashboard completely supports unauthenticated (demo) usage. If no Gmail is connected, the UI prompts connection seamlessly without crashing or forcing logins on unverified visitors.
2. **Test Users Only**: In Testing mode, only email addresses explicitly added to the Google Cloud "Test Users" list can authorize the application. **You must add the mentor's email address to the Test Users list** to allow them to test this application.
3. **Token Expiration**: In Testing mode, Google intentionally expires refresh tokens after exactly 7 days. This means the user (and the mentor) will be prompted to re-authorize weekly.
4. **Production Verification**: Moving the OAuth application from Testing to Production to allow unrestricted public sign-ins requires Google's mandatory App Verification process, since `gmail.readonly` allows access to restricted personal data. The current architecture successfully implements OAuth correctly but purposefully operates within the Testing limitations to avoid the months-long verification queue during development.

## 3. Endpoints & State Management
- `POST /api/gmail/renew-watch`: Explicit manual trigger for watch renewal.
- `GET /api/gmail/latest`: Polled every 5 seconds. Provides newly classified messages, monitors the connection state, and transparently handles the silent auto-renewal.
- The `monitoring_state` dictionary tracks the exact `expiration` and `renewal_status` to ensure idempotent, crash-proof behavior.

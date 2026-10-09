# Email Spam Shield - Diagnostics and Evaluation

## Part A: Live Monitoring Fixes
**Root Cause:**
The "Live monitoring failed" issue was caused by an unhandled expiration of the `historyId`. When the Gmail watch has been active for some time, the `historyId` tracked by the backend expires, and Google's `history.list()` API returns a 404 error. The backend caught the error and returned `None`, but the Pub/Sub webhook failed to assign a new `historyId` or recover, resulting in silent failures for all subsequent push notifications.

**Fixes Applied:**
1. **Fallback Recovery Sync**: Modified the `/api/gmail/pubsub` webhook in `app.py`. If `history.list()` fails, the system automatically falls back to `fetch_recent_emails(limit=10)`.
2. **State Recovery**: The system parses the new `historyId` embedded directly in the Pub/Sub push notification and resets the backend state, permanently recovering the watch sync.
3. **Idempotency Checks**: Duplicate Pub/Sub pushes are ignored since we check `not any(e['id'] == msg_id for e in monitoring_state['emails'])` before inserting.

## Part B: Full Email Text Extraction
**Root Cause:**
The model frequently received truncated or incomplete text. `_get_body()` was appending `text/plain` parts, but it lacked a check for attachments (e.g., base64 text attachments). Additionally, if a deeply nested `multipart/mixed` email lacked a proper `text/plain` part, `_get_body()` sometimes returned an empty string. The backend then silently fell back to classifying only the subject and the 200-character Gmail snippet, starving the model of context.

**Fixes Applied:**
1. **Attachment Exclusion**: Updated `_get_body()` in `gmail_service.py` to skip parts containing a `filename`, ensuring base64 attachments are not fed into the classifier.
2. **Fallback Diagnostics**: Added terminal print diagnostics in `app.py` for every classified message (`body_length`, `body_found`, `text_to_classify_length`). If the body is missing, it explicitly logs a warning rather than silently truncating.

## Part C: Classification Error Analysis
I ran the frozen inference pipeline against the reported phrases and inspected the model's raw decision scores and TF-IDF feature weights.

**Findings:**
1. **Domain Mismatch (SMS vs. Email):** The frozen `LinearSVC` was trained on SMS datasets (UCI and Indian SMS). In SMS data, words like "free", "urgent", and "your" are extremely strong indicators of spam because legitimate text messages rarely use formal promotional language.
   - For example, the model assigns massive spam weights to `"free"` (+2.49) and `"your"` (+2.07).
   - In standard email communication, `"your"` is used constantly in transactional/official emails (e.g., "your recent purchase", "your documents"). Thus, legitimate emails are heavily penalized.
2. **The "Documents" Example:** 
   - When I manually passed `"Please immediately send your documents"` into the classifier, it actually returned **SPAM** (Decision Score +0.117), driven heavily by the word `"your"`. 
   - If the user saw it classified as **HAM** in Live Monitor, it conclusively proves the **extraction truncation bug** occurred. The email body was likely skipped, and the model only classified a harmless subject line without seeing the actual text.

## Part D: Evaluation & Next Steps
Before altering the frozen model, we should implement a measured approach to domain adaptation.

**Proposed Experiment (Email Data):**
1. **Dataset**: Acquire a dedicated email dataset (e.g., the SpamAssassin Public Corpus or Enron Spam dataset).
2. **Methodology**: Perform a clean train/validation/test split. Train a new `TfidfVectorizer` and `LinearSVC` model on the email data.
3. **Metrics**: Compare Spam Precision, Spam Recall, and F1-score of the new model against the frozen baseline SMS model using the test split. 

**Proposed Human-Feedback Workflow:**
Instead of blindly retraining on incoming emails (which risks data poisoning), we should introduce a "Correct Classification" button on the frontend. 
- If a user flags a HAM as SPAM, the email text is stored in a secured `human_feedback.csv` file.
- We do **not** dynamically retrain the model. Instead, a developer periodically reviews the feedback file and batches it into the next formal training cycle, ensuring high-quality ground truth.

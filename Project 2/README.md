# PhishShift

> **ML-Powered Phishing Message Analysis**  
> *Understand suspicious messages before you trust them.*

PhishShift is a focused, modern cybersecurity application that analyzes SMS and email message content to detect potential phishing attempts. It pairs a supervised Linear Support Vector Classifier (LinearSVC) trained on TF-IDF n-grams with local, non-invasive URL structural analysis to provide actionable insights, clear explanations, and responsible handling of uncertain messages.

---

## 1. Key Features

- **Three-Outcome Classification:**
  - **Phishing** — The message text exhibits characteristics strongly associated with phishing by the trained model (SVM decision score $\ge +0.70$).
  - **Legitimate** — The message text falls below the decision boundary ($< 0.00$) and contains no configured URL structural warnings.
  - **Review Required** — The message's decision score falls in the uncertainty band ($0.00 \le \text{score} < +0.70$) or contains high-risk URL structural anomalies (e.g. raw IP hostnames, URL shorteners, brand impersonation).
- **Responsible SVM Decision Score Representation:**
  - Displays the geometric margin distance from the separating hyperplane.
  - Never misrepresents SVM margin scores as probabilities or percentage confidences.
  - Includes a visual scale indicating margin zones.
- **Local URL Structural Analysis:**
  - Extracts and inspects URL strings locally without making external DNS, HTTP, or reputation requests.
  - Identifies raw IP addresses, URL shorteners, excessive subdomains, high-risk TLDs, `@` symbols, and brand spoofing patterns.
  - URLs are rendered as plain non-clickable text to prevent accidental navigation.
- **Modern, Restrained Dark Interface:**
  - Built with React, Vite, and Lucide icons.
  - Deep charcoal backgrounds with subtle surface contrast, clear typography, and restrained emerald, amber, and red accents.
  - Responsive design supporting desktop, tablet, and mobile displays.

---

## 2. Architecture & File Structure

```
Project 2/
├── backend/
│   ├── app.py                     # Flask REST API server and error handlers
│   ├── predict.py                 # Artifact loader and 3-outcome inference engine
│   ├── url_analyzer.py            # Local syntactic URL analysis & risk detection
│   └── tests/
│       ├── test_url_analyzer.py   # Unit tests for URL structural analysis
│       ├── test_predict.py        # Integration tests for classification & thresholds
│       └── test_api.py            # Flask REST API endpoint tests
├── frontend/
│   ├── index.html                 # App shell with Inter typography
│   ├── package.json               # Frontend dependencies (React 19, Vite, Lucide)
│   ├── vite.config.js             # Vite config with backend proxy
│   └── src/
│       ├── App.jsx                # Core application state & layout
│       ├── index.css              # Custom cybersecurity dark theme
│       ├── main.jsx               # React DOM entrypoint
│       ├── components/
│       │   ├── Header.jsx         # Header with live engine status
│       │   ├── MessageInput.jsx   # Text input, char counter & quick samples
│       │   ├── PredictionResult.jsx # Status badge, score card & notices
│       │   ├── URLAnalysisSection.jsx # Safe URL structural breakdown
│       │   ├── InitialState.jsx   # Empty state prompt & feature pills
│       │   └── Footer.jsx         # Footer with safety disclaimer
│       └── services/
│           └── api.js             # REST API client
├── model/
│   ├── tfidf_vectorizer.joblib    # 15,000-feature TF-IDF vectorizer
│   ├── phishing_svm.joblib        # Trained scikit-learn LinearSVC model
│   └── threshold.joblib           # Review margin threshold (0.70)
└── README.md
```

---

## 3. Local Setup & Startup Guide

### Prerequisites
- Python 3.10+ (with `scikit-learn`, `flask`, `flask-cors`, and `joblib` installed)
- Node.js 18+ and npm

### Step 1: Start the Backend Service
From the `Project 2` root directory, execute:

```powershell
python backend/app.py
```
*The Flask server will start on `http://127.0.0.1:5000` and load the ML artifacts from `model/`.*

### Step 2: Start the Frontend Application
In a separate terminal, install dependencies and start the Vite development server:

```powershell
cd frontend
npm install
npm run dev
```
*The frontend dashboard will be available at `http://localhost:5173`.*

---

## 4. Running Backend Tests

The project includes unit, integration, and API tests:

```powershell
# Run URL structural analyzer tests
python -m unittest backend/tests/test_url_analyzer.py

# Run prediction & threshold margin tests
python -m unittest backend/tests/test_predict.py

# Run Flask REST API endpoint tests
python -m unittest backend/tests/test_api.py
```

---

## 5. Decision Logic & Margin Thresholds

| Margin Condition | Base Text Prediction | URL Warnings Present? | Final Classification | Reason / Behavior |
| :--- | :--- | :--- | :--- | :--- |
| $\text{Score} \ge 0.70$ | **Phishing** | Any | **Phishing** | "The message text was classified as phishing by the trained model." |
| $0.00 \le \text{Score} < 0.70$ | **Review Required** | Any | **Review Required** | "The model's score falls within the configured review threshold." |
| $\text{Score} < 0.00$ | **Legitimate** | Yes | **Review Required** | "The message text was classified as legitimate, but URL structural warnings were found. Additional verification is recommended." |
| $\text{Score} < 0.00$ | **Legitimate** | No | **Legitimate** | "The message was classified as legitimate, and no configured URL structural warnings were found." |

---

## 6. Security Constraints & Responsible Communication

1. **No External Network Calls for URLs:** URLs submitted by users are strictly inspected through local string parsing and regular expressions. The backend never performs DNS lookups, HTTP `GET`/`HEAD` requests, or submissions to external third-party threat intelligence APIs.
2. **No Guaranteed Safety:** Legitimate classifications explicitly state that no configured indicators were detected; they never guarantee that a message or link is completely safe.
3. **Non-Executable URLs:** Extracted URLs are rendered in plaintext code boxes without hyperlinks to prevent accidental clicks.

---

## 7. Known Limitations

- **Novel Campaign Wording:** Like all statistical NLP models, unfamiliar vocabulary or obfuscation tactics (e.g. zero-width characters, homoglyphs in text) can result in borderline scores requiring review.
- **Legitimate Urgent Messages:** Urgent legitimate notifications (e.g. legitimate password reset OTPs or critical flight alerts) may score closer to the decision boundary than conversational text.
- **URL Syntactic Scope:** Syntactic analysis inspects structure only (IP hostnames, shorteners, TLDs, subdomains); it cannot assess server payload changes or newly registered benign domains that turn malicious after inspection.

"""
Prediction Service for PhishShift.

Loads trained TF-IDF vectorizer, LinearSVC model, and review threshold artifacts.
Combines machine learning decision scoring with URL structural analysis.
"""

import os
import joblib
import numpy as np

try:
    from .url_analyzer import analyze_all_urls
    from .content_analyzer import analyze_message_content, explain_model_words
except ImportError:
    from url_analyzer import analyze_all_urls
    from content_analyzer import analyze_message_content, explain_model_words

# Module-level singletons for artifacts
_vectorizer = None
_model = None
_threshold = None
_models_loaded = False


def get_model_directory() -> str:
    """
    Resolves the directory containing the saved ML artifacts
    relative to the backend application location.
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    # Try sibling directory '../model' first (standard project root layout)
    candidate_1 = os.path.abspath(os.path.join(backend_dir, "..", "model"))
    if os.path.isdir(candidate_1):
        return candidate_1
    # Fallback to local 'model' directory inside backend
    candidate_2 = os.path.abspath(os.path.join(backend_dir, "model"))
    if os.path.isdir(candidate_2):
        return candidate_2
    # Default to candidate_1
    return candidate_1


def load_artifacts() -> None:
    """
    Loads saved vectorizer, model, and threshold artifacts once on startup.
    Raises RuntimeError with clear diagnostics if any artifact is missing or fails to load.
    """
    global _vectorizer, _model, _threshold, _models_loaded

    model_dir = get_model_directory()
    vec_path = os.path.join(model_dir, "tfidf_vectorizer.joblib")
    model_path = os.path.join(model_dir, "phishing_svm.joblib")
    thresh_path = os.path.join(model_dir, "threshold.joblib")

    missing = []
    for path, name in [
        (vec_path, "tfidf_vectorizer.joblib"),
        (model_path, "phishing_svm.joblib"),
        (thresh_path, "threshold.joblib"),
    ]:
        if not os.path.exists(path):
            missing.append(f"{name} (expected at {path})")

    if missing:
        raise RuntimeError(
            f"Failed to initialize PhishShift ML engine. Missing required model artifact(s): {', '.join(missing)}"
        )

    try:
        _vectorizer = joblib.load(vec_path)
        _model = joblib.load(model_path)
        _threshold = float(joblib.load(thresh_path))
        _models_loaded = True
    except Exception as e:
        raise RuntimeError(f"Error loading model artifacts from {model_dir}: {str(e)}") from e


def is_loaded() -> bool:
    """Returns True if ML artifacts are initialized and ready."""
    return _models_loaded


def get_vectorizer():
    """Returns the loaded TF-IDF vectorizer artifact."""
    return _vectorizer


def get_model():
    """Returns the loaded LinearSVC model artifact."""
    return _model


def get_threshold():
    """Returns the configured review threshold float."""
    return _threshold


def predict_message(message: str) -> dict:
    """
    Analyzes an input message and returns structured classification results.

    Returns dictionary containing:
        - text_prediction: "Phishing" | "Legitimate" | "Review Required"
        - decision_score: float (raw SVM decision score, not a probability)
        - extracted_urls: list of str
        - url_analysis: list of dicts with structural risk inspection
        - final_prediction: "Phishing" | "Legitimate" | "Review Required"
        - reason: str explanation
    """
    if not _models_loaded:
        load_artifacts()

    # 1. Transform message text with TF-IDF vectorizer
    X = _vectorizer.transform([message])

    # 2. Compute LinearSVC decision margin score
    raw_score = float(_model.decision_function(X)[0])
    decision_score = round(raw_score, 4)

    # 3. Determine base text prediction using review threshold
    # The decision score is a distance from the hyperplane.
    # Scores >= threshold indicate high confidence phishing.
    # Scores < 0 indicate legitimate leaning.
    # Scores in [0, threshold) represent uncertain / borderline cases.
    if decision_score >= _threshold:
        text_prediction = "Phishing"
    elif decision_score < 0.0:
        text_prediction = "Legitimate"
    else:
        text_prediction = "Review Required"

    # 4. Extract and structurally inspect any embedded URLs
    extracted_urls, url_analysis, has_url_warnings = analyze_all_urls(message)

    # 5. Determine final classification and supporting reason
    if text_prediction == "Phishing":
        final_prediction = "Phishing"
        reason = "The message text was classified as phishing by the trained model."
    elif text_prediction == "Review Required":
        final_prediction = "Review Required"
        reason = "The model's score falls within the configured review threshold."
    else:
        # text_prediction is Legitimate
        if has_url_warnings:
            # Conservative review behaviour triggered by URL structural risks
            final_prediction = "Review Required"
            reason = "The message text was classified as legitimate, but URL structural warnings were found. Additional verification is recommended."
        else:
            final_prediction = "Legitimate"
            reason = "The message was classified as legitimate, and no configured URL structural warnings were found."

    # 6. Generate user-friendly supporting message reports
    content_analysis = analyze_message_content(message)
    word_influences = explain_model_words(message, _vectorizer, _model, final_prediction)

    return {
        "text_prediction": text_prediction,
        "decision_score": decision_score,
        "extracted_urls": extracted_urls,
        "url_analysis": url_analysis,
        "final_prediction": final_prediction,
        "reason": reason,
        "content_analysis": content_analysis,
        "word_influences": word_influences
    }

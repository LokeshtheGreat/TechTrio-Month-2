"""
Flask Application for PhishShift API.

Exposes REST endpoints for message analysis and model health check.
Configures CORS for local frontend communication.
"""

import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from .predict import load_artifacts, predict_message, is_loaded
except ImportError:
    from predict import load_artifacts, predict_message, is_loaded

# Setup clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PhishShift")

app = Flask(__name__)
# Enable CORS for local development (Vite typically runs on 5173)
CORS(app, resources={r"/*": {"origins": "*"}})

MAX_MESSAGE_LENGTH = 5000

# Load model artifacts once on startup
try:
    load_artifacts()
    logger.info("PhishShift ML artifacts successfully loaded and ready for inference.")
except Exception as e:
    logger.error("CRITICAL: Failed to load PhishShift model artifacts: %s", str(e))
    # Note: Application continues so health check can report status, but /predict will fail safely


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend status and artifact availability."""
    return jsonify({
        "status": "healthy" if is_loaded() else "degraded",
        "service": "PhishShift Phishing Analysis API",
        "version": "1.0",
        "model_loaded": is_loaded()
    }), 200 if is_loaded() else 503


@app.route("/predict", methods=["POST"])
def predict():
    """
    Main prediction endpoint.
    Expects JSON payload: { "message": "..." }
    """
    if not is_loaded():
        logger.error("Predict endpoint called but model artifacts are not loaded.")
        return jsonify({
            "error": "Machine learning model artifacts are not loaded. Please verify model files and restart backend."
        }), 503

    if not request.is_json:
        return jsonify({
            "error": "Invalid request content-type. Expected application/json."
        }), 400

    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({
            "error": "Invalid JSON payload. Please provide a JSON object with a 'message' field."
        }), 400

    if "message" not in data:
        return jsonify({
            "error": "Missing required 'message' field in request body."
        }), 400

    raw_message = data.get("message")
    if not isinstance(raw_message, str):
        return jsonify({
            "error": "The 'message' field must be a text string."
        }), 400

    trimmed_message = raw_message.strip()
    if not trimmed_message:
        return jsonify({
            "error": "Message content cannot be empty or contain only whitespace."
        }), 400

    if len(raw_message) > MAX_MESSAGE_LENGTH:
        return jsonify({
            "error": f"Message length ({len(raw_message)} characters) exceeds the maximum allowed limit of {MAX_MESSAGE_LENGTH} characters."
        }), 400

    try:
        result = predict_message(trimmed_message)
        return jsonify(result), 200
    except Exception as e:
        logger.error("Unexpected error during message prediction: %s", str(e), exc_info=True)
        return jsonify({
            "error": "An unexpected error occurred while analyzing the message. Please try again."
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting PhishShift Flask API server on port %d...", port)
    app.run(host="0.0.0.0", port=port, debug=False)

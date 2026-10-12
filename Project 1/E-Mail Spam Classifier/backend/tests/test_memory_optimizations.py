import os
import sys
import pytest

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.classifier import SpamClassifier
from app import app


def test_procfile_memory_constrained_configuration():
    """Verify Procfile configures single-worker gthread concurrency and request recycling."""
    procfile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Procfile'))
    assert os.path.exists(procfile_path), "Procfile must exist in backend root"
    
    with open(procfile_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    assert "--workers 1" in content, "Procfile must constrain Gunicorn to 1 worker process"
    assert "--worker-class gthread" in content, "Procfile must use gthread worker class for low memory"
    assert "--threads" in content, "Procfile must specify thread-based concurrency"
    assert "--max-requests" in content, "Procfile must specify max-requests for worker recycling"


def test_requirements_excludes_unused_pandas():
    """Verify backend requirements.txt does not include pandas."""
    req_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'requirements.txt'))
    with open(req_path, 'r', encoding='utf-8') as f:
        lines = [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]

    assert 'pandas' not in lines, "pandas is unused and must be omitted from requirements.txt"


def test_classifier_handles_oversized_payload_safely():
    """Verify SpamClassifier gracefully truncates oversized messages to protect memory."""
    classifier = SpamClassifier()
    # Construct a 100 KB repetitive payload
    large_spam_payload = "FREE lottery prize claim now! " * 4000
    assert len(large_spam_payload) > 100000

    result = classifier.predict(large_spam_payload)
    assert result is not None
    assert 'prediction' in result
    assert result['prediction'] in ['SPAM', 'HAM']
    assert 'indicators' in result
    assert isinstance(result['indicators'], list)


def test_predict_api_handles_large_message():
    """Verify /api/predict handles large messages without HTTP 500 error."""
    large_msg = "Exclusive promotional offer! Urgent claim code inside. " * 1000
    with app.test_client() as client:
        res = client.post('/api/predict', json={'message': large_msg})
        assert res.status_code == 200
        data = res.get_json()
        assert 'prediction' in data
        assert data['prediction'] in ['SPAM', 'HAM']

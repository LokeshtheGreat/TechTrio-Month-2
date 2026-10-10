import pytest
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.classifier import SpamClassifier
from app import app

def test_classifier_loads_artifacts():
    """Verify that model and vectorizer artifacts load cleanly."""
    classifier = SpamClassifier()
    assert classifier.model is not None
    assert classifier.vectorizer is not None
    assert len(classifier.feature_names) > 0

def test_classifier_predict_spam():
    """Verify inference for a prototypical spam message."""
    classifier = SpamClassifier()
    result = classifier.predict("WINNER!! You have won a FREE cash prize! Claim immediately.")
    assert result['prediction'] == 'SPAM'
    assert 'decision_score' in result
    assert result['decision_score'] > 0
    assert 'indicators' in result
    assert isinstance(result['indicators'], list)

def test_classifier_predict_ham():
    """Verify inference for a prototypical ham message."""
    classifier = SpamClassifier()
    result = classifier.predict("Hey, are we still meeting for lunch at 1pm?")
    assert result['prediction'] == 'HAM'
    assert 'decision_score' in result
    assert result['decision_score'] < 0
    assert 'indicators' in result

def test_predict_api_endpoint():
    """Verify that the /api/predict HTTP route returns the expected JSON structure."""
    with app.test_client() as client:
        res = client.post('/api/predict', json={'message': 'Urgent account verification needed'})
        assert res.status_code == 200
        data = res.get_json()
        assert 'prediction' in data
        assert data['prediction'] in ['HAM', 'SPAM']
        assert 'strength' in data
        assert 'indicators' in data

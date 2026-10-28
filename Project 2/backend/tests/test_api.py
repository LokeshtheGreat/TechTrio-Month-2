"""
API integration tests for PhishShift Flask REST endpoints.
"""

import sys
import os
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["model_loaded"])

    def test_health_check_payload_fields(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("status", data)
        self.assertIn("service", data)
        self.assertIn("version", data)
        self.assertIn("model_loaded", data)
        self.assertEqual(data["service"], "PhishShift Phishing Analysis API")

    def test_cors_headers(self):
        # Health check should return Access-Control-Allow-Origin
        response = self.client.get("/health")
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")

        # Predict options preflight
        preflight = self.client.options("/predict")
        self.assertEqual(preflight.status_code, 200)
        self.assertEqual(preflight.headers.get("Access-Control-Allow-Origin"), "*")

    def test_predict_success(self):
        payload = {"message": "Urgent: Your account is suspended. Verify at http://192.168.1.1"}
        response = self.client.post(
            "/predict",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("final_prediction", data)
        self.assertIn("decision_score", data)
        self.assertIn("url_analysis", data)
        self.assertIn("reason", data)

    def test_empty_message_validation(self):
        payload = {"message": "   "}
        response = self.client.post(
            "/predict",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("cannot be empty", data.get("error", ""))

    def test_missing_message_field(self):
        payload = {"text": "hello"}
        response = self.client.post(
            "/predict",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("Missing required 'message'", data.get("error", ""))

    def test_exceeding_max_length(self):
        payload = {"message": "a" * 5001}
        response = self.client.post(
            "/predict",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("exceeds the maximum allowed limit", data.get("error", ""))


if __name__ == "__main__":
    unittest.main()

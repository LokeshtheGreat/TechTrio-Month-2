"""
Integration tests for PhishShift Prediction Engine.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from predict import load_artifacts, predict_message, is_loaded


class TestPredict(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        load_artifacts()

    def test_artifacts_loaded(self):
        self.assertTrue(is_loaded())

    def test_phishing_message(self):
        msg = "URGENT: Your bank account has been suspended due to suspicious activity. Log in immediately to verify your identity: http://192.168.1.1/login"
        res = predict_message(msg)
        self.assertEqual(res["final_prediction"], "Phishing")
        self.assertGreaterEqual(res["decision_score"], 0.70)
        self.assertIn("classified as phishing", res["reason"])
        self.assertGreater(len(res["extracted_urls"]), 0)

    def test_legitimate_message_without_urls(self):
        msg = "Hi team, please find attached the minutes from today's sync. Let me know if any updates are needed."
        res = predict_message(msg)
        self.assertEqual(res["final_prediction"], "Legitimate")
        self.assertLess(res["decision_score"], 0.0)
        self.assertEqual(len(res["extracted_urls"]), 0)
        self.assertIn("no configured URL structural warnings were found", res["reason"])

    def test_review_required_due_to_url_warning(self):
        # A message with legitimate text (score < 0) but containing a high-risk URL
        msg = "Hi John, can you review the document when you get a chance? http://192.168.1.1/doc"
        res = predict_message(msg)
        self.assertEqual(res["text_prediction"], "Legitimate")
        self.assertEqual(res["final_prediction"], "Review Required")
        self.assertIn("URL structural warnings", res["reason"])

    def test_review_required_due_to_threshold(self):
        # A message with intermediate score (0.0 <= score < 0.7)
        msg = "Please verify your email address to complete registration."
        res = predict_message(msg)
        self.assertGreaterEqual(res["decision_score"], 0.0)
        self.assertLess(res["decision_score"], 0.7)
        self.assertEqual(res["text_prediction"], "Review Required")
        self.assertEqual(res["final_prediction"], "Review Required")
        self.assertIn("falls within the configured review threshold", res["reason"])


if __name__ == "__main__":
    unittest.main()

"""
Tests for Message Content Analysis and Model Word Explanations.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from content_analyzer import analyze_message_content, explain_model_words
from predict import load_artifacts, predict_message, is_loaded, get_vectorizer, get_model


class TestContentAnalyzer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        load_artifacts()

    def test_urgent_wording_detected(self):
        text = "Please act immediately to avoid disruption."
        res = analyze_message_content(text)
        self.assertTrue(res["has_findings"])
        self.assertTrue(any(f["category"] == "Urgent or Pressuring Language" for f in res["findings"]))
        match = next(f for f in res["findings"] if f["category"] == "Urgent or Pressuring Language")
        self.assertIn("immediately", match["excerpt"].lower())

    def test_account_threat_detected(self):
        text = "Your account has been suspended due to unauthorized access."
        res = analyze_message_content(text)
        self.assertTrue(res["has_findings"])
        self.assertTrue(any(f["category"] == "Account or Security Alerts" for f in res["findings"]))

    def test_sensitive_info_request_detected(self):
        text = "Please update your password and provide your OTP to continue."
        res = analyze_message_content(text)
        self.assertTrue(res["has_findings"])
        self.assertTrue(any(f["category"] == "Sensitive Information Request" for f in res["findings"]))

    def test_prize_reward_detected(self):
        text = "Congratulations! You won a $1000 gift card! Claim your prize now."
        res = analyze_message_content(text)
        self.assertTrue(res["has_findings"])
        self.assertTrue(any(f["category"] == "Unexpected Prize or Offer" for f in res["findings"]))

    def test_ordinary_legitimate_message_no_false_alarm(self):
        text = "Hi team, please find attached the minutes from today's sync. Let me know if any updates are needed."
        res = analyze_message_content(text)
        self.assertFalse(res["has_findings"])
        self.assertEqual(res["summary"], "No obvious suspicious wording was detected.")
        self.assertEqual(len(res["findings"]), 0)

    def test_empty_and_whitespace_input(self):
        self.assertFalse(analyze_message_content("")["has_findings"])
        self.assertFalse(analyze_message_content("   ")["has_findings"])
        self.assertFalse(analyze_message_content(None)["has_findings"])

    def test_model_words_phishing_message(self):
        msg = "URGENT: Your bank account has been suspended. Click here immediately to verify your identity: http://192.168.1.1/login"
        explanation = explain_model_words(msg, get_vectorizer(), get_model(), "Phishing")
        self.assertTrue(explanation["has_influences"])
        self.assertGreater(len(explanation["suspicious_words"]), 0)
        self.assertIn("suspicious result", explanation["suspicious_note"].lower())
        # Check that top words like urgent or click are in suspicious_words
        found_expected = any(w in explanation["suspicious_words"] for w in ["urgent", "http", "click", "your", "account", "verify"])
        self.assertTrue(found_expected)

    def test_model_words_legitimate_message(self):
        msg = "Hi team, are we still having our weekly sync tomorrow? Let me know."
        explanation = explain_model_words(msg, get_vectorizer(), get_model(), "Legitimate")
        self.assertTrue(explanation["has_influences"])
        self.assertGreater(len(explanation["legitimate_words"]), 0)
        self.assertIn("ordinary messages", explanation["legitimate_note"].lower())

    def test_borderline_review_required_consistency(self):
        msg = "Please verify your email address to complete your account registration."
        pred = predict_message(msg)
        self.assertEqual(pred["final_prediction"], "Review Required")
        # Check that word influences are populated and consistent
        self.assertIn("word_influences", pred)
        self.assertIn("content_analysis", pred)
        self.assertIn("borderline", pred["word_influences"]["summary"].lower())

    def test_message_with_suspicious_url_and_ordinary_text(self):
        msg = "Hi John, can you review the document when you get a chance? http://192.168.1.1/doc"
        pred = predict_message(msg)
        # Final prediction should be Review Required due to conservative URL escalation
        self.assertEqual(pred["final_prediction"], "Review Required")
        self.assertTrue(len(pred["url_analysis"]) > 0)
        self.assertIn("content_analysis", pred)
        self.assertIn("word_influences", pred)


if __name__ == "__main__":
    unittest.main()

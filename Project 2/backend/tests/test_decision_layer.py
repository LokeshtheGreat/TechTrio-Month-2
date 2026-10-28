"""
Unit and Integration Tests for URL-Aware Final Decision Layer.

Covers:
1. Legitimate-looking .xyz URLs without other suspicious signals (should not be Phishing).
2. Suspicious lookalike hostnames (e.g. trusted.example.xyz where brand is not registered domain).
3. Exact trusted-host matching vs deceptive subdomains (never trust brand in subdomain).
4. Messages without URLs (retains existing SVM behavior).
5. Multiple URLs, malformed URLs, and mixed evidence.
6. Regression tests confirming all existing prediction and analysis fields remain present.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from predict import load_artifacts, predict_message, is_loaded
from url_analyzer import analyze_url_structure, parse_domain_components, DEFAULT_TRUSTED_DOMAINS
from decision_layer import evaluate_final_decision


class TestDecisionLayer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        load_artifacts()

    def test_artifacts_ready(self):
        self.assertTrue(is_loaded())

    def test_legitimate_looking_xyz_url_not_phishing(self):
        """
        Legitimate-looking .xyz URL without other suspicious signals must NEVER be classified as Phishing.
        A TLD alone is a weak signal and does not override legitimate text.
        """
        msg = "Hi John, can you review the document when you get a chance? https://alexander-design.xyz"
        res = predict_message(msg)

        # Ambient text prediction is Legitimate
        self.assertEqual(res["text_prediction"], "Legitimate")
        # Final prediction MUST NOT be Phishing
        self.assertNotEqual(res["final_prediction"], "Phishing")
        # In fact, with no strong signals, it evaluates as Legitimate
        self.assertEqual(res["final_prediction"], "Legitimate")
        self.assertIn("uncommon top-level domain", res["reason"].lower())

        # URL analysis verifies .xyz is treated as weak signal
        self.assertEqual(len(res["url_analysis"]), 1)
        url_info = res["url_analysis"][0]
        self.assertFalse(url_info["has_high_risk"])
        self.assertEqual(len(url_info["strong_signals"]), 0)
        self.assertTrue(any(".xyz" in w for w in url_info["weak_signals"]))

    def test_suspicious_lookalike_hostname_deceptive_subdomain(self):
        """
        Suspicious lookalike hostname (e.g. trusted.example.xyz where trusted brand is not the registered domain).
        Should identify deceptive subdomain and escalate legitimate text to Review Required.
        """
        # 1. Structural check directly
        analysis = analyze_url_structure("https://trusted.example.xyz/portal")
        self.assertEqual(analysis["registered_domain"], "example.xyz")
        self.assertEqual(analysis["subdomain"], "trusted")
        self.assertTrue(analysis["is_deceptive_subdomain"])
        self.assertTrue(analysis["has_high_risk"])
        self.assertEqual(analysis["risk_level"], "High")

        # 2. End-to-end prediction: benign text + deceptive subdomain URL
        msg = "Hi John, can you review the document when you get a chance? https://trusted.example.xyz/portal"
        res = predict_message(msg)

        self.assertEqual(res["text_prediction"], "Legitimate")
        # Due to strong URL risk (deceptive subdomain), verdict MUST escalate to Review Required
        self.assertEqual(res["final_prediction"], "Review Required")
        self.assertIn("URL structural warnings", res["reason"])

    def test_exact_trusted_host_matching_vs_deceptive_subdomain(self):
        """
        Exact trusted-host matching must recognize genuine domains from the allowlist,
        while rejecting deceptive subdomains where a trusted brand appears in the subdomain.
        """
        # Case A: Genuine trusted host (accounts.google.com)
        genuine = analyze_url_structure("https://accounts.google.com/signin")
        self.assertTrue(genuine["is_trusted_domain"])
        self.assertEqual(genuine["matched_trusted_domain"], "google.com")
        self.assertFalse(genuine["is_deceptive_subdomain"])
        self.assertFalse(genuine["has_high_risk"])
        self.assertEqual(genuine["risk_level"], "Low")

        # Case B: Genuine trusted host with benign message
        msg_genuine = "Hi John, can you review the document when you get a chance? https://google.com"
        res_genuine = predict_message(msg_genuine)
        self.assertEqual(res_genuine["text_prediction"], "Legitimate")
        self.assertEqual(res_genuine["final_prediction"], "Legitimate")
        self.assertIn("trusted domain", res_genuine["reason"].lower())

        # Case C: Deceptive subdomain attempting to impersonate google (google.com.evil-portal.net)
        deceptive = analyze_url_structure("https://google.com.evil-portal.net/login")
        self.assertEqual(deceptive["registered_domain"], "evil-portal.net")
        # MUST NOT be trusted
        self.assertFalse(deceptive["is_trusted_domain"])
        # MUST be flagged as deceptive subdomain
        self.assertTrue(deceptive["is_deceptive_subdomain"])
        self.assertTrue(deceptive["has_high_risk"])

        msg_deceptive = "Hi John, can you review the document when you get a chance? https://google.com.evil-portal.net/login"
        res_deceptive = predict_message(msg_deceptive)
        self.assertEqual(res_deceptive["text_prediction"], "Legitimate")
        self.assertEqual(res_deceptive["final_prediction"], "Review Required")

    def test_never_guarantee_safety_even_for_trusted_domain(self):
        """
        Phishing text must NOT be overridden by a trusted domain URL (trusted domains do not guarantee safety).
        """
        phishing_msg = (
            "Congratulations! You have won a free Walmart gift card. "
            "Claim your prize now before it expires today! Click to verify: https://google.com"
        )
        res = predict_message(phishing_msg)
        # Even with google.com in the URL, phishing text remains Phishing
        self.assertEqual(res["final_prediction"], "Phishing")
        self.assertIn("classified as phishing", res["reason"])

    def test_messages_with_no_urls(self):
        """
        Messages without URLs must retain exact existing SVM behavior.
        """
        # Benign message without URLs
        benign_msg = "Hi team, please find attached the minutes from today sync. Let me know if any updates are needed."
        res_benign = predict_message(benign_msg)
        self.assertEqual(res_benign["text_prediction"], "Legitimate")
        self.assertEqual(res_benign["final_prediction"], "Legitimate")
        self.assertEqual(len(res_benign["extracted_urls"]), 0)
        self.assertEqual(len(res_benign["url_analysis"]), 0)

        # Phishing message without URLs
        phishing_msg = "Congratulations! You have won a free Walmart gift card. Claim your prize now before it expires today! Click to verify."
        res_phish = predict_message(phishing_msg)
        self.assertEqual(res_phish["final_prediction"], "Phishing")
        self.assertEqual(len(res_phish["extracted_urls"]), 0)

    def test_multiple_urls_mixed_evidence(self):
        """
        Messages with multiple URLs must inspect ALL URLs without silently ignoring suspicious ones.
        A trusted URL must not mask an IP or deceptive URL.
        """
        msg = "Hi John, can you review the document when you get a chance? https://google.com and http://192.168.1.100/admin"
        res = predict_message(msg)

        # Both URLs must be extracted and analyzed
        self.assertEqual(len(res["extracted_urls"]), 2)
        self.assertEqual(len(res["url_analysis"]), 2)

        # URL 1 is trusted, URL 2 is raw IP
        has_trusted = any(u["is_trusted_domain"] for u in res["url_analysis"])
        has_ip = any(u["is_ip"] for u in res["url_analysis"])
        self.assertTrue(has_trusted)
        self.assertTrue(has_ip)

        # Final verdict must escalate to Review Required because of the IP URL
        self.assertEqual(res["text_prediction"], "Legitimate")
        self.assertEqual(res["final_prediction"], "Review Required")
        self.assertIn("URL structural warnings", res["reason"])

    def test_malformed_urls_safe_handling(self):
        """
        Malformed URLs must not cause crashes and must be flagged safely.
        """
        malformed = analyze_url_structure("http://:::80/invalid")
        self.assertIn(malformed["risk_level"], ("High", "Medium"))
        self.assertTrue(len(malformed["warnings"]) > 0)
        self.assertTrue(malformed["has_high_risk"])

        msg = "Hi John, can you review the document when you get a chance? http://:::80/invalid"
        res = predict_message(msg)
        self.assertEqual(res["final_prediction"], "Review Required")

    def test_regression_existing_prediction_and_analysis_fields(self):
        """
        Regression test: ensures all expected JSON fields and structures remain intact.
        """
        msg = "Urgent: Your account is suspended. Verify credentials at http://192.168.1.1"
        res = predict_message(msg)

        # Top-level required keys
        expected_keys = {
            "text_prediction",
            "decision_score",
            "extracted_urls",
            "url_analysis",
            "final_prediction",
            "reason",
            "content_analysis",
            "word_influences"
        }
        for key in expected_keys:
            self.assertIn(key, res, f"Missing required response key: {key}")

        self.assertIsInstance(res["decision_score"], float)
        self.assertIsInstance(res["extracted_urls"], list)
        self.assertIsInstance(res["url_analysis"], list)
        self.assertIsInstance(res["content_analysis"], dict)
        self.assertIsInstance(res["word_influences"], dict)

        # Content analysis structure
        self.assertIn("findings", res["content_analysis"])
        self.assertIn("has_findings", res["content_analysis"])
        self.assertIn("summary", res["content_analysis"])

        # Word influences structure
        self.assertIn("suspicious_words", res["word_influences"])
        self.assertIn("legitimate_words", res["word_influences"])

        # URL analysis item structure
        self.assertGreater(len(res["url_analysis"]), 0)
        item = res["url_analysis"][0]
        expected_url_keys = {"url", "hostname", "risk_level", "warnings", "has_high_risk", "notice"}
        for u_key in expected_url_keys:
            self.assertIn(u_key, item, f"Missing required url_analysis key: {u_key}")


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for URL Structural Analyzer.
"""

import sys
import os
import unittest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from url_analyzer import extract_urls, analyze_url_structure, analyze_all_urls


class TestUrlAnalyzer(unittest.TestCase):

    def test_extract_urls(self):
        text = "Check http://192.168.1.1/login or visit www.example.com/test today! Also contact me@domain.com"
        urls = extract_urls(text)
        self.assertIn("http://192.168.1.1/login", urls)
        self.assertIn("www.example.com/test", urls)
        # Should not include plain email address
        self.assertNotIn("me@domain.com", urls)

    def test_ip_address_url(self):
        result = analyze_url_structure("http://192.168.1.1/login")
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(result["has_high_risk"])
        self.assertTrue(any("raw IP address" in w for w in result["warnings"]))

    def test_shortener_url(self):
        result = analyze_url_structure("https://bit.ly/3xY9zQ")
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(any("shortening service" in w for w in result["warnings"]))

    def test_high_risk_tld(self):
        result = analyze_url_structure("http://verify-identity.xyz")
        self.assertIn(result["risk_level"], ("High", "Medium"))
        self.assertTrue(any("high-risk top-level domain" in w for w in result["warnings"]))

    def test_brand_spoofing(self):
        result = analyze_url_structure("http://paypal.login-security-update.com/signin")
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(any("paypal" in w.lower() for w in result["warnings"]))

    def test_at_symbol_in_url(self):
        result = analyze_url_structure("http://google.com@attacker.com/login")
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(any("@" in w for w in result["warnings"]))

    def test_legitimate_url_clean(self):
        result = analyze_url_structure("https://docs.python.org/3/library/unittest.html")
        self.assertEqual(result["risk_level"], "Low")
        self.assertEqual(len(result["warnings"]), 0)


if __name__ == "__main__":
    unittest.main()

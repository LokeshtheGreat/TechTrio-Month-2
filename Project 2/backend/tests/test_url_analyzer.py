"""
Unit tests for URL Structural Analyzer.
"""

import sys
import os
import unittest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from url_analyzer import (
    extract_urls,
    analyze_url_structure,
    analyze_all_urls,
    parse_domain_components,
    DEFAULT_TRUSTED_DOMAINS
)


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
        self.assertTrue(result["is_ip"])
        self.assertTrue(any("raw IP address" in w for w in result["warnings"]))
        self.assertIn("URL uses a raw IP address instead of a registered domain name.", result["strong_signals"])

    def test_shortener_url(self):
        result = analyze_url_structure("https://bit.ly/3xY9zQ")
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(result["is_shortener"])
        self.assertTrue(any("shortening service" in w for w in result["warnings"]))

    def test_high_risk_tld(self):
        result = analyze_url_structure("http://verify-identity.xyz")
        self.assertIn(result["risk_level"], ("High", "Medium"))
        self.assertTrue(any("high-risk top-level domain" in w for w in result["warnings"]))

    def test_weak_signals_only_for_xyz_and_biz(self):
        """
        TLD category (.xyz, .biz) must be treated strictly as weak signals,
        meaning has_high_risk must be False and strong_signals must be empty.
        """
        for tld in ("xyz", "biz"):
            result = analyze_url_structure(f"https://company-blog.{tld}")
            self.assertFalse(result["has_high_risk"])
            self.assertEqual(len(result["strong_signals"]), 0)
            self.assertTrue(any(f".{tld}" in w for w in result["weak_signals"]))

    def test_brand_spoofing(self):
        result = analyze_url_structure("http://paypal.login-security-update.com/signin")
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(result["is_deceptive_subdomain"])
        self.assertTrue(any("paypal" in w.lower() for w in result["warnings"]))

    def test_at_symbol_in_url(self):
        result = analyze_url_structure("http://google.com@attacker.com/login")
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(any("@" in w for w in result["warnings"]))

    def test_legitimate_url_clean(self):
        result = analyze_url_structure("https://docs.python.org/3/library/unittest.html")
        self.assertEqual(result["risk_level"], "Low")
        self.assertEqual(len(result["warnings"]), 0)
        self.assertFalse(result["has_high_risk"])

    def test_parse_domain_components(self):
        # Standard 2-level domain
        comp1 = parse_domain_components("blog.example.com")
        self.assertEqual(comp1["registered_domain"], "example.com")
        self.assertEqual(comp1["subdomain"], "blog")
        self.assertEqual(comp1["tld"], "com")
        self.assertFalse(comp1["is_ip"])

        # Multi-part public suffix (e.g. .co.uk)
        comp2 = parse_domain_components("auth.service.paypal.co.uk")
        self.assertEqual(comp2["registered_domain"], "paypal.co.uk")
        self.assertEqual(comp2["subdomain"], "auth.service")
        self.assertEqual(comp2["tld"], "co.uk")

        # IP address
        comp3 = parse_domain_components("192.168.1.1")
        self.assertEqual(comp3["registered_domain"], "192.168.1.1")
        self.assertTrue(comp3["is_ip"])

        # Trailing dot normalization
        comp4 = parse_domain_components("google.com.")
        self.assertEqual(comp4["registered_domain"], "google.com")

    def test_trusted_domain_matching(self):
        # Genuine trusted root and subdomain
        res1 = analyze_url_structure("https://google.com")
        self.assertTrue(res1["is_trusted_domain"])
        self.assertEqual(res1["matched_trusted_domain"], "google.com")

        res2 = analyze_url_structure("https://drive.google.com/folder")
        self.assertTrue(res2["is_trusted_domain"])
        self.assertEqual(res2["matched_trusted_domain"], "google.com")

        # Deceptive subdomain: brand in subdomain of attacker domain MUST NOT be trusted
        res3 = analyze_url_structure("https://google.com.attacker.xyz/login")
        self.assertFalse(res3["is_trusted_domain"])
        self.assertTrue(res3["is_deceptive_subdomain"])
        self.assertTrue(res3["has_high_risk"])


if __name__ == "__main__":
    unittest.main()

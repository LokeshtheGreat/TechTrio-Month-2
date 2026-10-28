"""
URL Structural Analysis Module for PhishShift.

Inspects URL strings locally without making external network requests.
Identifies syntactic risk indicators (e.g. raw IP hostnames, URL shorteners,
high-risk TLDs, excessive subdomains, brand spoofing patterns).
"""

import re
import ipaddress
from urllib.parse import urlparse

# Regular expression to safely locate URLs in text without executing them
URL_REGEX = re.compile(
    r'(?i)\b(?:https?://|www\d{0,3}\.|\b[a-z0-9.-]+\.[a-z]{2,10}(?:/[^\s]*)?)'
    r'(?<![.,;!?])',
    re.IGNORECASE
)

# Known URL shortening services that mask final destination
KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "bit.do", "cutt.ly", "rebrand.ly", "rb.gy",
    "tiny.cc", "shorte.st", "bc.vc", "shorturl.at"
}

# High-risk TLDs frequently abused in rapid-turnaround phishing campaigns
HIGH_RISK_TLDS = {
    "xyz", "top", "tk", "ml", "ga", "cf", "gq", "buzz", "icu",
    "cam", "work", "click", "link", "zip", "mov", "fit", "surf",
    "bar", "rest", "gdn", "cfd", "sbs"
}

# Major targeted brands frequently targeted in domain spoofing / subdomains
HIGH_VALUE_TARGETS = {
    "paypal", "apple", "microsoft", "google", "netflix", "amazon",
    "chase", "bankofamerica", "wellsfargo", "citibank", "wellsfargo",
    "irs", "dhl", "fedex", "usps", "facebook", "instagram", "whatsapp",
    "crypto", "binance", "coinbase", "metamask", "steam"
}

# Legitimate root domains for high value targets to prevent false positives
LEGITIMATE_TARGET_DOMAINS = {
    "paypal": "paypal.com",
    "apple": "apple.com",
    "microsoft": "microsoft.com",
    "google": "google.com",
    "netflix": "netflix.com",
    "amazon": "amazon.com",
    "chase": "chase.com",
    "bankofamerica": "bankofamerica.com",
    "wellsfargo": "wellsfargo.com",
    "citibank": "citi.com",
    "irs": "irs.gov",
    "dhl": "dhl.com",
    "fedex": "fedex.com",
    "usps": "usps.com",
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "whatsapp": "whatsapp.com",
    "binance": "binance.com",
    "coinbase": "coinbase.com",
    "metamask": "metamask.io",
    "steam": "steampowered.com"
}


def extract_urls(text: str) -> list[str]:
    """
    Extracts URL candidate strings from input text without visiting them.
    Filters out lone email addresses and common punctuation artefacts.
    """
    if not text or not isinstance(text, str):
        return []

    # First find standard candidates
    raw_matches = re.findall(r'(?:https?://[^\s<>"\']+|www\.[^\s<>"\']+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}(?:/[^\s<>"\']*)?)', text)

    cleaned_urls = []
    seen = set()

    for item in raw_matches:
        # Strip trailing punctuation
        item = item.rstrip('.,;:!?)>"\'')
        
        # Skip email-like patterns (e.g. user@domain.com) if not a URL with scheme
        if '@' in item and not item.startswith(('http://', 'https://')):
            continue
            
        # Must contain at least one dot or be localhost
        if '.' not in item and 'localhost' not in item:
            continue

        # Standardise representation for analysis
        if item.lower() not in seen:
            seen.add(item.lower())
            cleaned_urls.append(item)

    return cleaned_urls


def analyze_url_structure(url_str: str) -> dict:
    """
    Performs purely local syntactic and structural inspection on a URL string.
    Never resolves DNS, fetches HTTP content, or contacts external reputation services.
    """
    warnings = []
    risk_level = "Low"
    high_risk_flag = False

    # Normalize scheme if omitted so urlparse parses netloc correctly
    normalized = url_str
    if not (url_str.startswith('http://') or url_str.startswith('https://')):
        normalized = 'http://' + url_str

    try:
        parsed = urlparse(normalized)
    except Exception:
        return {
            "url": url_str,
            "hostname": "Unknown",
            "risk_level": "High",
            "warnings": ["Malformed URL syntax that could not be parsed safely."],
            "has_high_risk": True,
            "notice": "Structural analysis inspects URL format only and does not verify server reputation or content safety."
        }

    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    path = parsed.path.lower()
    query = parsed.query.lower()

    if not hostname:
        return {
            "url": url_str,
            "hostname": "None",
            "risk_level": "Medium",
            "warnings": ["Could not extract a valid host name from URL string."],
            "has_high_risk": False,
            "notice": "Structural analysis inspects URL format only and does not verify server reputation or content safety."
        }

    # 1. IP address hostname check (IPv4 or IPv6)
    try:
        ipaddress.ip_address(hostname)
        warnings.append("URL uses a raw IP address instead of a registered domain name.")
        high_risk_flag = True
    except ValueError:
        pass

    # 2. Punycode / IDN homograph check
    if "xn--" in hostname:
        warnings.append("Hostname contains Punycode ('xn--'), frequently associated with homograph domain impersonation.")
        high_risk_flag = True

    # 3. '@' symbol in authority/path
    if '@' in parsed.netloc or '@' in url_str.split('?')[0]:
        warnings.append("URL contains '@' symbol, which can mislead users about the true destination host.")
        high_risk_flag = True

    # 4. Known URL shortener
    if hostname in KNOWN_SHORTENERS:
        warnings.append(f"Hostname is a known URL shortening service ({hostname}) that masks destination structure.")
        # Shorteners hide target, so they warrant conservative verification
        high_risk_flag = True

    # 5. High-risk TLD check
    tld = hostname.split('.')[-1] if '.' in hostname else ""
    if tld in HIGH_RISK_TLDS:
        warnings.append(f"Domain uses high-risk top-level domain (.{tld}) commonly seen in disposable phishing infrastructure.")

    # 6. Excessive subdomains check (e.g. auth.verify.login.service.com)
    labels = hostname.split('.')
    if len(labels) > 4:
        warnings.append(f"Excessive subdomain depth ({len(labels) - 2} levels) detected, often used to disguise host identity.")

    # 7. Brand spoofing / impersonation check
    for brand, legit_root in LEGITIMATE_TARGET_DOMAINS.items():
        if brand in hostname:
            # Check if domain actually ends with the legitimate root domain
            if not (hostname == legit_root or hostname.endswith('.' + legit_root)):
                warnings.append(f"Hostname references recognized brand '{brand}' but domain does not belong to '{legit_root}'.")
                high_risk_flag = True
                break
        elif brand in path:
            warnings.append(f"URL path references recognized brand '{brand}' under an unrelated domain ({hostname}).")

    # 8. Excessive hyphens in domain
    if hostname.count('-') >= 2:
        warnings.append(f"Hostname contains multiple hyphens ({hostname.count('-')}), typical of typo-squatting or deceptive names.")

    # 9. Non-standard port
    if port and port not in (80, 443):
        warnings.append(f"URL specifies a non-standard network port (:{port}).")

    # 10. Abnormal URL length
    if len(url_str) > 85:
        warnings.append(f"Abnormally long URL ({len(url_str)} characters), which may obfuscate parameters or payload strings.")

    # Determine overall structural risk level
    if high_risk_flag or len(warnings) >= 2:
        risk_level = "High"
    elif len(warnings) == 1:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "url": url_str,
        "hostname": hostname,
        "risk_level": risk_level,
        "warnings": warnings,
        "has_high_risk": high_risk_flag or (risk_level == "High"),
        "notice": "Structural analysis inspects URL format only and does not verify server reputation or content safety."
    }


def analyze_all_urls(text: str) -> tuple[list[str], list[dict], bool]:
    """
    Extracts and evaluates all URLs found in the text.
    Returns:
        (extracted_urls, analysis_list, has_structural_warnings)
    """
    urls = extract_urls(text)
    analysis_list = [analyze_url_structure(u) for u in urls]
    
    # Any URL with warnings triggers structural caution
    has_warnings = any(item["risk_level"] in ("High", "Medium") or len(item["warnings"]) > 0 for item in analysis_list)
    
    return urls, analysis_list, has_warnings

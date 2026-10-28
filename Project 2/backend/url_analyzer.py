"""
URL Structural Analysis Module for PhishShift.

Inspects URL strings locally without making external network requests.
Identifies syntactic and structural risk indicators (e.g. raw IP hostnames,
URL shorteners, suspicious TLDs, deceptive subdomains, brand spoofing patterns)
and matches against a configurable trusted-domain allowlist.

Safety Guarantee:
Never fetches, visits, or opens user-supplied URLs.
Matching a trusted domain does not guarantee safety.
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

# Small, clearly documented configurable trusted-domain allowlist
# Exact root domain matching only; legitimate subdomains inherit trust,
# but deceptive subdomains (e.g. google.com.attacker.xyz) are explicitly rejected.
DEFAULT_TRUSTED_DOMAINS = {
    "google.com",
    "microsoft.com",
    "apple.com",
    "amazon.com",
    "paypal.com",
    "github.com",
    "chase.com",
    "bankofamerica.com",
    "wellsfargo.com",
    "citi.com",
    "irs.gov",
    "who.int",
    "nih.gov",
    "cdc.gov",
}

# Multi-part public suffixes to accurately isolate registrable domains
MULTI_PART_PUBLIC_SUFFIXES = {
    "co.uk", "gov.uk", "org.uk", "ac.uk", "me.uk",
    "com.au", "net.au", "org.au", "gov.au", "edu.au",
    "co.nz", "org.nz", "govt.nz",
    "co.jp", "ne.jp", "ac.jp", "go.jp",
    "co.in", "gov.in", "ac.in", "res.in",
    "com.br", "gov.br",
    "com.mx", "gob.mx",
    "com.sg", "gov.sg",
    "co.za", "gov.za",
}

# Known URL shortening services that mask final destination
KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "bit.do", "cutt.ly", "rebrand.ly", "rb.gy",
    "tiny.cc", "shorte.st", "bc.vc", "shorturl.at"
}

# TLDs frequently abused in bulk campaigns — treated as WEAK SIGNALS ONLY.
# A TLD alone must never trigger a Phishing verdict.
WEAK_SIGNAL_TLDS = {
    "xyz", "biz", "top", "click", "link", "icu", "cam", "work",
    "buzz", "rest", "fit", "surf", "cfd", "sbs", "tk", "ml", "ga", "cf", "gq"
}

# Major targeted brands frequently targeted in domain spoofing / subdomains
HIGH_VALUE_TARGETS = {
    "paypal", "apple", "microsoft", "google", "netflix", "amazon",
    "chase", "bankofamerica", "wellsfargo", "citibank", "citi",
    "irs", "dhl", "fedex", "usps", "facebook", "instagram", "whatsapp",
    "crypto", "binance", "coinbase", "metamask", "steam", "trusted"
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
    "citi": "citi.com",
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
    "steam": "steampowered.com",
    "trusted": "trusted.org"
}


def get_default_trusted_domains() -> set[str]:
    """Returns a copy of the default trusted domains set."""
    return set(DEFAULT_TRUSTED_DOMAINS)


def parse_domain_components(hostname: str) -> dict:
    """
    Safely decomposes a normalized hostname into registered_domain, subdomain, and tld.
    Handles IPv4/IPv6 addresses, localhost, and multi-part public suffixes (e.g. .co.uk).
    """
    if not hostname:
        return {
            "registered_domain": "",
            "subdomain": "",
            "tld": "",
            "is_ip": False
        }

    # Normalize: strip trailing dots and lowercase
    clean_host = hostname.strip().rstrip('.').lower()

    # Check for raw IP address
    try:
        ipaddress.ip_address(clean_host)
        return {
            "registered_domain": clean_host,
            "subdomain": "",
            "tld": "",
            "is_ip": True
        }
    except ValueError:
        pass

    labels = clean_host.split('.')
    if len(labels) <= 1:
        return {
            "registered_domain": clean_host,
            "subdomain": "",
            "tld": "",
            "is_ip": False
        }

    # Check for multi-part public suffixes (e.g. co.uk, gov.uk, com.au)
    if len(labels) >= 3:
        two_part = f"{labels[-2]}.{labels[-1]}"
        if two_part in MULTI_PART_PUBLIC_SUFFIXES:
            registered_domain = f"{labels[-3]}.{two_part}"
            subdomain = ".".join(labels[:-3])
            tld = two_part
            return {
                "registered_domain": registered_domain,
                "subdomain": subdomain,
                "tld": tld,
                "is_ip": False
            }

    # Standard single-part TLD (e.g. example.com)
    tld = labels[-1]
    registered_domain = f"{labels[-2]}.{tld}"
    subdomain = ".".join(labels[:-2])
    return {
        "registered_domain": registered_domain,
        "subdomain": subdomain,
        "tld": tld,
        "is_ip": False
    }


def extract_urls(text: str) -> list[str]:
    """
    Extracts URL candidate strings from input text without visiting them.
    Filters out lone email addresses and common punctuation artefacts.
    """
    if not text or not isinstance(text, str):
        return []

    # Find standard candidates safely
    raw_matches = re.findall(
        r'(?:https?://[^\s<>"\']+|www\.[^\s<>"\']+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}(?:/[^\s<>"\']*)?)',
        text
    )

    cleaned_urls = []
    seen = set()

    for item in raw_matches:
        # Strip trailing punctuation
        item = item.rstrip('.,;:!?)>"\'')

        # Skip email-like patterns (e.g. user@domain.com) if not a URL with scheme
        if '@' in item and not item.startswith(('http://', 'https://')):
            continue

        # If not an explicit URL with scheme, require at least one dot or localhost to avoid normal words
        if not item.startswith(('http://', 'https://')):
            if '.' not in item and 'localhost' not in item:
                continue

        if item.lower() not in seen:
            seen.add(item.lower())
            cleaned_urls.append(item)

    return cleaned_urls


def analyze_url_structure(url_str: str, trusted_domains: set[str] = None) -> dict:
    """
    Performs purely local syntactic and structural inspection on a URL string.
    Never resolves DNS, fetches HTTP content, or contacts external reputation services.

    Signals are partitioned into:
    - strong_signals: IP hostnames, shorteners, punycode, '@' masking, deceptive subdomains, malformed syntax.
    - weak_signals: weak TLDs (.xyz, .biz), excessive subdomains, multiple hyphens, abnormal length, non-standard port.
    """
    if trusted_domains is None:
        trusted_domains = DEFAULT_TRUSTED_DOMAINS

    warnings = []
    strong_signals = []
    weak_signals = []
    is_trusted_domain = False
    matched_trusted_domain = None
    is_deceptive_subdomain = False
    is_shortener = False

    # Normalize scheme if omitted so urlparse parses netloc correctly
    normalized = url_str.strip()
    if not (normalized.startswith('http://') or normalized.startswith('https://')):
        normalized = 'http://' + normalized

    try:
        parsed = urlparse(normalized)
    except Exception:
        malformed_msg = "Malformed URL syntax that could not be parsed safely."
        return {
            "url": url_str,
            "hostname": "Unknown",
            "registered_domain": "",
            "subdomain": "",
            "tld": "",
            "risk_level": "High",
            "warnings": [malformed_msg],
            "strong_signals": [malformed_msg],
            "weak_signals": [],
            "has_high_risk": True,
            "is_trusted_domain": False,
            "matched_trusted_domain": None,
            "is_deceptive_subdomain": False,
            "is_ip": False,
            "is_shortener": False,
            "notice": "Structural analysis inspects URL format only and does not verify server reputation, destination safety, or live content."
        }

    try:
        raw_hostname = (parsed.hostname or "").strip().rstrip('.').lower()
        port = parsed.port
    except Exception:
        malformed_msg = "Malformed URL syntax or invalid port specification."
        return {
            "url": url_str,
            "hostname": "Unknown",
            "registered_domain": "",
            "subdomain": "",
            "tld": "",
            "risk_level": "High",
            "warnings": [malformed_msg],
            "strong_signals": [malformed_msg],
            "weak_signals": [],
            "has_high_risk": True,
            "is_trusted_domain": False,
            "matched_trusted_domain": None,
            "is_deceptive_subdomain": False,
            "is_ip": False,
            "is_shortener": False,
            "notice": "Structural analysis inspects URL format only and does not verify server reputation, destination safety, or live content."
        }
    path = (parsed.path or "").lower()

    if not raw_hostname:
        no_host_msg = "Could not extract a valid host name from URL string."
        return {
            "url": url_str,
            "hostname": "None",
            "registered_domain": "",
            "subdomain": "",
            "tld": "",
            "risk_level": "Medium",
            "warnings": [no_host_msg],
            "strong_signals": [],
            "weak_signals": [no_host_msg],
            "has_high_risk": False,
            "is_trusted_domain": False,
            "matched_trusted_domain": None,
            "is_deceptive_subdomain": False,
            "is_ip": False,
            "is_shortener": False,
            "notice": "Structural analysis inspects URL format only and does not verify server reputation, destination safety, or live content."
        }

    # Decompose domain structure
    comp = parse_domain_components(raw_hostname)
    registered_domain = comp["registered_domain"]
    subdomain = comp["subdomain"]
    tld = comp["tld"]
    is_ip = comp["is_ip"]

    # 1. IP address hostname check (IPv4 or IPv6) -> STRONG SIGNAL
    if is_ip:
        ip_msg = "URL uses a raw IP address instead of a registered domain name."
        strong_signals.append(ip_msg)
        warnings.append(ip_msg)

    # 2. Punycode / IDN homograph check -> STRONG SIGNAL
    if "xn--" in raw_hostname:
        puny_msg = "Hostname contains Punycode ('xn--'), frequently associated with homograph domain impersonation."
        strong_signals.append(puny_msg)
        warnings.append(puny_msg)

    # 3. '@' symbol in authority/path -> STRONG SIGNAL
    if '@' in parsed.netloc or '@' in url_str.split('?')[0]:
        at_msg = "URL contains '@' symbol, which can mislead users about the true destination host."
        strong_signals.append(at_msg)
        warnings.append(at_msg)

    # 4. Known URL shortener -> STRONG SIGNAL
    if raw_hostname in KNOWN_SHORTENERS or registered_domain in KNOWN_SHORTENERS:
        is_shortener = True
        short_msg = f"Hostname is a known URL shortening service ({raw_hostname}) that masks destination structure."
        strong_signals.append(short_msg)
        warnings.append(short_msg)

    # 5. Exact matching against Configurable Trusted Domain Allowlist
    # Only exact registered domain matches qualify; never trust a URL simply because
    # a brand appears in a subdomain or path.
    if registered_domain in trusted_domains:
        is_trusted_domain = True
        matched_trusted_domain = registered_domain

    # 6. Deceptive Subdomain and Lookalike Brand Impersonation -> STRONG SIGNAL
    # If a high-value brand or trusted domain appears in the subdomain while the
    # registered domain belongs to an unrelated party, flag as deceptive structure.
    all_check_brands = HIGH_VALUE_TARGETS.union({d.split('.')[0] for d in trusted_domains})
    for brand in all_check_brands:
        legit_root = LEGITIMATE_TARGET_DOMAINS.get(brand, f"{brand}.com")
        # Check if brand appears in subdomain or hostname labels prior to registered domain
        if subdomain and (brand in subdomain.split('.') or brand in subdomain):
            if registered_domain != legit_root and registered_domain not in trusted_domains:
                is_deceptive_subdomain = True
                deceptive_msg = (
                    f"Deceptive subdomain structure: references recognized brand or entity '{brand}' "
                    f"in subdomain prefix, but registered domain is '{registered_domain}'."
                )
                strong_signals.append(deceptive_msg)
                warnings.append(deceptive_msg)
                break
        elif brand in raw_hostname and not is_trusted_domain:
            if registered_domain != legit_root:
                is_deceptive_subdomain = True
                spoof_msg = f"Hostname references recognized brand '{brand}' but domain does not belong to '{legit_root}'."
                strong_signals.append(spoof_msg)
                warnings.append(spoof_msg)
                break

    # 7. Brand in URL path -> WEAK SIGNAL
    for brand, legit_root in LEGITIMATE_TARGET_DOMAINS.items():
        if brand in path and not (registered_domain == legit_root or is_trusted_domain):
            path_msg = f"URL path references recognized brand '{brand}' under an unrelated domain ({raw_hostname})."
            weak_signals.append(path_msg)
            warnings.append(path_msg)
            break

    # 8. High-risk TLD check (e.g. .xyz, .biz) -> WEAK SIGNAL ONLY
    # Per requirements, TLD categories are strictly weak signals and never trigger phishing alone.
    if tld in WEAK_SIGNAL_TLDS:
        tld_msg = f"Domain uses high-risk top-level domain (.{tld}) commonly seen in disposable phishing infrastructure."
        weak_signals.append(tld_msg)
        warnings.append(tld_msg)

    # 9. Excessive subdomains check
    subdomain_parts = [p for p in subdomain.split('.') if p]
    if len(subdomain_parts) >= 3 or len(raw_hostname.split('.')) > 4:
        depth_msg = f"Excessive subdomain depth ({len(raw_hostname.split('.')) - 2} levels) detected, often used to disguise host identity."
        weak_signals.append(depth_msg)
        warnings.append(depth_msg)

    # 10. Excessive hyphens in domain -> WEAK SIGNAL
    if raw_hostname.count('-') >= 2:
        hyphen_msg = f"Hostname contains multiple hyphens ({raw_hostname.count('-')}), typical of typo-squatting or deceptive names."
        weak_signals.append(hyphen_msg)
        warnings.append(hyphen_msg)

    # 11. Non-standard port -> WEAK SIGNAL
    if port and port not in (80, 443):
        port_msg = f"URL specifies a non-standard network port (:{port})."
        weak_signals.append(port_msg)
        warnings.append(port_msg)

    # 12. Abnormal URL length -> WEAK SIGNAL
    if len(url_str) > 85:
        len_msg = f"Abnormally long URL ({len(url_str)} characters), which may obfuscate parameters or payload strings."
        weak_signals.append(len_msg)
        warnings.append(len_msg)

    # Determine overall structural risk level
    has_high_risk = len(strong_signals) > 0
    if has_high_risk:
        risk_level = "High"
    elif len(weak_signals) >= 1:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "url": url_str,
        "hostname": raw_hostname,
        "registered_domain": registered_domain,
        "subdomain": subdomain,
        "tld": tld,
        "risk_level": risk_level,
        "warnings": warnings,
        "strong_signals": strong_signals,
        "weak_signals": weak_signals,
        "has_high_risk": has_high_risk,
        "is_trusted_domain": is_trusted_domain,
        "matched_trusted_domain": matched_trusted_domain,
        "is_deceptive_subdomain": is_deceptive_subdomain,
        "is_ip": is_ip,
        "is_shortener": is_shortener,
        "notice": "Structural analysis inspects URL format only and does not verify server reputation, destination safety, or live content."
    }


def analyze_all_urls(text: str, trusted_domains: set[str] = None) -> tuple[list[str], list[dict], bool]:
    """
    Extracts and evaluates all URLs found in the text.
    Returns:
        (extracted_urls, analysis_list, has_structural_warnings)
    """
    urls = extract_urls(text)
    analysis_list = [analyze_url_structure(u, trusted_domains=trusted_domains) for u in urls]

    # Any URL with warnings or risk triggers structural caution indicator
    has_warnings = any(item["risk_level"] in ("High", "Medium") or len(item["warnings"]) > 0 for item in analysis_list)

    return urls, analysis_list, has_warnings

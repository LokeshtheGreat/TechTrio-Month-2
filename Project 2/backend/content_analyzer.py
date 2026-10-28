"""
Message Content Analyzer and Model Explanation Module for PhishShift.

Provides:
1. Rule-based detection of suspicious message patterns (urgent language, threats, sensitive info requests, prizes).
2. Model-derived word influence attribution using the trained TF-IDF vectorizer and LinearSVC coefficients.
"""

import re
import numpy as np


# Defined rule-based pattern categories for content analysis
CONTENT_RULES = [
    {
        "category": "Urgent or Pressuring Language",
        "description": "Urges immediate action before an artificial or sudden deadline.",
        "pattern": re.compile(
            r"\b(urgent(?:ly)?|immediate(?:ly)?|act now|immediate action|right away|asap|time sensitive|"
            r"expires? (?:today|soon|in \d+ \w+)|final notice|last chance|within \d+ (?:hours?|minutes?|mins?|days?)|"
            r"account will be (?:closed|suspended|deactivated))\b",
            re.IGNORECASE,
        ),
    },
    {
        "category": "Account or Security Alerts",
        "description": "Warns of account suspension, access restrictions, or security locks.",
        "pattern": re.compile(
            r"\b(account (?:has been |is )?(?:suspended|blocked|locked|disabled|restricted|deactivated|closed)|"
            r"unauthorized (?:activity|access|transaction|login)|security (?:alert|breach|warning)|"
            r"suspicious (?:activity|login|sign[\s-]in)|access (?:limited|denied|revoked)|unusual sign[\s-]in)\b",
            re.IGNORECASE,
        ),
    },
    {
        "category": "Sensitive Information Request",
        "description": "Prompts for passwords, security credentials, PINs, OTPs, or financial details.",
        "pattern": re.compile(
            r"\b(verify (?:your |the )?(?:identity|account|card|credentials?|password|pin)|"
            r"(?:enter|update|confirm|provide) (?:your )?(?:password|passcode|pin|credentials?|otp|"
            r"one[\s-]time (?:pin|password|code|passcode)|bank details?|card details?|credit card|cvv|security code))\b",
            re.IGNORECASE,
        ),
    },
    {
        "category": "Unexpected Prize or Offer",
        "description": "Offers unexpected prizes, rewards, lottery winnings, or pending refunds.",
        "pattern": re.compile(
            r"\b(congratulations|you(?: have|\'ve)? won|claim (?:your |free )?(?:prize|reward|gift card|bonus|cash|refund)|"
            r"lottery winner|exclusive reward|free gift|refund (?:pending|available|issued)|"
            r"selected (?:as a |to receive)|winner of)\b",
            re.IGNORECASE,
        ),
    },
    {
        "category": "Action Prompt Directive",
        "description": "Instructs clicking an external link, opening an attachment, or downloading a file.",
        "pattern": re.compile(
            r"\b(click (?:here|the link|below)|follow (?:this|the) link|tap (?:here|the link)|"
            r"open (?:the |this )?(?:attachment|file)|download (?:the |this )?(?:attachment|file|document))\b",
            re.IGNORECASE,
        ),
    },
]


def analyze_message_content(message: str) -> dict:
    """
    Examines message text for suspicious phrasing patterns using clear, testable rules.

    Does not alter model verdicts. Reports only findings actually present in the text.
    If no patterns are found, returns a neutral summary ("No obvious suspicious wording was detected.").
    """
    if not message or not isinstance(message, str):
        return {
            "findings": [],
            "has_findings": False,
            "summary": "No obvious suspicious wording was detected."
        }

    findings = []
    seen_categories = set()

    for rule in CONTENT_RULES:
        category = rule["category"]
        if category in seen_categories:
            continue

        match = rule["pattern"].search(message)
        if match:
            excerpt = match.group(0).strip()
            # Truncate very long excerpts neatly
            if len(excerpt) > 60:
                excerpt = excerpt[:57] + "..."

            findings.append({
                "category": category,
                "description": rule["description"],
                "excerpt": excerpt
            })
            seen_categories.add(category)

    if findings:
        count = len(findings)
        summary = f"{count} suspicious wording pattern{'s' if count > 1 else ''} detected in the message text."
        has_findings = True
    else:
        summary = "No obvious suspicious wording was detected."
        has_findings = False

    return {
        "findings": findings,
        "has_findings": has_findings,
        "summary": summary
    }


def explain_model_words(message: str, vectorizer, model, final_prediction: str, max_terms: int = 4) -> dict:
    """
    Identifies words or short phrases from the submitted message that influenced the model's prediction.

    Derives influence directly from the trained LinearSVC coefficients and the sample's TF-IDF features.
    Positive feature contributions push toward phishing; negative feature contributions lean legitimate.
    """
    if not message or vectorizer is None or model is None:
        return {
            "suspicious_words": [],
            "legitimate_words": [],
            "has_influences": False,
            "suspicious_note": "",
            "legitimate_note": "",
            "summary": "No specific words in the message strongly influenced the assessment."
        }

    try:
        X = vectorizer.transform([message])
        nonzero = X.nonzero()[1]

        if len(nonzero) == 0:
            return {
                "suspicious_words": [],
                "legitimate_words": [],
                "has_influences": False,
                "suspicious_note": "",
                "legitimate_note": "",
                "summary": "No specific words in the message strongly influenced the assessment."
            }

        feature_names = vectorizer.get_feature_names_out()
        coef = model.coef_[0]

        suspicious_candidates = []
        legitimate_candidates = []

        for idx in nonzero:
            tfidf_val = X[0, idx]
            weight = coef[idx]
            contribution = float(tfidf_val * weight)
            term = feature_names[idx]

            # Filter out single-character punctuation/noise
            if len(term.strip()) < 2:
                continue

            # Significant contribution threshold
            if contribution >= 0.015:
                suspicious_candidates.append((term, contribution))
            elif contribution <= -0.015:
                legitimate_candidates.append((term, contribution))

        # Sort suspicious descending (highest positive impact first)
        suspicious_candidates.sort(key=lambda item: item[1], reverse=True)
        # Sort legitimate ascending (most negative / legitimate-leaning first)
        legitimate_candidates.sort(key=lambda item: item[1])

        # Deduplicate overlapping unigrams and bigrams for cleaner user presentation
        def deduplicate_terms(terms_with_scores, limit):
            chosen = []
            chosen_words = set()
            for term, score in terms_with_scores:
                words = set(term.split())
                # If term is already completely contained in an already chosen bigram, or vice versa, skip if we already have representatives
                if any(words.issubset(c.split()) or set(c.split()).issubset(words) for c in chosen):
                    # Prefer shorter or first encountered unless list is small
                    if len(chosen) >= limit:
                        continue
                chosen.append(term)
                if len(chosen) >= limit:
                    break
            return chosen

        suspicious_words = deduplicate_terms(suspicious_candidates, max_terms)
        legitimate_words = deduplicate_terms(legitimate_candidates, max_terms)

        has_influences = bool(suspicious_words or legitimate_words)

        # Context-aware plain-English summaries
        if not has_influences:
            summary = "No specific words in the message strongly influenced the assessment."
            suspicious_note = ""
            legitimate_note = ""
        else:
            suspicious_note = "These words pushed the assessment toward a suspicious result." if suspicious_words else ""
            legitimate_note = "These words were more consistent with ordinary messages." if legitimate_words else ""

            if final_prediction == "Phishing":
                summary = "The model identified words that are frequently found in suspicious communications."
            elif final_prediction == "Legitimate":
                summary = "The model identified words that are consistent with standard everyday communications."
            else:
                summary = "The model noted a mix of wording patterns, resulting in a borderline assessment."

        return {
            "suspicious_words": suspicious_words,
            "legitimate_words": legitimate_words,
            "has_influences": has_influences,
            "suspicious_note": suspicious_note,
            "legitimate_note": legitimate_note,
            "summary": summary
        }

    except Exception:
        return {
            "suspicious_words": [],
            "legitimate_words": [],
            "has_influences": False,
            "suspicious_note": "",
            "legitimate_note": "",
            "summary": "No specific words in the message strongly influenced the assessment."
        }

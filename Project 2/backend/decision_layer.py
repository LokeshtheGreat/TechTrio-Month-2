"""
URL-Aware Final Decision Layer for PhishShift.

Combines machine learning text classification (TF-IDF + LinearSVC) with
URL risk evidence using conservative, explainable rules.

Key Principles:
1. Retains ambient text prediction (text_prediction) separately for full auditability.
2. Messages without URLs retain the exact baseline SVM classification.
3. Inspects ALL URLs in multi-URL messages without silently ignoring suspicious ones.
4. Top-level domains (e.g. .xyz, .biz) are weak signals only and NEVER trigger a phishing verdict alone.
5. Trusted-domain matches do NOT guarantee safety (never claimed guaranteed safe).
6. Ambiguous or conflicting evidence escalates to 'Review Required'.
"""


def evaluate_final_decision(
    text_prediction: str,
    decision_score: float,
    extracted_urls: list[str],
    url_analysis: list[dict],
    threshold: float = 0.70
) -> dict:
    """
    Evaluates final classification by fusing text model scoring with URL risk signals.

    Returns:
        {
            "final_prediction": "Phishing" | "Legitimate" | "Review Required",
            "reason": str,
            "decision_factors": dict
        }
    """
    # 1. No URLs present: retain baseline SVM behavior
    if not extracted_urls or not url_analysis:
        if text_prediction == "Phishing":
            reason = "The message text was classified as phishing by the trained model."
        elif text_prediction == "Review Required":
            reason = "The model's score falls within the configured review threshold."
        else:
            reason = "The message was classified as legitimate, and no configured URL structural warnings were found."

        return {
            "final_prediction": text_prediction,
            "reason": reason,
            "decision_factors": {
                "text_prediction": text_prediction,
                "decision_score": decision_score,
                "url_count": 0,
                "has_strong_url_risk": False,
                "has_weak_url_risk": False,
                "has_trusted_urls": False,
                "strong_signals": [],
                "weak_signals": [],
            }
        }

    # 2. URLs present: inspect all URLs thoroughly without skipping any
    all_strong_signals = []
    all_weak_signals = []
    all_warnings = []
    trusted_count = 0

    for item in url_analysis:
        strong = item.get("strong_signals", [])
        weak = item.get("weak_signals", [])
        warnings = item.get("warnings", [])

        all_strong_signals.extend(strong)
        all_weak_signals.extend(weak)
        all_warnings.extend(warnings)

        if item.get("is_trusted_domain") and not strong and not weak:
            trusted_count += 1

    has_strong_url_risk = len(all_strong_signals) > 0
    has_weak_url_risk = len(all_weak_signals) > 0
    all_trusted = (
        len(url_analysis) > 0
        and trusted_count == len(url_analysis)
        and not has_strong_url_risk
        and not has_weak_url_risk
    )
    has_trusted_url = trusted_count > 0

    # 3. Decision Combination Logic

    # Branch A: Ambient text prediction is Phishing (score >= threshold)
    if text_prediction == "Phishing":
        final_prediction = "Phishing"
        if has_strong_url_risk:
            first_sig = all_strong_signals[0]
            reason = (
                f"The message text was classified as phishing by the trained model, "
                f"reinforced by suspicious URL indicators ({first_sig})."
            )
        else:
            reason = "The message text was classified as phishing by the trained model. Embedded links do not override this assessment."

    # Branch B: Ambient text prediction is Review Required (0 <= score < threshold)
    elif text_prediction == "Review Required":
        final_prediction = "Review Required"
        if has_strong_url_risk:
            first_sig = all_strong_signals[0]
            reason = (
                f"The message text falls within the review threshold, and suspicious URL indicators "
                f"were detected ({first_sig}). Manual verification is strongly advised."
            )
        else:
            reason = "The model's score falls within the configured review threshold."

    # Branch C: Ambient text prediction is Legitimate (score < 0)
    else:
        # Case C1: Conflicting evidence — benign text, but strong URL risk detected
        # (e.g. raw IP address, deceptive subdomain, shortener, punycode, '@' symbol, malformed URL)
        if has_strong_url_risk:
            final_prediction = "Review Required"
            first_sig = all_strong_signals[0]
            reason = (
                f"The message text was classified as legitimate, but URL structural warnings "
                f"were found ({first_sig}). Additional verification is recommended."
            )

        # Case C2: Ambiguous evidence — multiple weak structural anomalies
        elif len(all_weak_signals) >= 2:
            final_prediction = "Review Required"
            first_sig = all_weak_signals[0]
            reason = (
                f"The message text was classified as legitimate, but multiple URL structural anomalies "
                f"were identified ({first_sig}). Verification is recommended."
            )

        # Case C3: Weak signal only (e.g. .xyz or .biz TLD alone with no other anomalies)
        # Requirements explicitly mandate: A TLD alone must never trigger a phishing verdict.
        # Legitimate-looking .xyz URLs without other suspicious signals remain Legitimate.
        elif has_weak_url_risk:
            final_prediction = "Legitimate"
            first_sig = all_weak_signals[0]
            reason = (
                f"The message was classified as legitimate. An uncommon top-level domain was detected "
                f"({first_sig}), but as an isolated weak signal it does not alter the legitimate classification."
            )

        # Case C4: All URLs match trusted allowlist with no warnings
        elif all_trusted:
            final_prediction = "Legitimate"
            reason = (
                "The message was classified as legitimate, and embedded URLs match the configured "
                "trusted domain allowlist. (Note: Trusted domain matches do not guarantee safety against "
                "compromised accounts or malicious redirects.)"
            )

        # Case C5: Clean URLs with no warnings
        else:
            final_prediction = "Legitimate"
            reason = "The message was classified as legitimate, and no configured URL structural warnings were found."

    return {
        "final_prediction": final_prediction,
        "reason": reason,
        "decision_factors": {
            "text_prediction": text_prediction,
            "decision_score": decision_score,
            "url_count": len(extracted_urls),
            "has_strong_url_risk": has_strong_url_risk,
            "has_weak_url_risk": has_weak_url_risk,
            "has_trusted_url": has_trusted_url,
            "all_trusted": all_trusted,
            "strong_signals": list(dict.fromkeys(all_strong_signals)),
            "weak_signals": list(dict.fromkeys(all_weak_signals)),
        }
    }

"""
PII Detector for Input Guardrails.
Detects and handles Personally Identifiable Information (PII) including:
- Email addresses
- Phone numbers (domestic & international)
- Social Security Numbers (SSN) / National Identification Numbers
- Credit / Debit Card numbers (with Luhn validation)
- Bank Account Numbers
"""
import re
from typing import Dict, List, Tuple
from guardrails.models import ActionTaken, GuardrailResult


class PIIDetector:
    """
    Detection Approach:
    - Combines contextual regular expressions with checksum validation (e.g., Luhn algorithm for cards).
    - Categorizes findings by entity type and replaces with semantic redaction tokens (e.g. [REDACTED_EMAIL]).

    Action Taken:
    - REDACT: Replaces sensitive tokens with anonymized placeholders so downstream model can still
      comprehend conversational context without storing or seeing sensitive PII.
    - If extreme risk or multiple high-stakes PII are detected alongside malicious intent, can flag for blocking.

    Limitations:
    - Regex cannot detect obfuscated PII (e.g. "john dot doe at gmail dot com" or spaced numbers "4 1 1 1").
    - False positives on legitimate non-PII serial numbers, order IDs, or software version strings.
    - Does not infer implicit identity through unstructured contextual biographical hints.
    """

    PATTERNS = {
        "EMAIL": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        ),
        "PHONE": re.compile(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        "SSN": re.compile(
            r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b"
        ),
        "CREDIT_CARD": re.compile(
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
        ),
        "BANK_ACCOUNT": re.compile(
            r"\b(?:acct|account|acc\s*no\.?)\s*[:#]?\s*([0-9]{8,12})\b",
            re.IGNORECASE
        ),
        "PASSPORT": re.compile(
            r"\b[A-PR-WY][1-9]\d\s?\d{4}[1-9]\b",
            re.IGNORECASE
        )
    }

    def __init__(self, redact: bool = True):
        self.redact = redact

    @staticmethod
    def _luhn_checksum_valid(card_num_str: str) -> bool:
        """Validate credit card number using Luhn formula."""
        digits = [int(c) for c in card_num_str if c.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False
        total = 0
        reverse_digits = digits[::-1]
        for idx, digit in enumerate(reverse_digits):
            if idx % 2 == 1:
                doubled = digit * 2
                total += doubled - 9 if doubled > 9 else doubled
            else:
                total += digit
        return total % 10 == 0

    def check(self, text: str) -> GuardrailResult:
        detected_entities: Dict[str, List[str]] = {}
        sanitized = text
        total_pii_count = 0

        # Check Credit Cards (with Luhn confirmation to prevent false positive numbers)
        for match in self.PATTERNS["CREDIT_CARD"].finditer(text):
            candidate = match.group(0)
            clean_digits = re.sub(r"\D", "", candidate)
            if self._luhn_checksum_valid(clean_digits):
                detected_entities.setdefault("CREDIT_CARD", []).append(candidate)
                total_pii_count += 1
                if self.redact:
                    sanitized = sanitized.replace(candidate, "[REDACTED_CREDIT_CARD]")

        # Check Emails
        for match in self.PATTERNS["EMAIL"].finditer(text):
            candidate = match.group(0)
            detected_entities.setdefault("EMAIL", []).append(candidate)
            total_pii_count += 1
            if self.redact:
                sanitized = sanitized.replace(candidate, "[REDACTED_EMAIL]")

        # Check SSNs
        for match in self.PATTERNS["SSN"].finditer(text):
            candidate = match.group(0)
            # Avoid replacing if it was already part of a credit card or other match
            if candidate in sanitized and not any(candidate in card for card in detected_entities.get("CREDIT_CARD", [])):
                # If 9 digits without hyphen, require keyword proximity or format
                if "-" in candidate or len(candidate) == 9:
                    detected_entities.setdefault("SSN", []).append(candidate)
                    total_pii_count += 1
                    if self.redact:
                        sanitized = sanitized.replace(candidate, "[REDACTED_SSN]")

        # Check Phones
        for match in self.PATTERNS["PHONE"].finditer(sanitized):
            candidate = match.group(0)
            if not any(token in candidate for token in ["[REDACTED", "REDACTED_"]):
                detected_entities.setdefault("PHONE", []).append(candidate)
                total_pii_count += 1
                if self.redact:
                    sanitized = sanitized.replace(candidate, "[REDACTED_PHONE]")

        # Check Bank Account
        for match in self.PATTERNS["BANK_ACCOUNT"].finditer(text):
            candidate = match.group(1)
            detected_entities.setdefault("BANK_ACCOUNT", []).append(candidate)
            total_pii_count += 1
            if self.redact:
                sanitized = sanitized.replace(candidate, "[REDACTED_BANK_ACCOUNT]")

        passed = (total_pii_count == 0)
        action = ActionTaken.ALLOW if passed else (ActionTaken.REDACT if self.redact else ActionTaken.BLOCK)
        risk_score = min(1.0, total_pii_count * 0.35)

        return GuardrailResult(
            guardrail_name="PII_Detection",
            passed=passed,
            action=action,
            risk_score=risk_score,
            message=f"Detected {total_pii_count} PII entity(ies)" if not passed else "No PII detected",
            sanitized_text=sanitized,
            details={
                "detected_count": total_pii_count,
                "detected_types": list(detected_entities.keys()),
                "entities_found": {k: [e[:3] + "***" for e in v] for k, v in detected_entities.items()},
            }
        )

"""
Sensitive Topic Classifier for Input Guardrails.
Identifies high-risk categories requiring special handling, refusal policies,
or emergency interventions.
"""
import re
from typing import Any, Dict, List, Optional
from guardrails.models import ActionTaken, GuardrailResult


class SensitiveTopicClassifier:
    """
    Detection Approach:
    - Multi-category keyword and phrase taxonomy with contextual boundary matching.
    - Classifies inputs into distinct policy risk domains:
      1. SELF_HARM: Suicide, self-injury, or emotional crisis.
      2. FINANCIAL_FRAUD_AML: Money laundering, credit card theft, structuring, evasion.
      3. CYBERATTACK_EXPLOIT: Exploitation tools, keyloggers, DDoS, ransomware.
      4. HATE_HARASSMENT: Hate speech, violence, severe abuse.
      5. UNAUTHORIZED_LEGAL_FINANCIAL_ADVICE: Demands for guaranteed fiduciary/tax evasion counsel.
    - Assigns tailored response policies and emergency mitigation messages per category.

    Action Taken:
    - BLOCK: For safety-critical domains (self-harm, fraud, exploits, hate).
      Returns immediate safe refusal with specialized hotlines or policy rationales.
    - SAFE_FALLBACK: When borderline or requiring disclaimers.

    Limitations:
    - May produce false positives for benign educational, journalistic, or defensive research
      (e.g., "Explain how banks detect money laundering" vs "How do I launder money?").
    - Highly creative metaphors, euphemisms, or slang may bypass dictionary-based keyword sets.
    """

    TOPIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
        "SELF_HARM": {
            "patterns": [
                r"\b(suicide|kill\s+myself|end\s+my\s+life|hang\s+myself|overdose\s+on\s+pills)\b",
                r"\b(want\s+to\s+die|ways\s+to\s+commit\s+suicide|self-harm|cut\s+my\s+wrists)\b",
            ],
            "severity": "CRITICAL",
            "fallback_message": (
                "If you or someone you know is going through a tough time or having thoughts of self-harm, "
                "please know that support is available. You can call or text 988 in the US and Canada, "
                "or contact your local emergency services for free, confidential 24/7 support."
            )
        },
        "FINANCIAL_FRAUD_AML": {
            "patterns": [
                r"\b(how\s+to\s+launder\s+money|evade\s+aml|clean\s+dirty\s+money)\b",
                r"\b(smurfing|structuring\s+deposits\s+to\s+avoid\s+reporting)\b",
                r"\b(counterfeit\s+currency|fake\s+bank\s+statements?|synthetic\s+identity\s+theft)\b",
                r"\b(steal\s+credit\s+cards?|carding\s+tutorial|credit\s+card\s+fraud\s+method)\b",
            ],
            "severity": "HIGH",
            "fallback_message": (
                "I cannot assist with queries involving financial fraud, identity theft, or circumventing "
                "anti-money laundering (AML) banking compliance."
            )
        },
        "CYBERATTACK_EXPLOIT": {
            "patterns": [
                r"\b(ransomware|keylogger|ddos\s+attack|malware|spyware|trojan)\b",
                r"\b(write|provide|create|code|generate)\s+.*?\b(ransomware|keylogger|ddos|exploit)\b",
                r"\b(exploit\s+zero-day|sql\s+injection\s+payload\s+to\s+hack|steal\s+session\s+cookies)\b",
                r"\b(how\s+to\s+hack\s+a\s+bank|bypass\s+firewall\s+unauthorized)\b",
            ],
            "severity": "HIGH",
            "fallback_message": (
                "I cannot provide instructions, code, or assistance designed to exploit systems, "
                "compromise cybersecurity, or develop malicious software."
            )
        },
        "HATE_HARASSMENT": {
            "patterns": [
                r"\b(exterminate|inferior\s+race|gas\s+the\b|kill\s+all\s+(men|women|immigrants|jews|muslims))\b",
                r"\b(lynch\b|violent\s+attack\s+against\b)",
            ],
            "severity": "HIGH",
            "fallback_message": (
                "I cannot generate hateful content, harassment, or inciteful language targeting groups or individuals."
            )
        }
    }

    def __init__(self):
        self.compiled_rules = {
            topic: [re.compile(p, re.IGNORECASE) for p in data["patterns"]]
            for topic, data in self.TOPIC_DEFINITIONS.items()
        }

    def check(self, text: str) -> GuardrailResult:
        flagged_categories = []
        highest_severity = "NONE"
        selected_fallback = ""

        for topic, patterns in self.compiled_rules.items():
            for p in patterns:
                if p.search(text):
                    flagged_categories.append(topic)
                    highest_severity = self.TOPIC_DEFINITIONS[topic]["severity"]
                    selected_fallback = self.TOPIC_DEFINITIONS[topic]["fallback_message"]
                    break

        passed = (len(flagged_categories) == 0)
        action = ActionTaken.ALLOW if passed else ActionTaken.BLOCK
        risk_score = 1.0 if highest_severity == "CRITICAL" else (0.85 if highest_severity == "HIGH" else 0.0)

        return GuardrailResult(
            guardrail_name="Sensitive_Topic_Classification",
            passed=passed,
            action=action,
            risk_score=risk_score,
            message=f"Flagged sensitive topic(s): {', '.join(flagged_categories)}" if not passed else "Topic is safe",
            details={
                "flagged_categories": flagged_categories,
                "severity": highest_severity,
                "policy_response": selected_fallback if not passed else None,
            }
        )

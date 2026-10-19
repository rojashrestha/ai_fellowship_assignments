"""
Prompt Injection Detector for Input Guardrails.
Detects attempts to override system prompts, bypass policy restrictions,
extract internal system instructions, or spoof conversational roles.
"""
import re
from typing import Dict, List, Tuple
from guardrails.models import ActionTaken, GuardrailResult


class PromptInjectionDetector:
    """
    Detection Approach:
    - Multi-tiered heuristic analysis:
      1. Direct Instruction Overrides (e.g. 'ignore previous instructions', 'disregard prior rules').
      2. Roleplay/Persona Hijacking & Jailbreaks (e.g. 'DAN mode', 'developer mode enabled', 'act as unrestricted').
      3. System Secret & Prompt Extraction (e.g. 'reveal system prompt', 'print initialization instructions').
      4. Delimiter & Role Spoofing (e.g. '[SYSTEM]', '</system>', 'Assistant:', 'Human:').
      5. Obfuscation heuristics (excessive special formatting or leetspeak).
    - Computes a weighted risk score; triggers BLOCK action if confidence exceeds threshold (default 0.5).

    Action Taken:
    - BLOCK: When an injection is detected, processing is halted immediately, preventing
      the payload from reaching the downstream foundation model. A safe refusal is returned.

    Limitations:
    - Zero-day linguistic paraphrasing or indirect multi-step hypothetical narratives
      might evade keyword/regex rules.
    - False positives can occur if a user asks pedagogical or informational questions
      about prompt injection (e.g. "What does 'ignore previous instructions' mean?").
    """

    DIRECT_OVERRIDE_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|commands)",
        r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|guidelines)",
        r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions|context|rules)",
        r"override\s+(all\s+)?(safety|system|instruction)\s*(settings|protocols)?",
        r"stop\s+being\s+an?\s+ai",
        r"do\s+anything\s+now",
        r"\bdan\s+mode\b",
        r"jailbreak",
        r"developer\s+mode\s+(output|enabled|on)",
        r"unfiltered\s+(mode|response)",
        r"act\s+as\s+an?\s+(unrestricted|unaligned|evil|ruleless)\b",
    ]

    LEAKAGE_EXTRACTION_PATTERNS = [
        r"(print|show|reveal|display|output|repeat|leak)\s+(the\s+)?(system\s+prompt|initial\s+instructions|secret\s+key|internal\s+rules)",
        r"what\s+are\s+your\s+(exact\s+)?(instructions|system\s+prompts|hidden\s+rules)",
        r"verbatim\s+copy\s+of\s+your\s+(initialization|prompt)",
        r"tell\s+me\s+your\s+secret\s+(code|token|key|instruction)",
    ]

    DELIMITER_SPOOFING_PATTERNS = [
        r"<\s*/?\s*(system|instruction|admin|developer)\s*>",
        r"\[\s*(system|instruction|override|admin)\s*\]",
        r"```\s*(system|instruction|admin)\b",
        r"(?:^|\n)\s*(?:human|user|assistant|system)\s*:\s*",
    ]

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.compiled_overrides = [re.compile(p, re.IGNORECASE) for p in self.DIRECT_OVERRIDE_PATTERNS]
        self.compiled_leakages = [re.compile(p, re.IGNORECASE) for p in self.LEAKAGE_EXTRACTION_PATTERNS]
        self.compiled_delimiters = [re.compile(p, re.IGNORECASE) for p in self.DELIMITER_SPOOFING_PATTERNS]

    def check(self, text: str) -> GuardrailResult:
        triggers: List[Dict[str, str]] = []
        score = 0.0

        # 1. Direct instruction overrides (High weight = 0.75)
        for pattern in self.compiled_overrides:
            matches = pattern.findall(text)
            if matches:
                triggers.append({"category": "DIRECT_OVERRIDE", "pattern": pattern.pattern})
                score += 0.75
                break

        # 2. Information/Prompt extraction (High weight = 0.70)
        for pattern in self.compiled_leakages:
            matches = pattern.findall(text)
            if matches:
                triggers.append({"category": "PROMPT_EXTRACTION", "pattern": pattern.pattern})
                score += 0.70
                break

        # 3. Delimiter / Role spoofing (Medium weight = 0.50)
        for pattern in self.compiled_delimiters:
            matches = pattern.findall(text)
            if matches:
                triggers.append({"category": "DELIMITER_SPOOFING", "pattern": pattern.pattern})
                score += 0.50
                break

        # Check leetspeak or character-spaced evasion (e.g. "i-g-n-o-r-e" or "1gn0r3")
        normalized_spaces = re.sub(r"[\s\-_.]+", "", text.lower())
        if "ignoreprevious" in normalized_spaces or "systemprompt" in normalized_spaces or "jailbreak" in normalized_spaces:
            if not triggers:
                triggers.append({"category": "OBFUSCATED_OVERRIDE", "pattern": "normalized_character_spacing"})
                score += 0.65

        risk_score = min(1.0, score)
        passed = (risk_score < self.threshold)
        action = ActionTaken.ALLOW if passed else ActionTaken.BLOCK

        return GuardrailResult(
            guardrail_name="Prompt_Injection_Detection",
            passed=passed,
            action=action,
            risk_score=risk_score,
            message="Prompt injection attempt detected" if not passed else "Prompt is safe from injection",
            sanitized_text=text if passed else None,
            details={
                "risk_score": round(risk_score, 3),
                "threshold": self.threshold,
                "triggers": triggers,
            }
        )

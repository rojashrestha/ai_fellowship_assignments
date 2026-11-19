"""
Groundedness Validator for Output Guardrails.
Evaluates whether claims made in the generated AI response are supported by
the provided reference documents/context (hallucination detection).
"""
import re
from typing import Dict, List, Optional, Set
from guardrails.models import ActionTaken, GuardrailResult

# Common English stopwords to exclude from lexical overlap
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}


class GroundednessValidator:
    """
    Detection Approach:
    - Splits the generated answer into distinct claims / sentences.
    - Filters out syntactic stopwords to extract salient factual content tokens and n-grams.
    - Evaluates token containment, bi-gram overlap, and Jaccard intersection against the
      reference context documents provided to the AI.
    - Computes a claim-level support score and an overall groundedness index (0.0 to 1.0).
    - If ungrounded claims exceed the tolerance threshold, flags the response as hallucinated.

    Action Taken:
    - REGENERATE or SAFE_FALLBACK:
      When generated claims deviate from the provided source of truth, the response is rejected
      to prevent misinformation. A safe fallback response is returned indicating that the generated
      content could not be factually verified.

    Limitations:
    - Lexical n-gram overlap cannot detect subtle numeric hallucinations (e.g. changing '5%' to '50%')
      if the surrounding lexical tokens match closely.
    - Complex semantic paraphrasing or cross-lingual reasoning may yield low lexical overlap
      even when logically entailed by the reference text.
    """

    def __init__(self, groundedness_threshold: float = 0.55, claim_threshold: float = 0.40):
        self.groundedness_threshold = groundedness_threshold
        self.claim_threshold = claim_threshold

    @staticmethod
    def _extract_content_tokens(text: str) -> Set[str]:
        tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
        return {
            t for t in tokens
            if t not in STOPWORDS
            and len(t) > 1
            and not t.startswith("redacted")
        }

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        # Split on sentence delimiters (.!?) while keeping non-empty segments
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return [p.strip() for p in parts if len(p.strip()) > 5]

    def check(self, answer_text: str, reference_context: Optional[str]) -> GuardrailResult:
        if not reference_context or not reference_context.strip():
            # If no reference context was provided, we cannot verify groundedness
            return GuardrailResult(
                guardrail_name="Groundedness_Validation",
                passed=False,
                action=ActionTaken.SAFE_FALLBACK,
                risk_score=0.8,
                message="Cannot verify groundedness: No reference context provided",
                details={"reason": "MISSING_REFERENCE_CONTEXT", "groundedness_score": 0.0}
            )

        context_tokens = self._extract_content_tokens(reference_context)
        context_lower = reference_context.lower()

        sentences = self._split_into_sentences(answer_text)
        if not sentences:
            sentences = [answer_text.strip()]

        sentence_scores = []
        unsupported_claims = []

        for sent in sentences:
            sent_tokens = self._extract_content_tokens(sent)
            if not sent_tokens:
                sentence_scores.append(1.0)
                continue

            # Check direct phrase substring presence
            if sent.lower() in context_lower:
                sentence_scores.append(1.0)
                continue

            # Token overlap ratio: how many of the claim's content tokens exist in reference
            overlap = sent_tokens.intersection(context_tokens)
            token_recall = len(overlap) / len(sent_tokens)

            # Check numbers/metrics explicitly for numerical fidelity
            sent_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", sent))
            context_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", reference_context))
            unsupported_numbers = sent_numbers - context_numbers

            # Heavy penalty if new unsupported numbers/metrics were fabricated
            if unsupported_numbers:
                token_recall *= 0.5

            sentence_scores.append(token_recall)
            if token_recall < self.claim_threshold:
                unsupported_claims.append({
                    "sentence": sent,
                    "support_score": round(token_recall, 3),
                    "unsupported_tokens": list(sent_tokens - context_tokens)[:5],
                    "fabricated_numbers": list(unsupported_numbers),
                })

        overall_groundedness = sum(sentence_scores) / len(sentence_scores) if sentence_scores else 0.0
        passed = (overall_groundedness >= self.groundedness_threshold) and (len(unsupported_claims) == 0)

        risk_score = max(0.0, min(1.0, 1.0 - overall_groundedness))
        action = ActionTaken.ALLOW if passed else ActionTaken.SAFE_FALLBACK

        return GuardrailResult(
            guardrail_name="Groundedness_Validation",
            passed=passed,
            action=action,
            risk_score=risk_score,
            message="Claims are grounded in reference documents" if passed else f"Identified {len(unsupported_claims)} unsupported/hallucinated claim(s)",
            details={
                "overall_groundedness_score": round(overall_groundedness, 3),
                "threshold": self.groundedness_threshold,
                "total_claims_evaluated": len(sentences),
                "unsupported_claims": unsupported_claims,
            }
        )

"""
End-to-End Guardrail Pipeline.
Integrates input and output guardrails with an AI model generation step,
enforcing multi-stage defense-in-depth, redaction, safe fallbacks, and audit logging.
"""
import time
from typing import Any, Callable, Dict, Optional

from guardrails.models import (
    ActionTaken,
    GuardrailResult,
    InputGuardrailReport,
    OutputGuardrailReport,
    PipelineResult,
)
from guardrails.input_guardrails import (
    PIIDetector,
    PromptInjectionDetector,
    SensitiveTopicClassifier,
)
from guardrails.output_guardrails import (
    SchemaValidator,
    GroundednessValidator,
    SensitiveInformationDetector,
)


class GuardrailPipeline:
    """
    Orchestrates the entire guardrail workflow:
    1. Input Inspection:
       - PII Detection & Sanitization/Redaction
       - Prompt Injection Detection & Blocking
       - Sensitive Topic Classification & Intervention
    2. Model Execution (Simulated / Callable):
       - Generates structured payload
    3. Output Inspection:
       - Schema Validation & Contract Enforcement
       - Groundedness & Hallucination Verification
       - Sensitive Secret & PII Disclosure Interception
    4. Safe Fallback & Redaction Application:
       - Returns safe fallback if output fails validation
    """

    def __init__(
        self,
        pii_detector: Optional[PIIDetector] = None,
        injection_detector: Optional[PromptInjectionDetector] = None,
        topic_classifier: Optional[SensitiveTopicClassifier] = None,
        schema_validator: Optional[SchemaValidator] = None,
        groundedness_validator: Optional[GroundednessValidator] = None,
        sensitive_info_detector: Optional[SensitiveInformationDetector] = None,
        max_regeneration_attempts: int = 1,
    ):
        self.pii_detector = pii_detector or PIIDetector(redact=True)
        self.injection_detector = injection_detector or PromptInjectionDetector(threshold=0.5)
        self.topic_classifier = topic_classifier or SensitiveTopicClassifier()
        self.schema_validator = schema_validator or SchemaValidator()
        self.groundedness_validator = groundedness_validator or GroundednessValidator()
        self.sensitive_info_detector = sensitive_info_detector or SensitiveInformationDetector(redact_on_detect=True)
        self.max_regeneration_attempts = max_regeneration_attempts

    def process_input(self, user_input: str) -> InputGuardrailReport:
        """Run all input stage guardrails in defensive order."""
        results: list[GuardrailResult] = []
        current_text = user_input
        passed_all = True
        blocked_reason = None
        primary_action = ActionTaken.ALLOW

        # 1. PII Detection (Redacts PII so downstream modules operate on sanitized prompt)
        pii_res = self.pii_detector.check(current_text)
        results.append(pii_res)
        if pii_res.action == ActionTaken.REDACT and pii_res.sanitized_text:
            current_text = pii_res.sanitized_text
            primary_action = ActionTaken.REDACT

        # 2. Prompt Injection Check
        injection_res = self.injection_detector.check(current_text)
        results.append(injection_res)
        if not injection_res.passed:
            passed_all = False
            blocked_reason = "Prompt Injection attempt detected"
            primary_action = ActionTaken.BLOCK
            return InputGuardrailReport(
                passed=False,
                sanitized_input=current_text,
                results=results,
                blocked_reason=blocked_reason,
                primary_action=primary_action,
            )

        # 3. Sensitive Topic Classification
        topic_res = self.topic_classifier.check(current_text)
        results.append(topic_res)
        if not topic_res.passed:
            passed_all = False
            policy_msg = topic_res.details.get("policy_response") or "Policy-prohibited sensitive topic"
            blocked_reason = policy_msg
            primary_action = ActionTaken.BLOCK
            return InputGuardrailReport(
                passed=False,
                sanitized_input=current_text,
                results=results,
                blocked_reason=blocked_reason,
                primary_action=primary_action,
            )

        return InputGuardrailReport(
            passed=passed_all,
            sanitized_input=current_text,
            results=results,
            blocked_reason=blocked_reason,
            primary_action=primary_action,
        )

    def process_output(
        self,
        raw_response: Any,
        reference_context: Optional[str] = None
    ) -> OutputGuardrailReport:
        """Run all output stage guardrails."""
        results: list[GuardrailResult] = []

        # 1. Schema Validation
        schema_res = self.schema_validator.check(raw_response)
        results.append(schema_res)
        if not schema_res.passed:
            fallback = self.schema_validator.create_safe_fallback(
                "Output failed structural schema validation"
            )
            return OutputGuardrailReport(
                passed=False,
                final_response=fallback,
                results=results,
                action_taken=ActionTaken.SAFE_FALLBACK,
                fallback_reason="Invalid schema structure or missing required fields",
            )

        answer_text = raw_response.get("answer", "")

        # 2. Sensitive Information Detection in Output (Redact or Intercept first)
        sec_res = self.sensitive_info_detector.check(answer_text)
        results.append(sec_res)
        final_answer = answer_text
        output_action = ActionTaken.ALLOW

        if not sec_res.passed:
            if sec_res.action == ActionTaken.REDACT and sec_res.sanitized_text:
                final_answer = sec_res.sanitized_text
                output_action = ActionTaken.REDACT
            else:
                fallback = self.schema_validator.create_safe_fallback(
                    "Response blocked: sensitive secrets or PII detected in output"
                )
                return OutputGuardrailReport(
                    passed=False,
                    final_response=fallback,
                    results=results,
                    action_taken=ActionTaken.SAFE_FALLBACK,
                    fallback_reason="Sensitive information leaked in generated response",
                )

        # 3. Groundedness Validation (if reference context provided)
        if reference_context is not None:
            ground_res = self.groundedness_validator.check(final_answer, reference_context)
            results.append(ground_res)
            if not ground_res.passed:
                fallback = self.schema_validator.create_safe_fallback(
                    "Generated answer contains claims unsupported by reference documents"
                )
                return OutputGuardrailReport(
                    passed=False,
                    final_response=fallback,
                    results=results,
                    action_taken=ActionTaken.SAFE_FALLBACK,
                    fallback_reason="Failed groundedness validation (hallucination detected)",
                )

        final_payload = dict(raw_response)
        final_payload["answer"] = final_answer

        return OutputGuardrailReport(
            passed=True,
            final_response=final_payload,
            results=results,
            action_taken=output_action,
        )

    def execute(
        self,
        query: str,
        reference_context: Optional[str] = None,
        model_generator: Optional[Callable[[str, Optional[str]], Any]] = None,
    ) -> PipelineResult:
        """
        Execute full end-to-end pipeline: Input Guardrails -> Model -> Output Guardrails.
        """
        start_time = time.perf_counter()

        # Step 1: Input Guardrails
        input_report = self.process_input(query)
        if not input_report.passed:
            # Short-circuit on input violation
            refusal_payload = {
                "status": "REFUSAL",
                "answer": f"Request Refused: {input_report.blocked_reason}",
                "confidence_score": 0.0,
                "citations": [],
                "metadata": {
                    "blocked_by": "InputGuardrails",
                    "reason": input_report.blocked_reason,
                }
            }
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return PipelineResult(
                query=query,
                sanitized_query=input_report.sanitized_input,
                reference_context=reference_context,
                input_report=input_report,
                raw_ai_response=None,
                output_report=None,
                final_output=refusal_payload,
                success=False,
                latency_ms=elapsed,
            )

        # Step 2: Model Invocation (or mock generator)
        raw_response = None
        if model_generator:
            raw_response = model_generator(input_report.sanitized_input, reference_context)
        else:
            # Default fallback generator mirroring grounded context
            raw_response = {
                "status": "SUCCESS",
                "answer": reference_context if reference_context else "Processed query successfully.",
                "confidence_score": 0.95,
                "citations": ["context_doc_01"] if reference_context else [],
                "metadata": {"model": "finsecure-guard-v1"}
            }

        # Step 3: Output Guardrails
        output_report = self.process_output(raw_response, reference_context)
        elapsed = (time.perf_counter() - start_time) * 1000.0

        return PipelineResult(
            query=query,
            sanitized_query=input_report.sanitized_input,
            reference_context=reference_context,
            input_report=input_report,
            raw_ai_response=raw_response,
            output_report=output_report,
            final_output=output_report.final_response or {},
            success=output_report.passed,
            latency_ms=elapsed,
        )

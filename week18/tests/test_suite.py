"""
Automated Test Suite and Evaluation Runner for Guardrail Pipeline.
Executes test cases, checks pass/fail against ground-truth contracts,
and computes evaluation metrics: TP, FP, TN, FN, Precision, Recall, and F1.
"""
import json
import os
import sys
import time
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from guardrails.pipeline import GuardrailPipeline
from guardrails.models import ActionTaken
from tests.test_cases import TEST_CASES, TestCase


class GuardrailTestSuite:
    def __init__(self, pipeline: GuardrailPipeline = None):
        self.pipeline = pipeline or GuardrailPipeline()

    def run_all(self) -> Dict[str, Any]:
        results_list = []
        metrics_by_category: Dict[str, Dict[str, int]] = {}
        total_tp = 0
        total_fp = 0
        total_tn = 0
        total_fn = 0
        passed_tests = 0

        for tc in TEST_CASES:
            category = tc.category
            if category not in metrics_by_category:
                metrics_by_category[category] = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}

            # Define a model generator for this test case
            def mock_generator(sanitized_input: str, reference: str):
                return tc.mock_model_output

            # Execute pipeline
            start = time.perf_counter()
            exec_res = self.pipeline.execute(
                query=tc.input_text,
                reference_context=tc.reference_context,
                model_generator=mock_generator,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            # Determine actual primary action
            actual_action = "ALLOW"
            if not exec_res.input_report.passed:
                actual_action = exec_res.input_report.primary_action.value
            elif exec_res.input_report.primary_action == ActionTaken.REDACT:
                actual_action = "REDACT"

            if exec_res.output_report:
                if not exec_res.output_report.passed:
                    actual_action = exec_res.output_report.action_taken.value
                elif exec_res.output_report.action_taken == ActionTaken.REDACT:
                    actual_action = "REDACT"

            # Check if actual behavior meets expectation
            # Primary action match:
            action_matched = (actual_action == tc.expected_primary_action)
            # If expected REDACT and actual is REDACT, or expected SAFE_FALLBACK and actual is SAFE_FALLBACK, etc.
            is_pass = action_matched

            # Metric classifications:
            # Positive = Violation / Attack present (tc.ground_truth_violation == True)
            # Negative = Benign / Safe (tc.ground_truth_violation == False)
            # Detected = Action is BLOCK, REDACT, or SAFE_FALLBACK
            action_detected_issue = (actual_action in ["BLOCK", "REDACT", "SAFE_FALLBACK"])

            if tc.ground_truth_violation:
                if action_detected_issue:
                    metrics_by_category[category]["TP"] += 1
                    total_tp += 1
                else:
                    metrics_by_category[category]["FN"] += 1
                    total_fn += 1
            else:
                if not action_detected_issue:
                    metrics_by_category[category]["TN"] += 1
                    total_tn += 1
                else:
                    metrics_by_category[category]["FP"] += 1
                    total_fp += 1

            if is_pass:
                passed_tests += 1

            # Format human-readable actual outcome summary
            actual_summary = f"Action: {actual_action} | "
            if not exec_res.input_report.passed:
                actual_summary += f"Blocked at Input ({exec_res.input_report.blocked_reason})"
            elif actual_action == "REDACT":
                actual_summary += f"Sanitized PII/Secrets in input/output"
            elif exec_res.output_report and not exec_res.output_report.passed:
                actual_summary += f"Output intercepted ({exec_res.output_report.fallback_reason})"
            else:
                actual_summary += "Response delivered successfully"

            results_list.append({
                "id": tc.id,
                "category": tc.category,
                "description": tc.description,
                "input_sample": tc.input_text[:65] + "..." if len(tc.input_text) > 65 else tc.input_text,
                "reference_context": (tc.reference_context[:50] + "...") if tc.reference_context else "None",
                "ground_truth_violation": tc.ground_truth_violation,
                "expected_action": tc.expected_primary_action,
                "actual_action": actual_action,
                "expected_behavior": tc.expected_behavior,
                "actual_summary": actual_summary,
                "status": "PASS" if is_pass else "FAIL",
                "latency_ms": round(elapsed_ms, 2),
            })

        # Calculate Precision, Recall, F1
        precision = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 1.0
        recall = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        accuracy = ((total_tp + total_tn) / len(TEST_CASES)) if len(TEST_CASES) > 0 else 0.0

        category_stats = {}
        for cat, counts in metrics_by_category.items():
            tp, fp, tn, fn = counts["TP"], counts["FP"], counts["TN"], counts["FN"]
            cat_prec = (tp / (tp + fp)) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
            cat_rec = (tp / (tp + fn)) if (tp + fn) > 0 else (1.0 if fp == 0 else 0.0)
            cat_f1 = (2 * cat_prec * cat_rec / (cat_prec + cat_rec)) if (cat_prec + cat_rec) > 0 else 0.0
            category_stats[cat] = {
                "TP": tp, "FP": fp, "TN": tn, "FN": fn,
                "Precision": round(cat_prec, 4),
                "Recall": round(cat_rec, 4),
                "F1": round(cat_f1, 4),
            }

        return {
            "summary": {
                "total_test_cases": len(TEST_CASES),
                "passed_tests": passed_tests,
                "failed_tests": len(TEST_CASES) - passed_tests,
                "pass_rate": f"{(passed_tests / len(TEST_CASES)) * 100:.1f}%",
                "metrics": {
                    "TP": total_tp,
                    "FP": total_fp,
                    "TN": total_tn,
                    "FN": total_fn,
                    "Precision": round(precision, 4),
                    "Recall": round(recall, 4),
                    "F1_Score": round(f1, 4),
                    "Accuracy": round(accuracy, 4),
                }
            },
            "category_metrics": category_stats,
            "test_details": results_list,
        }

    def generate_markdown_report(self, run_results: Dict[str, Any]) -> str:
        s = run_results["summary"]
        m = s["metrics"]

        md = []
        md.append("# Trustworthy AI Guardrails: Evaluation & Test Report\n")
        md.append(f"**Total Test Cases**: {s['total_test_cases']} | **Passed**: {s['passed_tests']} | **Pass Rate**: {s['pass_rate']}\n")

        md.append("## 1. Overall Evaluation Metrics (Ground-Truth Confusion Matrix)\n")
        md.append("| Metric | Value | Description |")
        md.append("| :--- | :--- | :--- |")
        md.append(f"| **True Positives (TP)** | `{m['TP']}` | Attacks/violations correctly identified and mitigated |")
        md.append(f"| **True Negatives (TN)** | `{m['TN']}` | Benign/safe interactions correctly allowed without hindrance |")
        md.append(f"| **False Positives (FP)** | `{m['FP']}` | Safe interactions incorrectly flagged or blocked |")
        md.append(f"| **False Negatives (FN)** | `{m['FN']}` | Attacks or violations missed by the guardrail controls |")
        md.append(f"| **Precision** | **{m['Precision'] * 100:.2f}%** | Proportion of flagged items that were genuine violations |")
        md.append(f"| **Recall** | **{m['Recall'] * 100:.2f}%** | Proportion of actual violations caught by the system |")
        md.append(f"| **F1 Score** | **{m['F1_Score'] * 100:.2f}%** | Harmonic balance between precision and recall |")
        md.append(f"| **Overall Accuracy** | **{m['Accuracy'] * 100:.2f}%** | Total correct classification rate across all inputs |")
        md.append("\n")

        md.append("## 2. Category-Level Performance Breakdown\n")
        md.append("| Category | TP | FP | TN | FN | Precision | Recall | F1 Score |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for cat, c in run_results["category_metrics"].items():
            md.append(f"| **{cat}** | {c['TP']} | {c['FP']} | {c['TN']} | {c['FN']} | {c['Precision']*100:.1f}% | {c['Recall']*100:.1f}% | {c['F1']*100:.1f}% |")
        md.append("\n")

        md.append("## 3. Detailed Test Case Audit Trail (At Least 20 Cases)\n")
        md.append("| ID | Category | Test Input & Reference | Expected Behavior | Actual Behavior | Status |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :---: |")
        for t in run_results["test_details"]:
            input_ref = f"**Input**: {t['input_sample']}<br>**Ref**: {t['reference_context']}"
            md.append(f"| **{t['id']}** | {t['category']} | {input_ref} | {t['expected_behavior']} | {t['actual_summary']} | **{t['status']}** |")
        md.append("\n")

        return "\n".join(md)


if __name__ == "__main__":
    suite = GuardrailTestSuite()
    results = suite.run_all()
    md_report = suite.generate_markdown_report(results)
    print(md_report)

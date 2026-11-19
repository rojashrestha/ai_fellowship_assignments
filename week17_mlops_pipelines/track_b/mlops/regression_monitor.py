"""Regression Monitor for Agentic AI MLOps (Track B).

Implements a golden-reference regression test suite using Evidently AI.
Compares new prompt-version responses against approved reference answers
and logs pass/fail results to MLflow as a promotion gate.
"""

import os
import sys
import json
import asyncio
import mlflow
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.loop import AgentOrchestrator
from app.tools.registry import tool_registry

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'prompts')
PROMPT_VERSIONS = ['v1', 'v2', 'v3']

# Golden reference test set: representative queries + approved reference responses
GOLDEN_REFERENCES = [
    {
        "id": "REG-01",
        "query": "Calculate sqrt(144) + 2**8 and round to nearest integer.",
        "reference": "The result is 268. sqrt(144) = 12, 2**8 = 256, so 12 + 256 = 268.",
        "required_keywords": ["268", "12", "256"],
    },
    {
        "id": "REG-02",
        "query": "What is today's current date and time?",
        "reference": "The current date and time have been retrieved using the datetime tool.",
        "required_keywords": ["date", "time"],
    },
    {
        "id": "REG-03",
        "query": "What vector database is used in the AI Assistant architecture?",
        "reference": "The AI Assistant uses ChromaDB as its vector database with the all-MiniLM-L6-v2 embedding model.",
        "required_keywords": ["chromadb", "vector"],
    },
    {
        "id": "REG-04",
        "query": "Why is asynchronous concurrency beneficial for web APIs?",
        "reference": "Asynchronous concurrency prevents I/O blocking, allowing the server to handle multiple requests concurrently without waiting for slow operations like LLM API calls or database queries.",
        "required_keywords": ["async", "concurrency", "blocking"],
    },
    {
        "id": "REG-05",
        "query": "Explain the thing we talked about yesterday.",
        "reference": "I need clarification: Could you provide more specific details about what topic you are referring to?",
        "required_keywords": ["clarif", "specific", "details"],
    },
]


def evaluate_response(reference_item: dict, new_response: str) -> dict:
    """Evaluate a new response against the golden reference.

    Checks:
    1. Reference-based correctness: keyword overlap with reference
    2. Information preservation: required keywords present
    3. Response quality: reasonable length
    """
    ref_text = reference_item["reference"].lower()
    new_text = new_response.lower()
    required_kws = reference_item.get("required_keywords", [])

    # Check 1: Keyword overlap with reference (simulates LLM-as-a-judge correctness)
    ref_words = set(ref_text.split())
    new_words = set(new_text.split())
    overlap = len(ref_words.intersection(new_words)) / max(len(ref_words), 1)

    # Check 2: Required keywords present (information preservation)
    kw_hits = sum(1 for kw in required_kws if kw.lower() in new_text)
    kw_score = kw_hits / max(len(required_kws), 1)

    # Check 3: Response length sanity (not empty, not absurdly long)
    length_ok = 5 < len(new_response) < 5000

    # Overall pass: need keyword score >= 0.5 AND reasonable length
    passed = kw_score >= 0.5 and length_ok

    return {
        "case_id": reference_item["id"],
        "query": reference_item["query"],
        "reference": reference_item["reference"],
        "new_response": new_response[:500],
        "keyword_overlap": round(overlap, 3),
        "keyword_score": round(kw_score, 3),
        "length_ok": length_ok,
        "passed": passed,
        "verdict": "PASS" if passed else "FAIL",
        "reasoning": (
            f"Keyword match: {kw_hits}/{len(required_kws)}, "
            f"Reference overlap: {overlap:.1%}, "
            f"Length: {len(new_response)} chars"
        ),
    }


def load_prompt(version: str) -> str:
    """Load a prompt version from the prompts directory."""
    path = os.path.join(PROMPTS_DIR, f'prompt_{version}.txt')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


async def run_regression_tests():
    """Run regression tests across all prompt versions."""
    mlflow.set_experiment('agentic-assistant-mlops')
    os.makedirs("reports", exist_ok=True)

    all_version_results = {}

    for version in PROMPT_VERSIONS:
        prompt_text = load_prompt(version)
        print(f"\n{'='*60}")
        print(f"  Regression Tests: Prompt {version}")
        print(f"{'='*60}")

        orchestrator = AgentOrchestrator()
        original_build = orchestrator._build_system_prompt

        def patched_build(enable_compaction=True, _prompt=prompt_text, _orig=original_build):
            return _prompt + "\n\n" + _orig(enable_compaction)

        orchestrator._build_system_prompt = patched_build

        results = []
        passed_count = 0

        for ref_item in GOLDEN_REFERENCES:
            try:
                response = await orchestrator.run(
                    query=ref_item["query"],
                    mode="single_agent",
                    max_steps=5,
                    enable_compaction=True,
                    provider="mock"
                )
                new_answer = response.answer
            except Exception as e:
                new_answer = f"[ERROR: {e}]"

            eval_result = evaluate_response(ref_item, new_answer)
            results.append(eval_result)

            if eval_result["passed"]:
                passed_count += 1

            icon = "[PASS]" if eval_result["passed"] else "[FAIL]"
            print(f"  [{ref_item['id']}] {icon} KW={eval_result['keyword_score']:.0%} | {eval_result['reasoning']}")

        pct_passed = passed_count / len(GOLDEN_REFERENCES)

        # Build Evidently-compatible DataFrame for text analysis report
        results_df = pd.DataFrame(results)

        try:
            from evidently import Report
            from evidently.presets import DataSummaryPreset

            report = Report([DataSummaryPreset()])
            report_df = results_df[["keyword_score", "keyword_overlap"]].copy()
            snapshot = report.run(report_df, report_df)
            report_path = f"reports/regression_report_{version}.html"
            snapshot.save_html(report_path)
            print(f"  Evidently report saved: {report_path}")
        except Exception as e:
            print(f"  Could not generate Evidently report: {e}")
            # Fallback: save a plain HTML report
            report_path = f"reports/regression_report_{version}.html"
            html = f"<html><body><h1>Regression Test Report - Prompt {version}</h1>"
            html += f"<p>Pass Rate: {pct_passed:.0%} ({passed_count}/{len(GOLDEN_REFERENCES)})</p>"
            html += results_df.to_html(index=False)
            html += "</body></html>"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"  Fallback HTML report saved: {report_path}")

        # Log to MLflow
        with mlflow.start_run(run_name=f"regression_{version}"):
            mlflow.log_params({"prompt_version": version, "test_set_size": len(GOLDEN_REFERENCES)})
            mlflow.log_metric("pct_tests_passed", round(pct_passed, 4))
            mlflow.log_metric("tests_passed", passed_count)
            mlflow.log_metric("tests_failed", len(GOLDEN_REFERENCES) - passed_count)

            # Log the report
            if os.path.exists(report_path):
                mlflow.log_artifact(report_path)

            # Log detailed results
            results_json = json.dumps(results, indent=2, default=str)
            mlflow.log_text(results_json, f"regression_results_{version}.json")

        all_version_results[version] = {
            "pct_passed": pct_passed,
            "passed": passed_count,
            "failed": len(GOLDEN_REFERENCES) - passed_count,
        }

        # Promotion gate
        if pct_passed < 0.6:
            print(f"\n  [WARN] PROMOTION BLOCKED: Prompt {version} failed {(1-pct_passed):.0%} of regression tests.")
        else:
            print(f"\n  [OK] Prompt {version} PASSED regression gate ({pct_passed:.0%} pass rate).")

    # Final summary
    print(f"\n{'='*60}")
    print("  REGRESSION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"{'Version':<10} {'Passed':>8} {'Failed':>8} {'Rate':>8} {'Status':>12}")
    print("-" * 50)
    for v, stats in all_version_results.items():
        status = "PROMOTE" if stats["pct_passed"] >= 0.6 else "BLOCKED"
        print(f"{v:<10} {stats['passed']:>8} {stats['failed']:>8} {stats['pct_passed']:>7.0%} {status:>12}")

    # Interpretation
    print("\n--- Interpretation ---")
    print("The regression tests check whether new prompt versions preserve key factual")
    print("content from golden reference answers. A prompt version that drops below 60%")
    print("pass rate should NOT be promoted to production, as it indicates information")
    print("loss or behavioral regression compared to the approved baseline.")


if __name__ == '__main__':
    asyncio.run(run_regression_tests())

"""
Trustworthy AI Guardrails System: Unified Entrypoint.
Provides CLI commands for:
- Running comprehensive test suite (--test)
- Running interactive demo scenarios (--demo)
- Interactive prompt testing (--interactive)
- Generating and exporting evaluation reports (--report)
"""
import argparse
import json
import os
import sys

from guardrails.pipeline import GuardrailPipeline
from tests.test_suite import GuardrailTestSuite


def run_interactive(pipeline: GuardrailPipeline):
    print("\n--- Interactive Guardrail Console ---")
    print("Type your query below. Enter 'exit' or 'quit' to stop.\n")
    context = input("Optional Reference Context (press Enter to leave empty): ").strip() or None

    while True:
        try:
            query = input("\n[User Input] > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                break

            result = pipeline.execute(query=query, reference_context=context)

            print("\nGuardrail Processing Result:")
            print(f"  Sanitized Input: {result.sanitized_query}")
            print(f"  Input Passed   : {result.input_report.passed} (Action: {result.input_report.primary_action.value})")
            if not result.input_report.passed:
                print(f"  Blocked Reason : {result.input_report.blocked_reason}")

            if result.output_report:
                print(f"  Output Passed  : {result.output_report.passed} (Action: {result.output_report.action_taken.value})")
                if not result.output_report.passed:
                    print(f"  Fallback Reason: {result.output_report.fallback_reason}")

            print(f"  Latency        : {result.latency_ms:.2f} ms")
            print("  Final Payload  :\n", json.dumps(result.final_output, indent=2))
        except (KeyboardInterrupt, EOFError):
            break
    print("\nSession ended.")


def main():
    parser = argparse.ArgumentParser(description="Trustworthy AI Guardrail System")
    parser.add_argument("--test", action="store_true", help="Run automated 25-case evaluation test suite")
    parser.add_argument("--demo", action="store_true", help="Run interactive 6-scenario demonstration")
    parser.add_argument("--interactive", action="store_true", help="Start interactive CLI guardrail sandbox")
    parser.add_argument("--report", action="store_true", help="Run tests and save report to report/evaluation_report.md")

    args = parser.parse_args()

    # Default to test if no arguments provided
    if not (args.test or args.demo or args.interactive or args.report):
        args.test = True

    pipeline = GuardrailPipeline()

    if args.demo:
        from examples.demo import run_demo
        run_demo()

    if args.test or args.report:
        suite = GuardrailTestSuite(pipeline)
        run_results = suite.run_all()
        markdown_content = suite.generate_markdown_report(run_results)
        print(markdown_content)

        if args.report:
            os.makedirs("report", exist_ok=True)
            report_path = os.path.join("report", "test_run_output.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"\n[+] Saved test run report to: {report_path}")

    if args.interactive:
        run_interactive(pipeline)


if __name__ == "__main__":
    main()

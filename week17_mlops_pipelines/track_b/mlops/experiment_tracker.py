"""Experiment Tracker for Agentic AI MLOps (Track B).

Runs the W16 eval harness across 3 prompt versions, captures structured traces,
and logs params/metrics/artifacts to MLflow for side-by-side comparison.
"""

import os
import sys
import json
import time
import asyncio
import mlflow

# Add the track_b root to the path so we can import the W16 app code
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.loop import AgentOrchestrator
from app.agent.models import AgentResponse
from evals.eval_harness import BENCHMARK_SUITE, TestCase
from app.tools.registry import tool_registry

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'prompts')
PROMPT_VERSIONS = ['v1', 'v2', 'v3']


def load_prompt(version: str) -> str:
    """Load a prompt version from the prompts directory."""
    path = os.path.join(PROMPTS_DIR, f'prompt_{version}.txt')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def response_to_trace(query: str, response: AgentResponse) -> dict:
    """Convert an AgentResponse into a structured trace record."""
    steps = []
    for step in response.trajectory.steps:
        steps.append({
            "step_number": step.step_number,
            "tool_name": step.action.tool_name,
            "arguments": step.action.arguments,
            "result": step.compacted_observation or step.observation,
            "reasoning": step.thought,
        })
    return {
        "query": query,
        "total_iterations": response.trajectory.total_steps,
        "stop_reason": response.trajectory.stop_reason,
        "total_tokens": response.trajectory.total_tokens,
        "estimated_cost_usd": response.trajectory.estimated_cost_usd,
        "answer_snippet": response.answer[:300],
        "steps": steps,
    }


def check_keyword_match(test_case: TestCase, answer: str) -> bool:
    """Check if the answer contains expected keywords."""
    if not test_case.expected_keywords:
        return True
    ans_lower = answer.lower()
    matched = sum(1 for kw in test_case.expected_keywords if kw.lower() in ans_lower)
    return matched > 0


def check_tool_correctness(test_case: TestCase, tools_called: list) -> bool:
    """Check if expected tools were selected."""
    if not test_case.expected_tools:
        return True
    return any(t in tools_called for t in test_case.expected_tools)


async def run_experiment():
    """Run the evaluation harness for each prompt version and log to MLflow."""
    mlflow.set_experiment('agentic-assistant-mlops')

    all_results = {}

    for version in PROMPT_VERSIONS:
        prompt_text = load_prompt(version)
        print(f"\n{'='*60}")
        print(f"  Evaluating Prompt Version: {version}")
        print(f"{'='*60}")

        # Create an orchestrator instance and monkey-patch the system prompt
        orchestrator = AgentOrchestrator()
        original_build = orchestrator._build_system_prompt

        def patched_build(enable_compaction=True, _prompt=prompt_text, _orig=original_build):
            """Inject the versioned prompt as the base system prompt."""
            base = _orig(enable_compaction)
            # Prepend the versioned prompt instructions
            return _prompt + "\n\n" + base

        orchestrator._build_system_prompt = patched_build

        with mlflow.start_run(run_name=f"prompt_{version}"):
            # Log parameters
            mlflow.log_params({
                "prompt_version": version,
                "temperature": 0.2,
                "max_iterations": 5,
                "provider": "mock",
                "model_choice": "mock",
                "num_test_cases": len(BENCHMARK_SUITE),
            })

            # Save prompt text as artifact
            mlflow.log_text(prompt_text, f"prompt_{version}.txt")

            traces = []
            completed_count = 0
            tool_correct_count = 0
            total_tokens = 0
            total_cost = 0.0
            total_traj_length = 0

            for tc in BENCHMARK_SUITE:
                # Set up failure injection if specified
                tool_registry.set_failure_injection(tc.failure_injection, tc.target_tool)

                try:
                    response = await orchestrator.run(
                        query=tc.query,
                        mode="single_agent",
                        max_steps=5,
                        enable_compaction=True,
                        provider="mock"
                    )

                    tools_called = [s.action.tool_name for s in response.trajectory.steps if s.action]
                    tool_ok = check_tool_correctness(tc, tools_called)
                    keyword_ok = check_keyword_match(tc, response.answer)

                    # Determine completion
                    if tc.failure_injection:
                        ans_lower = response.answer.lower()
                        completed = any(w in ans_lower for w in
                                        ["unavailable", "offline", "error", "failed", "corrupt", "could not"])
                    else:
                        completed = tool_ok and response.trajectory.stop_reason != "max_iterations_reached"

                    if completed:
                        completed_count += 1
                    if tool_ok:
                        tool_correct_count += 1

                    total_tokens += response.trajectory.total_tokens
                    total_cost += response.trajectory.estimated_cost_usd
                    total_traj_length += response.trajectory.total_steps

                    trace = response_to_trace(tc.query, response)
                    trace["case_id"] = tc.id
                    trace["category"] = tc.category
                    trace["completed"] = completed
                    trace["tool_correct"] = tool_ok
                    traces.append(trace)

                    status = "PASS" if completed else "FAIL"
                    print(f"  [{tc.id}] [{status}] Steps={response.trajectory.total_steps} "
                          f"Tools={tools_called} Tokens={response.trajectory.total_tokens}")

                except Exception as e:
                    print(f"  [{tc.id}] [ERROR] {e}")
                    traces.append({
                        "case_id": tc.id,
                        "query": tc.query,
                        "error": str(e),
                        "completed": False,
                    })
                finally:
                    tool_registry.set_failure_injection(None)

            # Compute aggregate metrics
            n = len(BENCHMARK_SUITE)
            completion_rate = completed_count / n if n > 0 else 0
            tool_correctness_rate = tool_correct_count / n if n > 0 else 0
            avg_traj = total_traj_length / n if n > 0 else 0
            avg_tokens = total_tokens / n if n > 0 else 0

            # Log metrics
            mlflow.log_metrics({
                "task_completion_rate": round(completion_rate, 4),
                "tool_correctness_rate": round(tool_correctness_rate, 4),
                "avg_trajectory_length": round(avg_traj, 2),
                "avg_tokens_per_query": round(avg_tokens, 2),
                "total_cost_usd": round(total_cost, 6),
            })

            # Save traces as artifact
            traces_path = f"traces_{version}.json"
            with open(traces_path, 'w', encoding='utf-8') as f:
                json.dump(traces, f, indent=2, default=str)
            mlflow.log_artifact(traces_path)
            os.remove(traces_path)

            all_results[version] = {
                "completion_rate": completion_rate,
                "tool_correctness": tool_correctness_rate,
                "avg_trajectory": avg_traj,
                "avg_tokens": avg_tokens,
                "total_cost": total_cost,
            }

            print(f"\n  Summary for {version}: completion={completion_rate:.0%}, "
                  f"tool_correctness={tool_correctness_rate:.0%}, avg_steps={avg_traj:.1f}")

    # Final comparison
    print(f"\n{'='*60}")
    print("  CROSS-VERSION COMPARISON")
    print(f"{'='*60}")
    print(f"{'Version':<10} {'Completion':>12} {'Tool Correct':>14} {'Avg Steps':>10} {'Avg Tokens':>12} {'Cost ($)':>10}")
    print("-" * 70)
    for v, stats in all_results.items():
        print(f"{v:<10} {stats['completion_rate']:>11.0%} {stats['tool_correctness']:>13.0%} "
              f"{stats['avg_trajectory']:>10.1f} {stats['avg_tokens']:>12.0f} {stats['total_cost']:>10.6f}")


if __name__ == '__main__':
    asyncio.run(run_experiment())

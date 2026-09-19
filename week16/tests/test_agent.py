"""Automated tests for Week 16 Agentic Loop, Verifier, Context Compaction, and Failure Injection."""

import pytest
import asyncio
from app.agent.loop import agent_orchestrator
from app.agent.verifier import verifier_agent
from app.agent.skills import skill_registry
from app.tools.registry import tool_registry


def test_single_agent_react_loop():
    """Verify single-agent ReAct loop executes tools and concludes."""
    async def _run():
        return await agent_orchestrator.run(
            query="Calculate sqrt(144) + 2**8",
            mode="single_agent",
            max_steps=4,
            provider="mock"
        )
    response = asyncio.run(_run())
    assert response is not None
    assert response.mode == "single_agent"
    assert response.trajectory.total_steps >= 1
    assert response.trajectory.stop_reason in ["goal_achieved", "completed"]
    assert "268" in response.answer or "sqrt" in response.answer or "calculated" in response.answer.lower()


def test_multi_agent_verifier_coordination():
    """Verify independent Verifier agent evaluates candidate answer with context isolation."""
    async def _run():
        return await agent_orchestrator.run(
            query="What vector database and embedding model are used in the architecture?",
            mode="multi_agent",
            max_steps=4,
            provider="mock"
        )
    response = asyncio.run(_run())
    assert response is not None
    assert response.mode == "multi_agent"
    assert response.verification is not None
    assert response.verification.passed is True
    assert response.verification.score >= 0.8
    assert response.trajectory.stop_reason in ["verifier_approved", "verifier_corrected_and_approved", "goal_achieved"]


def test_agent_stopping_condition_enforced():
    """Verify agent stops strictly at max_steps and does not run indefinitely."""
    async def _run():
        return await agent_orchestrator.run(
            query="Perform infinite searching for non-existent concept",
            mode="single_agent",
            max_steps=2,
            provider="mock"
        )
    response = asyncio.run(_run())
    assert response.trajectory.total_steps <= 2
    assert response.trajectory.total_tokens > 0


def test_context_compaction():
    """Verify observation compaction prevents context saturation."""
    raw_payload = {
        "results": [
            {"title": "Doc A", "snippet": "A" * 500},
            {"title": "Doc B", "snippet": "B" * 500}
        ],
        "status": "success"
    }
    compacted = agent_orchestrator._compact_observation("search_web", raw_payload)
    assert len(compacted) < len(str(raw_payload))
    assert "[Web Evidence" in compacted


def test_failure_injection_handling():
    """Verify system recognizes injected tool failure and adapts gracefully."""
    tool_registry.set_failure_injection("tool_unavailable", target_tool="search_web")
    try:
        async def _run():
            return await agent_orchestrator.run(
                query="Search web for latest AI news and updates",
                mode="single_agent",
                max_steps=3,
                provider="mock"
            )
        response = asyncio.run(_run())
        assert response is not None
        ans_lower = response.answer.lower()
        # Agent must acknowledge error or limitation, not hallucinate
        assert any(w in ans_lower for w in ["unavailable", "offline", "error", "failed", "could not"])
    finally:
        tool_registry.set_failure_injection(None)


def test_progressive_skill_disclosure():
    """Verify skills are initially concise and disclosed fully on demand."""
    catalog = skill_registry.get_concise_catalog()
    assert "cross_source_fact_checking" in catalog
    assert len(catalog.splitlines()) <= 5  # Small initial context footprint

    full_skill = skill_registry.load_full_skill("cross_source_fact_checking")
    assert "Instructions:" in full_skill
    assert len(full_skill) > len(catalog)

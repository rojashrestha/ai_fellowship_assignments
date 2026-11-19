"""Skill definitions and progressive disclosure manager.

Demonstrates the 'Skill vs Agent' and 'Progressive Disclosure' context engineering principles:
1. Concise summaries are provided initially to minimize context footprint.
2. Full skill instructions are loaded into context only when requested by the agent.
"""

from typing import Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    def Field(default=None, **kwargs):
        return default


class Skill(BaseModel):
    name: str = ""
    summary: str = ""
    detailed_instructions: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SkillRegistry:
    """Registry managing progressive disclosure of skills."""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._register_default_skills()

    def register(self, name: str, summary: str, detailed_instructions: str):
        self._skills[name] = Skill(
            name=name,
            summary=summary,
            detailed_instructions=detailed_instructions
        )

    def _register_default_skills(self):
        self.register(
            name="cross_source_fact_checking",
            summary="Synthesize and cross-validate conflicting claims across multiple web and internal sources.",
            detailed_instructions=(
                "Skill: Cross-Source Fact-Checking\n"
                "Instructions:\n"
                "1. Gather at least 2 distinct sources (e.g. 1 RAG internal doc + 1 Web Search query).\n"
                "2. Extract candidate facts and compare publication dates and authors.\n"
                "3. If contradictions exist, explicitly flag them and state the consensus or discrepancy.\n"
                "4. Calculate confidence based on corroborating evidence."
            )
        )
        self.register(
            name="rigorous_unit_and_date_math",
            summary="Precise arithmetic evaluation for currency, timezone differences, and compounding units.",
            detailed_instructions=(
                "Skill: Rigorous Unit and Date Math\n"
                "Instructions:\n"
                "1. Isolate the base units and reference datetimes.\n"
                "2. Always invoke the calculate tool for numerical computations; do not perform mental math.\n"
                "3. Use get_current_datetime to anchor relative dates (e.g. 'last week', '3 days ago').\n"
                "4. Round floats to 2 decimal places unless scientific precision is requested."
            )
        )

    def get_concise_catalog(self) -> str:
        """Returns brief one-liners for initial system prompt (lightweight context)."""
        lines = ["Available Skills (progressive disclosure):"]
        for s in self._skills.values():
            lines.append(f"- {s.name}: {s.summary}")
        return "\n".join(lines)

    def get_skill(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def load_full_skill(self, name: str) -> str:
        """Disclose full instructions on demand."""
        skill = self.get_skill(name)
        if skill:
            return f"\n[PROGRESSIVE DISCLOSURE: Skill '{name}' Loaded]\n{skill.detailed_instructions}\n"
        return f"\n[Error: Skill '{name}' not found]\n"


skill_registry = SkillRegistry()

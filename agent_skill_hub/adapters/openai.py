from __future__ import annotations

from typing import Any

from agent_skill_hub.core.types import Skill


def to_openai_tools(skills: dict[str, Skill] | list[Skill]) -> list[dict[str, Any]]:
    items = skills.values() if isinstance(skills, dict) else skills
    return [
        {
            "type": "function",
            "function": {
                "name": skill.name,
                "description": skill.description,
                "parameters": skill.input_schema,
            },
        }
        for skill in items
    ]

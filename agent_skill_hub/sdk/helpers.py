from __future__ import annotations

from typing import Any, Callable

from agent_skill_hub.core.types import Skill


def define_skill(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    execution_type: str = "python",
    entry: str | None = None,
    endpoint: str | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": input_schema,
        "execution": {
            "type": execution_type,
            "entry": entry,
            "endpoint": endpoint,
        },
    }


def define_handler(fn: Callable) -> Callable:
    """Marker decorator for skill handler functions."""
    fn._is_skill_handler = True  # type: ignore[attr-defined]
    return fn

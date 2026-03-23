from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
from typing import Any
from urllib.request import urlopen, Request

from .types import Skill, SkillResult

EXECUTION_TIMEOUT_S = 30


async def run_skill(skill: Skill, input_data: dict[str, Any]) -> SkillResult:
    try:
        if skill.execution.type == "python":
            return await _run_python_skill(skill, input_data)
        elif skill.execution.type == "http":
            return await _run_http_skill(skill, input_data)
        else:
            return SkillResult(success=False, error=f"Unknown execution type: {skill.execution.type}")
    except Exception as exc:
        return SkillResult(success=False, error=str(exc))


async def _run_python_skill(skill: Skill, input_data: dict[str, Any]) -> SkillResult:
    entry = skill.execution.entry
    if not entry:
        return SkillResult(success=False, error="Python skill missing 'entry' field")

    module_path = Path(skill.dir) / entry
    if not module_path.exists():
        return SkillResult(success=False, error=f"Entry file not found: {module_path}")

    spec = importlib.util.spec_from_file_location("_skill_module", str(module_path))
    if spec is None or spec.loader is None:
        return SkillResult(success=False, error="Could not load skill module")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    handler = getattr(mod, "handler", None) or getattr(mod, "run", None) or getattr(mod, "main", None)
    if handler is None:
        return SkillResult(success=False, error="Skill module does not export handler/run/main")

    if asyncio.iscoroutinefunction(handler):
        result = await asyncio.wait_for(handler(input_data), timeout=EXECUTION_TIMEOUT_S)
    else:
        result = await asyncio.wait_for(
            asyncio.to_thread(handler, input_data),
            timeout=EXECUTION_TIMEOUT_S,
        )

    return SkillResult(success=True, data=result)


async def _run_http_skill(skill: Skill, input_data: dict[str, Any]) -> SkillResult:
    endpoint = skill.execution.endpoint
    if not endpoint:
        return SkillResult(success=False, error="HTTP skill missing 'endpoint' field")

    import json

    body = json.dumps(input_data).encode("utf-8")
    req = Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")

    def _do_request():
        with urlopen(req, timeout=EXECUTION_TIMEOUT_S) as resp:
            return json.loads(resp.read())

    data = await asyncio.to_thread(_do_request)
    return SkillResult(success=True, data=data)

from __future__ import annotations

import json
from pathlib import Path

from .types import Skill


def load_skills(skills_dir: str | Path) -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    skills_path = Path(skills_dir).resolve()

    if not skills_path.is_dir():
        return skills

    for entry in skills_path.iterdir():
        if not entry.is_dir():
            continue

        skill_json = entry / "skill.json"
        if not skill_json.exists():
            continue

        try:
            raw = json.loads(skill_json.read_text(encoding="utf-8"))
            skill = Skill.model_validate(raw)
            skill.dir = str(entry)
            skills[skill.name] = skill
        except Exception as exc:
            print(f"[loader] Failed to load skill '{entry.name}': {exc}")

    return skills

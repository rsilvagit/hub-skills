from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class SkillExecution(BaseModel):
    type: Literal["python", "http"]
    entry: str | None = None
    endpoint: str | None = None


class Skill(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    input_schema: dict[str, Any]
    execution: SkillExecution
    dir: str = ""


class SkillResult(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None

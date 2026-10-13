"""Quest record — objective, hook, complication, reward."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    TRIVIAL = "trivial"
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    DEADLY = "deadly"


class Quest(BaseModel):
    quest_id: str
    title: str
    hook: str
    objective: str
    complication: str | None = None
    reward_gold: int = Field(default=0, ge=0)
    difficulty: Difficulty = Difficulty.MODERATE

    def summary(self) -> str:
        return f"[{self.difficulty.value}] {self.title}: {self.objective}"
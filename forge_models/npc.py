"""NPC record — the shape every NPC plugin ultimately produces."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NPC(BaseModel):
    npc_id: str
    name: str = Field(min_length=1, max_length=80)
    role: str = "wanderer"
    quirk: str | None = None
    secret: str | None = None
    stat_hints: dict[str, int] = Field(default_factory=dict)

    def to_prompt_line(self) -> str:
        bits = [f"{self.name} ({self.role})"]
        if self.quirk:
            bits.append(f"quirk: {self.quirk}")
        if self.secret:
            bits.append(f"secret: {self.secret}")
        return "; ".join(bits)
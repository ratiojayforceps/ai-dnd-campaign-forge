"""Session state — the mutable scratchpad a forge pass writes into."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class SessionState:
    campaign_id: str
    seed: int
    party_size: int
    started_at: datetime
    scenes: list[dict[str, Any]] = field(default_factory=list)
    sealed: bool = False

    @classmethod
    def new(cls, seed: int, party_size: int) -> "SessionState":
        return cls(
            campaign_id=f"cmp-{uuid.uuid4().hex[:10]}",
            seed=seed,
            party_size=party_size,
            started_at=datetime.now(timezone.utc),
        )

    def attach(self, fragment: dict[str, Any]) -> None:
        if self.sealed:
            raise RuntimeError("session is sealed; cannot attach fragments")
        self.scenes.append(fragment)

    def seal(self) -> None:
        self.sealed = True
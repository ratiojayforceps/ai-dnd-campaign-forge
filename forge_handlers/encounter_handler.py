"""Encounter handler — turns plugin encounter fragments into session scenes."""

from __future__ import annotations

from typing import Any

from forge_core.session import SessionState
from forge_services.llm_bridge import LLMBridge
from forge_utils.logging import get_logger

log = get_logger(__name__)


class EncounterHandler:
    def __init__(self, llm: LLMBridge) -> None:
        self._llm = llm

    async def on_encounter_fragment(self, payload: dict[str, Any]) -> None:
        session: SessionState = payload["session"]
        fragment = payload["fragment"]
        narration = await self._llm.narrate_encounter(
            encounter=fragment,
            party_size=session.party_size,
        )
        session.attach({**fragment, "narration": narration})
        log.debug("encounter.attached", campaign_id=session.campaign_id)
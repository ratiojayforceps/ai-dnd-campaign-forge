"""Shared contracts every plugin implements.

This module is the ABI. Plugins import from here and nowhere else inside the
host. Bumping anything in this file is a breaking change — record it in the
registry's ABI version and add a migration note.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from forge_core.dice import Dice
from forge_core.session import SessionState
from forge_services.llm_bridge import LLMBridge

PLUGIN_ABI_VERSION = "1.2"


class Phase(str, Enum):
    WORLD = "world"
    REGION = "region"
    FACTION = "faction"
    QUEST = "quest"
    NPC = "npc"
    ENCOUNTER = "encounter"
    RENDER = "render"


@dataclass(frozen=True, slots=True)
class PluginMeta:
    id: str
    version: str
    summary: str
    phase: Phase
    entrypoint: str
    capabilities: tuple[str, ...] = ()


@runtime_checkable
class CampaignPlugin(Protocol):
    meta: PluginMeta

    async def generate(
        self,
        session: SessionState,
        dice: Dice,
        llm: LLMBridge,
    ) -> dict[str, Any]: ...
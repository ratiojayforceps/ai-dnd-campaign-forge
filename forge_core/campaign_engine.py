"""Campaign engine.

Drives a forge pass: rolls the skeleton, dispatches generation hooks to every
registered plugin, then stitches plugin output into a coherent campaign.

Ordering matters. Structure plugins run first (world, region, faction), then
content plugins (quest, npc, encounter), then render plugins (map, handout).
The engine enforces the ordering via the plugin `phase` field, not by plugin
name — a plugin can declare any phase, but phases run in a fixed sequence.
"""

from __future__ import annotations

from typing import Final

from forge_core.dice import Dice
from forge_core.session import SessionState
from forge_handlers.event_bus import EventBus
from forge_plugins.contracts import CampaignPlugin, Phase
from forge_plugins.registry import PluginRegistry
from forge_services.llm_bridge import LLMBridge
from forge_services.persistence import CampaignStore
from forge_utils.logging import get_logger

log = get_logger(__name__)

PHASE_ORDER: Final[tuple[Phase, ...]] = (
    Phase.WORLD,
    Phase.REGION,
    Phase.FACTION,
    Phase.QUEST,
    Phase.NPC,
    Phase.ENCOUNTER,
    Phase.RENDER,
)


class CampaignEngine:
    """Runs one forge pass over a session."""

    def __init__(self, llm: LLMBridge, store: CampaignStore) -> None:
        self._llm = llm
        self._store = store

    async def run(
        self,
        session: SessionState,
        registry: PluginRegistry,
        bus: EventBus,
    ) -> None:
        dice = Dice(seed=session.seed)

        for phase in PHASE_ORDER:
            plugins: list[CampaignPlugin] = registry.by_phase(phase)
            if not plugins:
                log.debug("phase.empty", phase=phase.value)
                continue

            log.info("phase.begin", phase=phase.value, plugins=len(plugins))
            for plugin in plugins:
                try:
                    fragment = await plugin.generate(session, dice, self._llm)
                except Exception as exc:  # noqa: BLE001 — plugin boundary
                    log.error("plugin.failed", plugin=plugin.meta.id, error=str(exc))
                    await bus.emit("plugin.error", {"plugin": plugin.meta.id, "error": str(exc)})
                    continue
                session.attach(fragment)
                await bus.emit("plugin.done", {"plugin": plugin.meta.id, "phase": phase.value})

        session.seal()
        self._store.save(session)
        log.info("campaign.sealed", campaign_id=session.campaign_id, scenes=len(session.scenes))
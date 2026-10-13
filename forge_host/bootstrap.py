"""Host bootstrap — wires config, registry, services, and the event bus.

The host owns the lifecycle. Services are constructed here and injected into
handlers. Plugins are discovered from disk and registered before the first
forge pass. Nothing in this module reaches into plugin internals; everything
goes through the registry and the contracts module.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forge_config.schema import ForgeConfig
from forge_core.campaign_engine import CampaignEngine
from forge_core.session import SessionState
from forge_handlers.event_bus import EventBus
from forge_plugins.loader import PluginLoader
from forge_plugins.registry import PluginRegistry
from forge_services.llm_bridge import LLMBridge
from forge_services.persistence import CampaignStore
from forge_utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class ForgeHost:
    """The running host. One instance per process."""

    config: ForgeConfig
    registry: PluginRegistry
    bus: EventBus
    engine: CampaignEngine

    async def forge_campaign(self, seed: int, party_size: int) -> SessionState:
        session = SessionState.new(seed=seed, party_size=party_size)
        log.info("forge.start", campaign_id=session.campaign_id, seed=seed)
        await self.bus.emit("campaign.begin", session)
        await self.engine.run(session, self.registry, self.bus)
        await self.bus.emit("campaign.end", session)
        return session


def bootstrap_host(config: ForgeConfig, plugin_dir: Path) -> ForgeHost:
    registry = PluginRegistry(plugin_dir)
    registry.discover()

    loader = PluginLoader(registry)
    loader.load_all()

    llm = LLMBridge(config.llm)
    store = CampaignStore(config.storage.root)
    bus = EventBus()

    engine = CampaignEngine(llm=llm, store=store)

    log.info("host.ready", plugins=len(registry), llm=config.llm.backend)
    return ForgeHost(config=config, registry=registry, bus=bus, engine=engine)
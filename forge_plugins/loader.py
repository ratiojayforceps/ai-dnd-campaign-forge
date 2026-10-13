"""Plugin loader — imports plugin modules and binds instances to the registry."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from forge_plugins.contracts import CampaignPlugin
from forge_plugins.registry import PluginRegistry
from forge_utils.logging import get_logger

log = get_logger(__name__)


class PluginLoader:
    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry

    def load_all(self) -> None:
        for meta in self._registry.describe():
            record = self._registry._records[meta.id]  # noqa: SLF001 — loader owns binding
            module = self._import_module(meta.id, record.root / meta.entrypoint)
            if module is None:
                continue
            instance = self._instantiate(module, meta.id)
            if instance is None:
                continue
            self._registry.attach(meta.id, instance)
            log.info("plugin.loaded", plugin=meta.id, version=meta.version)

    def _import_module(self, plugin_id: str, path: Path):
        spec = importlib.util.spec_from_file_location(f"forge_plugin_{plugin_id}", path)
        if spec is None or spec.loader is None:
            log.error("loader.no_spec", plugin=plugin_id, path=str(path))
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001 — plugin import boundary
            log.error("loader.import_failed", plugin=plugin_id, error=str(exc))
            return None
        return module

    @staticmethod
    def _instantiate(module, plugin_id: str) -> CampaignPlugin | None:
        factory = getattr(module, "build_plugin", None)
        if not callable(factory):
            log.error("loader.no_factory", plugin=plugin_id)
            return None
        try:
            instance = factory()
        except Exception as exc:  # noqa: BLE001
            log.error("loader.factory_failed", plugin=plugin_id, error=str(exc))
            return None
        if not isinstance(instance, CampaignPlugin):
            log.error("loader.bad_contract", plugin=plugin_id)
            return None
        return instance
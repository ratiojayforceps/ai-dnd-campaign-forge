"""Plugin registry — discovery, metadata validation, phase indexing.

Discovery walks a directory for `plugin.toml` files, parses them, and
validates the declared entrypoint stays inside the plugin directory. Anything
that escapes is rejected with a logged reason and skipped.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from forge_plugins.contracts import PLUGIN_ABI_VERSION, CampaignPlugin, Phase, PluginMeta
from forge_utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class PluginRecord:
    meta: PluginMeta
    root: Path
    instance: CampaignPlugin | None = None


class PluginRegistry:
    def __init__(self, plugin_dir: Path) -> None:
        self._root = plugin_dir
        self._records: dict[str, PluginRecord] = {}

    def discover(self) -> None:
        if not self._root.exists():
            log.warning("registry.missing_dir", path=str(self._root))
            return
        for toml_path in sorted(self._root.glob("*/plugin.toml")):
            self._register(toml_path)

    def _register(self, toml_path: Path) -> None:
        try:
            data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            log.error("registry.bad_toml", path=str(toml_path), error=str(exc))
            return

        plugin_root = toml_path.parent
        entrypoint = data.get("entrypoint", "")
        if not self._entrypoint_is_safe(plugin_root, entrypoint):
            log.error("registry.unsafe_entrypoint", plugin=data.get("id"), entry=entrypoint)
            return

        abi = data.get("abi", "1.0")
        if abi.split(".")[0] != PLUGIN_ABI_VERSION.split(".")[0]:
            log.error("registry.abi_mismatch", plugin=data.get("id"), abi=abi)
            return

        meta = PluginMeta(
            id=data["id"],
            version=data["version"],
            summary=data.get("summary", ""),
            phase=Phase(data["phase"]),
            entrypoint=entrypoint,
            capabilities=tuple(data.get("capabilities", ())),
        )
        self._records[meta.id] = PluginRecord(meta=meta, root=plugin_root)
        log.debug("registry.registered", plugin=meta.id, phase=meta.phase.value)

    @staticmethod
    def _entrypoint_is_safe(root: Path, entrypoint: str) -> bool:
        if not entrypoint or entrypoint.startswith(("/", "\\")):
            return False
        candidate = (root / entrypoint).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            return False
        return candidate.suffix == ".py"

    def by_phase(self, phase: Phase) -> list[CampaignPlugin]:
        return [
            rec.instance
            for rec in self._records.values()
            if rec.meta.phase == phase and rec.instance is not None
        ]

    def describe(self) -> list[PluginMeta]:
        return [rec.meta for rec in self._records.values()]

    def attach(self, plugin_id: str, instance: CampaignPlugin) -> None:
        if plugin_id not in self._records:
            raise KeyError(f"unknown plugin: {plugin_id}")
        self._records[plugin_id].instance = instance

    def __len__(self) -> int:
        return len(self._records)
"""NPC synthesis — assembles a coherent NPC from plugin-contributed traits.

Plugins contribute trait fragments (name, role, quirk, secret). This module
merges them, resolves conflicts by phase priority, and produces a final NPC
record that the render phase can format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from forge_models.npc import NPC


@dataclass(slots=True)
class TraitPool:
    name: list[str] = field(default_factory=list)
    role: list[str] = field(default_factory=list)
    quirk: list[str] = field(default_factory=list)
    secret: list[str] = field(default_factory=list)
    stat_hints: dict[str, int] = field(default_factory=dict)


def synthesize(pool: TraitPool, npc_id: str) -> NPC:
    if not pool.name:
        raise ValueError("trait pool has no names; at least one name plugin must run")
    return NPC(
        npc_id=npc_id,
        name=pool.name[0],
        role=pool.role[0] if pool.role else "wanderer",
        quirk=pool.quirk[0] if pool.quirk else None,
        secret=pool.secret[0] if pool.secret else None,
        stat_hints=dict(pool.stat_hints),
    )


def merge_fragment(pool: TraitPool, fragment: dict[str, Any]) -> None:
    for key in ("name", "role", "quirk", "secret"):
        if key in fragment and isinstance(fragment[key], str):
            getattr(pool, key).append(fragment[key])
    if "stat_hints" in fragment and isinstance(fragment["stat_hints"], dict):
        pool.stat_hints.update(fragment["stat_hints"])
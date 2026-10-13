"""Minimal async event bus.

Handlers subscribe to named events. The host emits lifecycle events
(`campaign.begin`, `plugin.done`, `campaign.end`). Handlers are awaited in
subscription order; a handler that raises is logged and skipped, never
allowed to abort the forge pass.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Awaitable, Callable

from forge_utils.logging import get_logger

log = get_logger(__name__)

Handler = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Handler]] = defaultdict(list)

    def on(self, event: str, handler: Handler) -> None:
        self._subs[event].append(handler)

    async def emit(self, event: str, payload: Any) -> None:
        handlers = self._subs.get(event, [])
        if not handlers:
            return
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as exc:  # noqa: BLE001 — handler boundary
                log.error("handler.failed", event=event, error=str(exc))
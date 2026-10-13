"""LLM bridge.

Single choke point for every model call. Backends: `openai` (remote HTTP),
`local` (llama-cpp-python, in-process), `null` (deterministic stub for tests).
Plugins never call a backend directly — they call `LLMBridge.complete`.

Prompt sanitization strips the obvious injection vectors from campaign text
before it enters the system prompt. Not a security boundary; a hygiene step.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from forge_config.schema import LLMConfig
from forge_utils.logging import get_logger

log = get_logger(__name__)

_INJECTION_PATTERNS = re.compile(
    r"(ignore (all )?previous|disregard (the )?system|you are now|new instructions:)",
    re.IGNORECASE,
)


class Backend(Protocol):
    async def complete(self, system: str, user: str, **kw: Any) -> str: ...


@dataclass(slots=True)
class _NullBackend:
    async def complete(self, system: str, user: str, **kw: Any) -> str:
        return f"[null-backend] {user[:80]}"


class _OpenAIBackend:
    def __init__(self, cfg: LLMConfig) -> None:
        self._cfg = cfg
        self._client = httpx.AsyncClient(timeout=cfg.timeout_s)

    async def complete(self, system: str, user: str, **kw: Any) -> str:
        resp = await self._client.post(
            f"{self._cfg.endpoint}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._cfg.api_key}"},
            json={
                "model": self._cfg.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": kw.get("temperature", self._cfg.temperature),
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class LLMBridge:
    def __init__(self, cfg: LLMConfig) -> None:
        self._cfg = cfg
        self._backend: Backend
        if cfg.backend == "openai":
            self._backend = _OpenAIBackend(cfg)
        elif cfg.backend == "null":
            self._backend = _NullBackend()
        else:
            raise ValueError(f"unsupported backend: {cfg.backend}")

    @staticmethod
    def sanitize_prompt(text: str) -> str:
        return _INJECTION_PATTERNS.sub("[redacted]", text)

    async def complete(self, system: str, user: str, **kw: Any) -> str:
        clean_user = self.sanitize_prompt(user)
        log.debug("llm.call", backend=self._cfg.backend, model=self._cfg.model)
        return await self._backend.complete(system, clean_user, **kw)

    async def narrate_encounter(self, encounter: dict[str, Any], party_size: int) -> str:
        system = (
            "You are a D&D 5e dungeon master. Narrate the encounter in 2-3 "
            "sentences. Match tone to the encounter's difficulty."
        )
        user = f"Encounter: {encounter}\nParty size: {party_size}"
        return await self.complete(system, user, temperature=0.8)
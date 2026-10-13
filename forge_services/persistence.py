"""Campaign persistence — JSON session files under a storage root."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from forge_core.session import SessionState
from forge_utils.logging import get_logger

log = get_logger(__name__)


class CampaignStore:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, session: SessionState) -> Path:
        path = self._root / f"{session.campaign_id}.json"
        payload = asdict(session)
        payload["started_at"] = session.started_at.isoformat()
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log.info("campaign.saved", path=str(path))
        return path

    def load(self, campaign_id: str) -> dict:
        path = self._root / f"{campaign_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def list_recent(self, limit: int = 20) -> list[str]:
        files = sorted(self._root.glob("cmp-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return [p.stem for p in files[:limit]]

    def touch(self, campaign_id: str) -> datetime:
        path = self._root / f"{campaign_id}.json"
        return datetime.fromtimestamp(path.stat().st_mtime)
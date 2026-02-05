import json
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import SETTINGS


class MockAPIBridge:
    def __init__(
        self,
        session_id: str,
        competition_key: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.session_id = session_id
        self.competition_key = competition_key or SETTINGS.MOCK_SCAMMER_API_KEY
        self.api_url = (api_url or SETTINGS.MOCK_SCAMMER_API_URL or "").rstrip("/")
        self.history: List[Dict[str, Any]] = []

    def add_turn(self, role: str, content: str) -> None:
        if not role or content is None:
            return
        self.history.append({"role": str(role), "content": str(content)})
        if len(self.history) > 120:
            self.history = self.history[-120:]

    async def simulate_scammer_response(self, our_message: str) -> str:
        if not self.api_url:
            return ""

        headers = {}
        if self.competition_key:
            headers["X-API-KEY"] = self.competition_key

        payload = {
            "session_id": self.session_id,
            "our_last_message": our_message,
            "history": self.history,
        }

        timeout_s = SETTINGS.MOCK_SCAMMER_TIMEOUT_SECONDS
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                r = await client.post(
                    f"{self.api_url}/next-message",
                    json=payload,
                    headers=headers,
                )
                r.raise_for_status()
                data = r.json()
                msg = data.get("scammer_message")
                return str(msg) if msg is not None else ""
        except Exception:
            return ""

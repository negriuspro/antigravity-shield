from typing import Any
import httpx
from app.config import get_settings

settings = get_settings()


class AdGuardClient:
    def __init__(self):
        self._base = settings.adguard_base_url
        self._auth = (settings.adguard_user, settings.adguard_password)

    async def _get(self, path: str) -> Any:
        async with httpx.AsyncClient(auth=self._auth, timeout=10) as client:
            resp = await client.get(f"{self._base}{path}")
            resp.raise_for_status()
            return resp.json()

    async def _post(self, path: str, data: Any = None) -> Any:
        async with httpx.AsyncClient(auth=self._auth, timeout=10) as client:
            resp = await client.post(f"{self._base}{path}", json=data)
            resp.raise_for_status()
            return resp.json() if resp.text else None

    async def get_status(self) -> dict:
        return await self._get("/control/status")

    async def get_stats(self) -> dict:
        return await self._get("/control/stats")

    async def get_query_log(self, limit: int = 100, offset: int = 0) -> dict:
        return await self._get(f"/control/querylog?limit={limit}&offset={offset}")

    async def get_clients(self) -> dict:
        return await self._get("/control/clients")

    async def get_filtering_status(self) -> dict:
        return await self._get("/control/filtering/status")

    async def add_filter_rule(self, rules: list[str]) -> None:
        await self._post("/control/filtering/add_url", {"url": rules[0], "name": "Custom"})

    async def block_client(self, client_id: str) -> None:
        clients = await self.get_clients()
        # patch client to add blocked status via client settings
        await self._post("/control/clients/update", {
            "data": {"ids": [client_id], "blocked_services": {"schedule": {}, "ids": ["all"]}},
            "name": client_id,
        })

    async def get_top_domains(self, limit: int = 10) -> dict:
        stats = await self.get_stats()
        return {
            "top_blocked": stats.get("top_blocked_domains", [])[:limit],
            "top_queried": stats.get("top_queried_domains", [])[:limit],
            "top_clients": stats.get("top_clients", [])[:limit],
        }

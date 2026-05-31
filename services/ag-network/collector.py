import logging
from datetime import datetime, timezone
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from config import Settings

log = logging.getLogger("ag-network.collector")


class AdGuardCollector:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self._session = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)
        self._last_offset = 0

    async def init_db(self):
        async with self._engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        log.info("Database connection OK")

    async def _fetch_querylog(self, limit: int = 500) -> list[dict]:
        auth = (self.settings.adguard_user, self.settings.adguard_password)
        url = f"{self.settings.adguard_base_url}/control/querylog?limit={limit}&offset={self._last_offset}"
        async with httpx.AsyncClient(auth=auth, timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])

    async def _upsert_device(self, session: AsyncSession, client_ip: str) -> str | None:
        result = await session.execute(
            text("SELECT id FROM devices WHERE ip = :ip LIMIT 1"),
            {"ip": client_ip},
        )
        row = result.fetchone()
        if row:
            await session.execute(
                text("UPDATE devices SET last_seen = NOW(), status = 'online' WHERE ip = :ip"),
                {"ip": client_ip},
            )
            return str(row[0])
        return None

    async def _insert_query(self, session: AsyncSession, entry: dict, device_id: str | None):
        answer = entry.get("answer", [{}])
        upstream = entry.get("upstream", "")
        reason = entry.get("reason", "")
        blocked = reason != "" and "NotFilteredNotFound" not in reason

        queried_at_raw = entry.get("time", "")
        try:
            queried_at = datetime.fromisoformat(queried_at_raw.replace("Z", "+00:00"))
        except Exception:
            queried_at = datetime.now(timezone.utc)

        await session.execute(
            text("""
                INSERT INTO dns_queries
                    (device_id, client_ip, domain, query_type, blocked, reason, upstream, queried_at)
                VALUES
                    (:device_id, :client_ip, :domain, :query_type, :blocked, :reason, :upstream, :queried_at)
                ON CONFLICT DO NOTHING
            """),
            {
                "device_id": device_id,
                "client_ip": entry.get("client", ""),
                "domain": entry.get("question", {}).get("name", ""),
                "query_type": entry.get("question", {}).get("type", "A"),
                "blocked": blocked,
                "reason": reason[:255] if reason else None,
                "upstream": upstream[:100] if upstream else None,
                "queried_at": queried_at,
            },
        )

        if blocked:
            domain = entry.get("question", {}).get("name", "")
            await session.execute(
                text("""
                    INSERT INTO blocked_requests (domain, count, first_seen, last_seen)
                    VALUES (:domain, 1, NOW(), NOW())
                    ON CONFLICT (domain) DO UPDATE
                    SET count = blocked_requests.count + 1, last_seen = NOW()
                """),
                {"domain": domain},
            )

    async def collect(self):
        entries = await self._fetch_querylog(limit=200)
        if not entries:
            return

        async with self._session() as session:
            for entry in entries:
                client_ip = entry.get("client", "")
                if not client_ip:
                    continue
                device_id = await self._upsert_device(session, client_ip)
                await self._insert_query(session, entry, device_id)
            await session.commit()

        log.info("Collected %d DNS entries", len(entries))

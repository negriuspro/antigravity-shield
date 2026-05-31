import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta

from app.database import AsyncSessionLocal
from app.models.dns_query import DnsQuery


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


async def realtime_feed(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            async with AsyncSessionLocal() as db:
                since = datetime.now(timezone.utc) - timedelta(seconds=5)
                total = await db.scalar(select(func.count()).where(DnsQuery.queried_at >= since)) or 0
                blocked = await db.scalar(
                    select(func.count()).where(DnsQuery.queried_at >= since, DnsQuery.blocked == True)
                ) or 0
            await ws.send_text(json.dumps({
                "type": "stats",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "queries_last_5s": total,
                "blocked_last_5s": blocked,
            }))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(ws)

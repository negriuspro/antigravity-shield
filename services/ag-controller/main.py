"""
ag-controller — Device Discovery & Inventory
Scans local network via ARP and maintains device registry in PostgreSQL.
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from config import Settings
from scanner import scan, DiscoveredDevice

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ag-controller")


class DeviceController:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self._session = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    async def upsert_device(self, session: AsyncSession, dev: DiscoveredDevice):
        await session.execute(
            text("""
                INSERT INTO devices (mac, ip, hostname, manufacturer, status, last_seen, first_seen)
                VALUES (:mac, :ip, :hostname, :manufacturer, 'online', NOW(), NOW())
                ON CONFLICT (mac) DO UPDATE SET
                    ip = EXCLUDED.ip,
                    hostname = COALESCE(EXCLUDED.hostname, devices.hostname),
                    manufacturer = COALESCE(EXCLUDED.manufacturer, devices.manufacturer),
                    status = 'online',
                    last_seen = NOW(),
                    updated_at = NOW()
            """),
            {
                "mac": dev.mac,
                "ip": dev.ip,
                "hostname": dev.hostname,
                "manufacturer": dev.manufacturer,
            },
        )

    async def mark_offline(self, session: AsyncSession, active_ips: list[str]):
        if not active_ips:
            return
        placeholders = ", ".join(f":ip{i}" for i in range(len(active_ips)))
        params = {f"ip{i}": ip for i, ip in enumerate(active_ips)}
        await session.execute(
            text(f"UPDATE devices SET status = 'offline' WHERE ip NOT IN ({placeholders}) AND status = 'online'"),
            params,
        )

    async def run_scan(self):
        log.info("Scanning %s on %s", self.settings.network_subnet, self.settings.network_interface)
        devices = await scan(self.settings.network_subnet, self.settings.network_interface)
        log.info("Found %d devices", len(devices))

        async with self._session() as session:
            for dev in devices:
                await self.upsert_device(session, dev)
            await self.mark_offline(session, [d.ip for d in devices])
            await session.commit()


async def main():
    settings = Settings()
    controller = DeviceController(settings)
    log.info("ag-controller started — scanning every %ds", settings.scan_interval_seconds)
    while True:
        try:
            await controller.run_scan()
        except Exception as e:
            log.error("Scan error: %s", e)
        await asyncio.sleep(settings.scan_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())

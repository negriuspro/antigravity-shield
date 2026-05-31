"""
ag-network — Network Analytics Collector
Polls AdGuard Home API and stores DNS data in PostgreSQL.
"""
import asyncio
import logging
from collector import AdGuardCollector
from config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ag-network")


async def main():
    settings = Settings()
    collector = AdGuardCollector(settings)
    await collector.init_db()
    log.info("ag-network started — polling every %ds", settings.poll_interval)
    while True:
        try:
            await collector.collect()
        except Exception as e:
            log.error("Collection error: %s", e)
        await asyncio.sleep(settings.poll_interval)


if __name__ == "__main__":
    asyncio.run(main())

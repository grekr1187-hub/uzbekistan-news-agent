from __future__ import annotations

import asyncio
import logging
import os

from .config import Settings
from .worker import NewsWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def main() -> None:
    settings = Settings.from_env()
    worker = NewsWorker(settings)
    if os.getenv("RUN_MODE", "continuous").lower() == "cron":
        asyncio.run(worker.run_scheduled())
    else:
        asyncio.run(worker.run_forever())


if __name__ == "__main__":
    main()

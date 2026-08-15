from __future__ import annotations

import asyncio
import logging

from .config import Settings
from .worker import NewsWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def main() -> None:
    settings = Settings.from_env()
    asyncio.run(NewsWorker(settings).run_forever())


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    telegram_bot_token: str
    telegram_channel_id: str
    poll_interval_seconds: int = 300
    database_path: str = "data/news.db"

    @classmethod
    def from_env(cls) -> "Settings":
        required = ("OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise ValueError("Missing required environment variables: " + ", ".join(missing))
        return cls(
            openai_api_key=os.environ["OPENAI_API_KEY"],
            telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
            telegram_channel_id=os.environ["TELEGRAM_CHANNEL_ID"],
            poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "300")),
            database_path=os.getenv("DATABASE_PATH", "data/news.db"),
        )

from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser
import httpx

from .models import RawItem
from .sources import Source

log = logging.getLogger(__name__)


class SourceCollector:
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    async def fetch(self, source: Source) -> list[RawItem]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers={"User-Agent": "UzbekistanNewsAgent/0.1"}) as client:
            response = await client.get(source.url)
            response.raise_for_status()
        feed = feedparser.parse(response.text)
        items: list[RawItem] = []
        for entry in feed.entries[:50]:
            published = None
            if getattr(entry, "published_parsed", None):
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            items.append(RawItem(
                title=str(getattr(entry, "title", "")).strip(),
                url=str(getattr(entry, "link", "")).strip(),
                source=source.name,
                published_at=published,
                summary=str(getattr(entry, "summary", "")).strip(),
            ))
        return items

    async def collect(self, sources: list[Source]) -> list[RawItem]:
        result: list[RawItem] = []
        for source in sources:
            try:
                result.extend(await self.fetch(source))
            except Exception as exc:
                log.warning("source_failed source=%s error=%s", source.name, exc.__class__.__name__)
        return result

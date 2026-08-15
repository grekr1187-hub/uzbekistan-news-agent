from __future__ import annotations

import asyncio
import logging

from .collector import SourceCollector
from .config import Settings
from .dedupe import is_duplicate
from .editor import AIEditor
from .models import Story
from .sources import DEFAULT_SOURCES
from .store import StoryStore
from .telegram import TelegramPublisher

log = logging.getLogger(__name__)


class NewsWorker:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = StoryStore(settings.database_path)
        self.collector = SourceCollector()
        self.editor = AIEditor(settings.openai_api_key)
        self.publisher = TelegramPublisher(settings.telegram_bot_token, settings.telegram_channel_id)

    async def run_once(self) -> int:
        items = await self.collector.collect(DEFAULT_SOURCES)
        recent_titles = self.store.find_recent_titles()
        stories: list[Story] = []
        for item in items:
            if not item.title or not item.url or is_duplicate(item.title, item.url, recent_titles):
                continue
            story = Story(item.title, item.url, item.source, item.published_at, item.summary)
            if self.store.upsert_story(story):
                stories.append(story)
        stories.sort(key=lambda s: s.published_at or 0, reverse=True)
        published = 0
        for story in stories[:20]:
            try:
                decision = await self.editor.evaluate_and_write(story, [])
                self.store.mark_status(story.url, decision.status)
                if decision.status == "reject":
                    continue
                message_id = await self.publisher.publish(decision, [story.url])
                self.store.mark_published(story.url, message_id)
                published += 1
            except Exception as exc:
                log.exception("story_failed url=%s error=%s", story.url, exc.__class__.__name__)
        return published

    async def run_forever(self) -> None:
        while True:
            try:
                await self.run_once()
            except Exception as exc:
                log.exception("cycle_failed error=%s", exc.__class__.__name__)
            await asyncio.sleep(self.settings.poll_interval_seconds)

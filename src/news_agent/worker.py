from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from .collector import SourceCollector
from .config import Settings
from .dedupe import is_duplicate
from .editor import AIEditor
from .models import Story
from .sources import DEFAULT_SOURCES
from .store import StoryStore, make_review_key
from .telegram import TelegramPublisher
from .video import make_news_image, make_news_video

log = logging.getLogger(__name__)


class NewsWorker:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = StoryStore(settings.database_path)
        self.collector = SourceCollector()
        self.editor = AIEditor(settings.openai_api_key)
        self.publisher = TelegramPublisher(settings.telegram_bot_token, settings.telegram_channel_id)
        self._update_offset: int | None = None
        self.bootstrap_url = os.getenv("AUTO_PUBLISH_URL", "").strip()
        self.bootstrap_title = "Государственный долг Узбекистана превысил 48 млрд долларов"
        self.generate_video = os.getenv("GENERATE_VIDEO", "false").strip().lower() in {"1", "true", "yes", "on"}

    def _media_path(self, story_key: str, suffix: str) -> str:
        safe = "".join(c if c.isalnum() else "_" for c in story_key)[:40]
        return str(Path(tempfile.gettempdir()) / f"news_{safe}.{suffix}")

    async def _make_image(self, story: Story, decision) -> str | None:
        try:
            path = self._media_path(story.review_key or make_review_key(story.url), "jpg")
            return await asyncio.to_thread(make_news_image, decision.ru_title, decision.ru_body, path)
        except Exception as exc:
            log.exception("image_generation_failed error=%s", exc.__class__.__name__)
            return None

    async def _make_video(self, story: Story, decision) -> str | None:
        if not self.generate_video:
            return None
        try:
            path = self._media_path(story.review_key or make_review_key(story.url), "mp4")
            return await asyncio.to_thread(make_news_video, decision.ru_title, decision.ru_body, path)
        except Exception as exc:
            log.exception("video_generation_failed error=%s", exc.__class__.__name__)
            return None

    async def _make_media(self, story: Story, decision) -> tuple[str | None, str | None]:
        image = await self._make_image(story, decision)
        video = await self._make_video(story, decision)
        return video, image

    async def run_once(self) -> int:
        items = await self.collector.collect(DEFAULT_SOURCES)
        recent_titles = self.store.find_recent_titles()
        stories: list[Story] = []
        for item in items:
            if not item.title or not item.url or is_duplicate(item.title, item.url, recent_titles):
                continue
            story = Story(item.title, item.url, item.source, item.published_at, item.summary, review_key=make_review_key(item.url))
            if self.store.upsert_story(story):
                stories.append(story)
        stories.sort(key=lambda s: s.published_at or 0, reverse=True)
        reviews = 0
        for story in stories[:20]:
            try:
                decision = await self.editor.evaluate_and_write(story, [])
                self.store.mark_status(story.url, decision.status)
                if decision.status == "reject":
                    self.store.set_review_status(story.url, "rejected")
                    continue
                video, image = await self._make_media(story, decision)

                # One-time launch test: publish the requested current-day Uzbekistan headline directly.
                launch_post = (
                    self.bootstrap_url == "*"
                    or (self.bootstrap_url and story.url == self.bootstrap_url)
                    or (self.bootstrap_url == "" and self.bootstrap_title.lower() in story.title.lower())
                )
                if launch_post:
                    message_id = await self.publisher.publish(decision, [story.url], video, image)
                    self.store.mark_published(story.url, message_id)
                    self.bootstrap_url = "__done__"
                    continue

                key = story.review_key or make_review_key(story.url)
                message_id = await self.publisher.send_review(decision, key, [story.url], self.settings.telegram_admin_user_id, video, image)
                self.store.set_review_message(story.url, message_id)
                reviews += 1
            except Exception as exc:
                log.exception("story_review_failed url=%s error=%s", story.url, exc.__class__.__name__)
        return reviews

    async def run_scheduled(self) -> int:
        """Run exactly one collection/publish cycle for Railway cron/manual runs."""
        await self.publisher.initialize()
        try:
            return await self.run_once()
        finally:
            await self.publisher.close()

    async def handle_review_action(self, action: str, story_key: str, user_id: int) -> None:
        if user_id != self.settings.telegram_admin_user_id:
            return
        story = self.store.get_by_review_key(story_key)
        if story is None or not story.review_message_id:
            return
        if action == "reject":
            if story.review_status in {"rejected", "published"}:
                return
            self.store.set_review_status(story.url, "rejected")
            await self.publisher.finish_review(user_id, story.review_message_id, "❌ <b>Отклонено</b>\n\nНовость не опубликована.")
            return
        if action == "regenerate":
            if story.review_status in {"rejected", "published"}:
                return
            decision = await self.editor.evaluate_and_write(story, [])
            video, image = await self._make_media(story, decision)
            await self.publisher.update_review(user_id, story.review_message_id, decision, [story.url], story_key, video, image)
            self.store.mark_status(story.url, decision.status)
            return
        if action == "approve":
            if story.review_status in {"rejected", "published"} or story.telegram_message_id:
                return
            self.store.set_review_status(story.url, "approved")
            decision = await self.editor.evaluate_and_write(story, [])
            if decision.status == "reject":
                self.store.set_review_status(story.url, "rejected")
                await self.publisher.finish_review(user_id, story.review_message_id, "❌ <b>Отклонено AI-проверкой</b>\n\nНовость не опубликована.")
                return
            video, image = await self._make_media(story, decision)
            message_id = await self.publisher.publish(decision, [story.url], video, image)
            self.store.mark_published(story.url, message_id)
            await self.publisher.finish_review(user_id, story.review_message_id, f"✅ <b>Опубликовано</b>\n\nСообщение канала: #{message_id}")

    async def process_updates(self) -> None:
        while True:
            try:
                updates = await self.publisher.get_updates(self._update_offset)
                for update in updates:
                    self._update_offset = update.update_id + 1
                    callback = update.callback_query
                    if callback is None or callback.from_user is None or not callback.data:
                        continue
                    parts = callback.data.split(":", 2)
                    if len(parts) != 3 or parts[0] != "news":
                        continue
                    action, key = parts[1], parts[2]
                    if callback.from_user.id != self.settings.telegram_admin_user_id:
                        await self.publisher.answer_callback(callback.id, "Нет доступа", show_alert=True)
                        continue
                    await self.publisher.answer_callback(callback.id, "Обрабатываю…")
                    try:
                        await self.handle_review_action(action, key, callback.from_user.id)
                    except Exception as exc:
                        log.exception("review_action_failed key=%s error=%s", key, exc.__class__.__name__)
                        await self.publisher.answer_callback(callback.id, "Ошибка обработки", show_alert=True)
            except Exception as exc:
                log.exception("telegram_updates_failed error=%s", exc.__class__.__name__)
                await asyncio.sleep(5)

    async def run_forever(self) -> None:
        await self.publisher.initialize()
        update_task = asyncio.create_task(self.process_updates())
        try:
            while True:
                try:
                    await self.run_once()
                except Exception as exc:
                    log.exception("cycle_failed error=%s", exc.__class__.__name__)
                await asyncio.sleep(self.settings.poll_interval_seconds)
        finally:
            update_task.cancel()
            await self.publisher.close()

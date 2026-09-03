from __future__ import annotations

from pathlib import Path

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from .models import EditorialDecision


def render(decision: EditorialDecision, sources: list[str], review: bool = False) -> str:
    marker = "🔴 СРОЧНО" if decision.priority >= 85 else ("🟡 ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ" if decision.status == "unconfirmed" else "🇺🇿 НОВОСТИ")
    source_text = "\n".join(f"• {url}" for url in sources[:4])
    review_note = "\n\n🛡 Черновик. В канал не опубликовано." if review else ""
    return (f"{marker}\n\n<b>{decision.ru_title}</b>\n{decision.ru_body}\n\n"
            f"🇺🇿 <b>{decision.uz_title}</b>\n{decision.uz_body}\n\n"
            f"📊 Надёжность: {decision.confidence:.0%}\n"
            f"📝 {decision.reason}\n\n"
            f"📌 Источники / Manbalar:\n{source_text}\n\n"
            f"🇺🇿 Узбекистан слушает{review_note}")


def review_keyboard(story_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Опубликовать", callback_data=f"news:approve:{story_key}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"news:reject:{story_key}"),
         InlineKeyboardButton("✏️ Переписать", callback_data=f"news:regenerate:{story_key}")],
    ])


class TelegramPublisher:
    def __init__(self, token: str, channel_id: str):
        self.bot = Bot(token=token)
        self.channel_id = channel_id

    async def initialize(self) -> None:
        await self.bot.initialize()

    async def publish(self, decision: EditorialDecision, sources: list[str], video_path: str | None = None, image_path: str | None = None) -> str:
        if video_path and Path(video_path).exists():
            try:
                with open(video_path, "rb") as video:
                    message = await self.bot.send_video(chat_id=self.channel_id, video=video, caption=render(decision, sources), parse_mode="HTML")
                return str(message.message_id)
            except Exception:
                pass
        if image_path and Path(image_path).exists():
            try:
                with open(image_path, "rb") as image:
                    message = await self.bot.send_photo(chat_id=self.channel_id, photo=image, caption=render(decision, sources), parse_mode="HTML")
                return str(message.message_id)
            except Exception:
                pass
        message = await self.bot.send_message(chat_id=self.channel_id, text=render(decision, sources), parse_mode="HTML", disable_web_page_preview=True)
        return str(message.message_id)

    async def send_review(self, decision: EditorialDecision, story_key: str, sources: list[str], admin_user_id: int, video_path: str | None = None, image_path: str | None = None) -> str:
        if video_path and Path(video_path).exists():
            try:
                with open(video_path, "rb") as video:
                    message = await self.bot.send_video(chat_id=admin_user_id, video=video, caption=render(decision, sources, review=True), parse_mode="HTML", reply_markup=review_keyboard(story_key))
                return str(message.message_id)
            except Exception:
                pass
        if image_path and Path(image_path).exists():
            try:
                with open(image_path, "rb") as image:
                    message = await self.bot.send_photo(chat_id=admin_user_id, photo=image, caption=render(decision, sources, review=True), parse_mode="HTML", reply_markup=review_keyboard(story_key))
                return str(message.message_id)
            except Exception:
                pass
        message = await self.bot.send_message(chat_id=admin_user_id, text=render(decision, sources, review=True), parse_mode="HTML", disable_web_page_preview=True, reply_markup=review_keyboard(story_key))
        return str(message.message_id)

    async def update_review(self, admin_user_id: int, message_id: str, decision: EditorialDecision, sources: list[str], story_key: str, video_path: str | None = None, image_path: str | None = None) -> None:
        try:
            await self.bot.edit_message_text(chat_id=admin_user_id, message_id=int(message_id), text=render(decision, sources, review=True), parse_mode="HTML", disable_web_page_preview=True, reply_markup=review_keyboard(story_key))
        except Exception:
            pass
        if video_path and Path(video_path).exists():
            try:
                with open(video_path, "rb") as video:
                    await self.bot.send_video(chat_id=admin_user_id, video=video, caption=f"🎬 {decision.ru_title}")
                return
            except Exception:
                pass
        if image_path and Path(image_path).exists():
            try:
                with open(image_path, "rb") as image:
                    await self.bot.send_photo(chat_id=admin_user_id, photo=image, caption=f"🖼 {decision.ru_title}")
            except Exception:
                pass

    async def finish_review(self, admin_user_id: int, message_id: str, text: str) -> None:
        try:
            await self.bot.edit_message_text(chat_id=admin_user_id, message_id=int(message_id), text=text, parse_mode="HTML")
        except Exception:
            await self.bot.send_message(chat_id=admin_user_id, text=text, parse_mode="HTML")

    async def answer_callback(self, callback_id: str, text: str, show_alert: bool = False) -> None:
        await self.bot.answer_callback_query(callback_id, text=text, show_alert=show_alert)

    async def get_updates(self, offset: int | None = None):
        return await self.bot.get_updates(offset=offset, timeout=25, allowed_updates=["callback_query"])

    async def close(self) -> None:
        await self.bot.shutdown()

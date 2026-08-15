from __future__ import annotations

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

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


class TelegramPublisher:
    def __init__(self, token: str, channel_id: str):
        self.bot = Bot(token=token)
        self.channel_id = channel_id

    async def publish(self, decision: EditorialDecision, sources: list[str]) -> str:
        message = await self.bot.send_message(chat_id=self.channel_id, text=render(decision, sources), parse_mode="HTML", disable_web_page_preview=True)
        return str(message.message_id)

    async def send_review(self, decision: EditorialDecision, story_key: str, sources: list[str], admin_user_id: int) -> str:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Опубликовать", callback_data=f"news:approve:{story_key}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"news:reject:{story_key}"),
             InlineKeyboardButton("✏️ Переписать", callback_data=f"news:regenerate:{story_key}")],
        ])
        message = await self.bot.send_message(
            chat_id=admin_user_id,
            text=render(decision, sources, review=True),
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
        return str(message.message_id)

    async def update_review(self, message_id: str, decision: EditorialDecision, sources: list[str], story_key: str) -> None:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Опубликовать", callback_data=f"news:approve:{story_key}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"news:reject:{story_key}"),
             InlineKeyboardButton("✏️ Переписать", callback_data=f"news:regenerate:{story_key}")],
        ])
        await self.bot.edit_message_text(
            chat_id=message_id.split(":", 1)[0] if ":" in message_id else None,
            message_id=int(message_id.split(":")[-1]),
            text=render(decision, sources, review=True),
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )

    async def answer_callback(self, callback_id: str, text: str, show_alert: bool = False) -> None:
        await self.bot.answer_callback_query(callback_id, text=text, show_alert=show_alert)

    async def close(self) -> None:
        await self.bot.shutdown()

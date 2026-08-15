from __future__ import annotations

import asyncio

from telegram import Bot

from .models import EditorialDecision


def render(decision: EditorialDecision, sources: list[str]) -> str:
    marker = "🔴 СРОЧНО" if decision.priority >= 85 else ("🟡 ТРЕБУЕТ ПОДТВЕРЖДЕНИЯ" if decision.status == "unconfirmed" else "🇺🇿 НОВОСТИ")
    source_text = "\n".join(f"• {url}" for url in sources[:4])
    return (f"{marker}\n\n<b>{decision.ru_title}</b>\n{decision.ru_body}\n\n"
            f"🇺🇿 <b>{decision.uz_title}</b>\n{decision.uz_body}\n\n"
            f"📌 Источники / Manbalar:\n{source_text}\n\n"
            f"🇺🇿 Узбекистан слушает")


class TelegramPublisher:
    def __init__(self, token: str, channel_id: str):
        self.bot = Bot(token=token)
        self.channel_id = channel_id

    async def publish(self, decision: EditorialDecision, sources: list[str]) -> str:
        message = await self.bot.send_message(chat_id=self.channel_id, text=render(decision, sources), parse_mode="HTML", disable_web_page_preview=True)
        return str(message.message_id)

    async def update(self, message_id: str, decision: EditorialDecision, sources: list[str]) -> None:
        await self.bot.edit_message_text(chat_id=self.channel_id, message_id=int(message_id), text=render(decision, sources), parse_mode="HTML", disable_web_page_preview=True)

    async def close(self) -> None:
        await self.bot.shutdown()

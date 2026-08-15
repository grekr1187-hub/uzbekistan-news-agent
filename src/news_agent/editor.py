from __future__ import annotations

import json
from dataclasses import asdict

from openai import AsyncOpenAI

from .models import EditorialDecision, Story

SYSTEM = """You are the senior editor of a Uzbekistan news Telegram channel. Never invent facts. Use only supplied source material. Do not copy source wording. Return JSON only with keys: status, confidence, priority, reason, ru_title, ru_body, uz_title, uz_body. status must be publish, unconfirmed, or reject. Confidence is 0..1. Priority is 1..100. Breaking events get higher priority. If the supplied evidence is insufficient, choose unconfirmed or reject. Every body must be concise, factual, and include no unsupported details."""


class AIEditor:
    def __init__(self, api_key: str, model: str = "gpt-5.4-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def evaluate_and_write(self, story: Story, corroborating_items: list[Story]) -> EditorialDecision:
        evidence = [{"source": story.source, "url": story.url, "title": story.title, "summary": story.summary}]
        evidence.extend({"source": x.source, "url": x.url, "title": x.title, "summary": x.summary} for x in corroborating_items[:4])
        prompt = json.dumps({"story": asdict(story), "evidence": evidence}, ensure_ascii=False)
        response = await self.client.responses.create(
            model=self.model,
            instructions=SYSTEM,
            input=prompt,
        )
        data = json.loads(response.output_text)
        required = ("status", "confidence", "priority", "reason", "ru_title", "ru_body", "uz_title", "uz_body")
        if any(key not in data for key in required) or data["status"] not in {"publish", "unconfirmed", "reject"}:
            raise ValueError("Invalid editorial decision")
        return EditorialDecision(
            status=data["status"], confidence=float(data["confidence"]), priority=int(data["priority"]),
            reason=str(data["reason"]), ru_title=str(data["ru_title"]), ru_body=str(data["ru_body"]),
            uz_title=str(data["uz_title"]), uz_body=str(data["uz_body"]),
        )

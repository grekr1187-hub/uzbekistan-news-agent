from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawItem:
    title: str
    url: str
    source: str
    published_at: datetime | None
    summary: str


@dataclass
class Story:
    title: str
    url: str
    source: str
    published_at: datetime | None
    summary: str
    confidence: float = 0.0
    status: str = "new"
    telegram_message_id: str | None = None


@dataclass
class EditorialDecision:
    status: str
    confidence: float
    priority: int
    reason: str
    ru_title: str
    ru_body: str
    uz_title: str
    uz_body: str

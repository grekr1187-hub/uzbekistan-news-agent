from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Story


class StoryStore:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            published_at TEXT,
            summary TEXT,
            confidence REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'new',
            telegram_message_id TEXT
        )""")
        self.conn.commit()

    def upsert_story(self, story: Story) -> bool:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO stories(url,title,source,published_at,summary,confidence,status) VALUES(?,?,?,?,?,?,?)",
            (story.url, story.title, story.source, story.published_at.isoformat() if story.published_at else None,
             story.summary, story.confidence, story.status),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def mark_published(self, story_url: str, message_id: str) -> None:
        self.conn.execute("UPDATE stories SET status='published', telegram_message_id=? WHERE url=?", (message_id, story_url))
        self.conn.commit()

    def mark_status(self, story_url: str, status: str) -> None:
        self.conn.execute("UPDATE stories SET status=? WHERE url=?", (status, story_url))
        self.conn.commit()

    def find_recent_titles(self, limit: int = 100) -> list[str]:
        rows = self.conn.execute("SELECT title FROM stories ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [r[0] for r in rows]

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from .models import ReviewStatus, Story


def make_review_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


class StoryStore:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            published_at TEXT,
            summary TEXT,
            confidence REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'new',
            telegram_message_id TEXT,
            review_key TEXT UNIQUE,
            review_message_id TEXT,
            review_status TEXT NOT NULL DEFAULT 'pending'
        )""")
        self._ensure_columns()
        self.conn.commit()

    def _ensure_columns(self) -> None:
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(stories)")}
        if "review_key" not in columns:
            self.conn.execute("ALTER TABLE stories ADD COLUMN review_key TEXT")
        if "review_message_id" not in columns:
            self.conn.execute("ALTER TABLE stories ADD COLUMN review_message_id TEXT")
        if "review_status" not in columns:
            self.conn.execute("ALTER TABLE stories ADD COLUMN review_status TEXT NOT NULL DEFAULT 'pending'")

    def upsert_story(self, story: Story) -> bool:
        key = story.review_key or make_review_key(story.url)
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO stories(url,title,source,published_at,summary,confidence,status,review_key,review_status) VALUES(?,?,?,?,?,?,?,?,?)",
            (story.url, story.title, story.source, story.published_at.isoformat() if story.published_at else None,
             story.summary, story.confidence, story.status, key, story.review_status),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def _row_to_story(self, row: sqlite3.Row | None) -> Story | None:
        if row is None:
            return None
        from datetime import datetime
        published = datetime.fromisoformat(row["published_at"]) if row["published_at"] else None
        return Story(
            title=row["title"], url=row["url"], source=row["source"], published_at=published,
            summary=row["summary"] or "", confidence=row["confidence"], status=row["status"],
            telegram_message_id=row["telegram_message_id"], review_key=row["review_key"],
            review_message_id=row["review_message_id"], review_status=row["review_status"] or "pending",
        )

    def get_by_review_key(self, key: str) -> Story | None:
        return self._row_to_story(self.conn.execute("SELECT * FROM stories WHERE review_key=?", (key,)).fetchone())

    def set_review_message(self, story_url: str, message_id: str) -> None:
        self.conn.execute("UPDATE stories SET review_message_id=?, review_status='pending' WHERE url=?", (message_id, story_url))
        self.conn.commit()

    def set_review_status(self, story_url: str, status: ReviewStatus) -> None:
        self.conn.execute("UPDATE stories SET review_status=? WHERE url=?", (status, story_url))
        self.conn.commit()

    def mark_published(self, story_url: str, message_id: str) -> None:
        self.conn.execute("UPDATE stories SET status='published', telegram_message_id=?, review_status='published' WHERE url=?", (message_id, story_url))
        self.conn.commit()

    def mark_status(self, story_url: str, status: str) -> None:
        self.conn.execute("UPDATE stories SET status=? WHERE url=?", (status, story_url))
        self.conn.commit()

    def find_recent_titles(self, limit: int = 100) -> list[str]:
        rows = self.conn.execute("SELECT title FROM stories ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [r[0] for r in rows]

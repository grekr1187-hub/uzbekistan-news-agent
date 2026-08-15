# Uzbekistan News Agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a continuously running Railway worker that collects Uzbekistan news, deduplicates and classifies it, creates concise RU/UZ posts with OpenAI, and publishes/updates them in Telegram.

**Architecture:** Python worker with focused collector, normalization, scoring/editor, persistence, and Telegram publisher modules. SQLite is used for the MVP to keep deployment simple; all state needed for idempotency survives restarts. The worker polls sources on a bounded interval and prioritizes breaking items.

**Tech Stack:** Python 3.12, asyncio, httpx, feedparser, BeautifulSoup4, OpenAI SDK, python-telegram-bot, SQLite, pytest, Railway.

## Global Constraints

- Every published story has Russian and Uzbek copy.
- Social/Telegram posts are leads, not sole confirmation for factual claims.
- Important stories should be corroborated by an independent source where practical.
- Unconfirmed but credible breaking reports are explicitly labeled and monitored for confirmation.
- Source articles are never reproduced verbatim.
- Duplicate and low-value stories are suppressed.
- Secrets are only environment variables and never committed.
- Source/API failures are isolated; retries use bounded exponential backoff.

---

### Task 1: Application skeleton and configuration

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/news_agent/__init__.py`
- Create: `src/news_agent/config.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces `Settings` with `openai_api_key`, `telegram_bot_token`, `telegram_channel_id`, `poll_interval_seconds`, and `database_path`.

- [ ] **Step 1: Write the failing configuration test**

```python
from news_agent.config import Settings

def test_settings_reads_required_values(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-telegram")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@test_channel")
    settings = Settings.from_env()
    assert settings.openai_api_key == "test-openai"
    assert settings.telegram_channel_id == "@test_channel"
```

- [ ] **Step 2: Run test and verify failure**

Run: `pytest tests/test_config.py -v`
Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement configuration and project metadata**

`Settings.from_env()` must require the three secret/channel variables and default `POLL_INTERVAL_SECONDS=300` and `DATABASE_PATH=data/news.db`. Raise `ValueError` naming any missing required variable.

- [ ] **Step 4: Run test**

Run: `pytest tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore .env.example src/news_agent tests/test_config.py
git commit -m "chore: scaffold news agent configuration"
```

### Task 2: Persistent story store and deduplication

**Files:**
- Create: `src/news_agent/models.py`
- Create: `src/news_agent/store.py`
- Create: `src/news_agent/dedupe.py`
- Create: `tests/test_store.py`
- Create: `tests/test_dedupe.py`

**Interfaces:**
- `Story(id, title, url, source, published_at, summary, confidence, status, telegram_message_id)` dataclass.
- `StoryStore.upsert_story(story) -> bool` returns whether the story was newly inserted.
- `StoryStore.mark_published(story_id, telegram_message_id) -> None`.
- `StoryStore.find_recent_titles(hours: int) -> list[str]`.
- `is_duplicate(title, url, recent_titles) -> bool` normalizes URLs and compares normalized token overlap.

- [ ] **Step 1: Write failing tests for idempotent storage and duplicates.**
- [ ] **Step 2: Run `pytest tests/test_store.py tests/test_dedupe.py -v` and verify failure.**
- [ ] **Step 3: Implement SQLite schema and deterministic duplicate checks.**
- [ ] **Step 4: Run the targeted tests and verify PASS.**
- [ ] **Step 5: Commit `feat: add persistent story store and dedupe`.**

### Task 3: Source collection and normalization

**Files:**
- Create: `src/news_agent/sources.py`
- Create: `src/news_agent/collector.py`
- Create: `tests/test_collector.py`

**Interfaces:**
- `Source(name: str, url: str, kind: str)` dataclass.
- `SourceCollector.fetch(source) -> list[RawItem]`.
- `normalize_item(raw) -> Story`.
- `DEFAULT_SOURCES` contains configured RSS/Atom feeds and source endpoints that are publicly accessible; source failures are caught per source.

- [ ] **Step 1: Write tests using local fixture XML/HTML for title, URL, timestamp and summary extraction.**
- [ ] **Step 2: Run targeted collector tests and verify failure.**
- [ ] **Step 3: Implement async HTTP fetching with timeouts, user-agent, feed parsing and normalization.**
- [ ] **Step 4: Add per-source exception isolation and structured logging.**
- [ ] **Step 5: Run `pytest tests/test_collector.py -v` and verify PASS.**
- [ ] **Step 6: Commit `feat: add news source collection`.**

### Task 4: Reliability classification and bilingual AI editing

**Files:**
- Create: `src/news_agent/editor.py`
- Create: `tests/test_editor.py`

**Interfaces:**
- `EditorialDecision(status: Literal["publish","unconfirmed","reject"], confidence: float, priority: int, reason: str, ru_title: str, ru_body: str, uz_title: str, uz_body: str)`.
- `AIEditor.evaluate_and_write(story, corroborating_items) -> EditorialDecision`.

- [ ] **Step 1: Write tests against a mocked OpenAI client verifying JSON parsing and rejection of malformed model output.**
- [ ] **Step 2: Run targeted tests and verify failure.**
- [ ] **Step 3: Implement a strict structured prompt requiring factual grounding, source attribution, RU/UZ copy, status, confidence and priority.**
- [ ] **Step 4: Implement schema validation and safe fallback to `reject` on invalid output.**
- [ ] **Step 5: Run tests and verify PASS.**
- [ ] **Step 6: Commit `feat: add bilingual AI editorial engine`.**

### Task 5: Telegram publisher and update flow

**Files:**
- Create: `src/news_agent/telegram.py`
- Create: `tests/test_telegram.py`

**Interfaces:**
- `TelegramPublisher.publish(decision, source_urls) -> str` returns Telegram message ID.
- `TelegramPublisher.update(message_id, decision, source_urls) -> None`.

- [ ] **Step 1: Write mocked Telegram API tests for publish and update, including idempotent retry behavior.**
- [ ] **Step 2: Run targeted tests and verify failure.**
- [ ] **Step 3: Implement formatted RU/UZ posts with status labels and source links.**
- [ ] **Step 4: Implement retries with exponential backoff for transient Telegram failures.**
- [ ] **Step 5: Run tests and verify PASS.**
- [ ] **Step 6: Commit `feat: add telegram publishing`.**

### Task 6: Worker orchestration

**Files:**
- Create: `src/news_agent/worker.py`
- Create: `src/news_agent/main.py`
- Create: `tests/test_worker.py`

**Interfaces:**
- `NewsWorker.run_once() -> int` processes one collection cycle and returns publication count.
- `NewsWorker.run_forever() -> None` repeats with configured polling interval.

- [ ] **Step 1: Write orchestration tests with fake collector/editor/publisher/store.**
- [ ] **Step 2: Verify failure.**
- [ ] **Step 3: Implement flow: collect → dedupe → gather corroboration → classify/write → publish/update → persist.**
- [ ] **Step 4: Ensure one story's failure cannot terminate the cycle and that priorities are processed highest first.**
- [ ] **Step 5: Run full test suite `pytest -q` and verify PASS.**
- [ ] **Step 6: Commit `feat: orchestrate news agent worker`.**

### Task 7: Railway deployment configuration

**Files:**
- Create: `Dockerfile`
- Create: `railway.toml`
- Modify: `.env.example`
- Create: `tests/test_startup.py`

**Interfaces:**
- Container starts with `python -m news_agent.main`.

- [ ] **Step 1: Write a startup smoke test that imports the package and verifies required configuration errors are explicit.**
- [ ] **Step 2: Run test and verify failure until the final package is importable.**
- [ ] **Step 3: Add Python 3.12 Docker image, dependency installation, persistent `/data` path and worker command.**
- [ ] **Step 4: Run `pytest -q` and build the Docker image locally.**
- [ ] **Step 5: Commit `chore: add Railway deployment configuration`.**

### Task 8: Production variables and Telegram smoke test

**Files:**
- Modify: `.env.example` only if a discovered runtime variable needs documenting.

- [ ] **Step 1: Create a dedicated Railway project/service from this GitHub repository.**
- [ ] **Step 2: Add `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHANNEL_ID` to Railway Variables without committing their values.**
- [ ] **Step 3: Deploy and inspect logs for a successful startup.**
- [ ] **Step 4: Run a controlled single-cycle smoke test that publishes one real test post to the channel.**
- [ ] **Step 5: Confirm the Telegram message ID is persisted and restart the service to verify no duplicate publication.**
- [ ] **Step 6: Commit any required deployment-only documentation changes.**

### Task 9: Production verification and monitoring baseline

**Files:**
- Modify: `README.md`
- Create: `docs/operations.md`

- [ ] **Step 1: Document source policy, environment variables, startup, logs, and safe secret rotation.**
- [ ] **Step 2: Run `pytest -q` and record the passing suite.**
- [ ] **Step 3: Verify Railway deployment status is healthy and no crash loop is present.**
- [ ] **Step 4: Verify one normal story and one unconfirmed/confirmation update path in a controlled test.**
- [ ] **Step 5: Commit `docs: document production operations`.**

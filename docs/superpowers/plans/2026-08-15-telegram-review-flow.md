# Telegram Review Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Telegram editorial inbox where AI-prepared RU/UZ news drafts are sent to the owner for approval before publication.

**Architecture:** The worker keeps collecting and editing news, but the publisher becomes a two-stage workflow: create draft -> send review message to the configured admin chat -> wait for an inline-button callback -> publish, reject, or regenerate. Draft state and Telegram IDs are persisted so restarts do not lose pending approvals.

**Tech Stack:** Python 3.12, asyncio, httpx, OpenAI SDK, python-telegram-bot, SQLite, pytest, Railway.

## Global Constraints

- No story is published without explicit approval.
- Approval UI is Telegram inline buttons.
- Every draft contains Russian and Uzbek text and source attribution.
- Rejecting a draft must prevent publication.
- Regenerate must produce a fresh AI draft while preserving the source story.
- Telegram/OpenAI secrets remain environment variables and never enter GitHub.
- Callback handling must be idempotent so repeated taps cannot create duplicate posts.

---

### Task 1: Persist draft/review state

**Files:**
- Modify: `src/news_agent/models.py`
- Modify: `src/news_agent/store.py`
- Create: `tests/test_review_store.py`

**Interfaces:**
- `ReviewStatus = Literal["pending", "approved", "rejected", "published"]`.
- `Story.review_status: ReviewStatus`.
- `Story.review_message_id: str | None`.
- `StoryStore.set_review_message(story_id: str, telegram_message_id: str) -> None`.
- `StoryStore.set_review_status(story_id: str, status: ReviewStatus) -> None`.
- `StoryStore.get_by_id(story_id: str) -> Story | None`.

- [ ] Write tests proving pending state survives reopening SQLite and approved/rejected transitions are idempotent.
- [ ] Run `pytest tests/test_review_store.py -v` and verify failure before implementation.
- [ ] Add schema migration-safe columns with defaults.
- [ ] Run the targeted tests and verify PASS.
- [ ] Commit `feat: persist telegram review state`.

### Task 2: Telegram review inbox

**Files:**
- Modify: `src/news_agent/telegram.py`
- Create: `tests/test_review_telegram.py`

**Interfaces:**
- `TelegramPublisher.send_review(draft: EditorialDecision, story_id: str, source_urls: list[str]) -> str`.
- `TelegramPublisher.publish_approved(draft: EditorialDecision, source_urls: list[str]) -> str`.
- `TelegramPublisher.update_review(message_id: str, text: str, keyboard) -> None`.
- Callback data format: `news:approve:<story_id>`, `news:reject:<story_id>`, `news:regenerate:<story_id>`.

- [ ] Write mocked Telegram API tests for review message formatting and all three callback payloads.
- [ ] Run targeted tests and verify failure.
- [ ] Implement inline keyboard with `✅ Опубликовать`, `❌ Отклонить`, `✏️ Переписать`.
- [ ] Ensure source links and confidence/status are visible in the review message.
- [ ] Run tests and verify PASS.
- [ ] Commit `feat: add telegram editorial inbox`.

### Task 3: Callback handler and approval workflow

**Files:**
- Modify: `src/news_agent/telegram.py`
- Modify: `src/news_agent/worker.py`
- Create: `tests/test_review_callbacks.py`

**Interfaces:**
- `ReviewController.handle_callback(callback_data: str, user_id: int) -> None`.
- `NewsWorker.handle_review_action(action: str, story_id: str, user_id: int) -> None`.

- [ ] Write tests for unauthorized users, approve, reject, regenerate, duplicate approve, and approve-after-reject.
- [ ] Run targeted tests and verify failure.
- [ ] Implement an `TELEGRAM_ADMIN_USER_ID` allowlist; all other callback users receive no state change.
- [ ] On approve, atomically transition pending -> approved before publishing, then approved -> published after Telegram success; on transient failure keep approved state for retry.
- [ ] On reject, transition pending -> rejected and disable the keyboard.
- [ ] On regenerate, keep the source story pending and replace the review text with a new AI result.
- [ ] Run tests and verify PASS.
- [ ] Commit `feat: implement review approval callbacks`.

### Task 4: Worker integration

**Files:**
- Modify: `src/news_agent/worker.py`
- Modify: `src/news_agent/main.py`
- Create: `tests/test_review_worker.py`

- [ ] Write an integration-style test proving a new story creates a pending review rather than publishing directly.
- [ ] Run test and verify failure.
- [ ] Connect the review inbox to the Telegram polling/application loop while retaining the periodic news collection loop.
- [ ] Ensure startup recovers pending reviews from SQLite without re-sending duplicates.
- [ ] Run `pytest -q` and verify PASS.
- [ ] Commit `feat: route news through manual approval`.

### Task 5: Configuration and deployment

**Files:**
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/operations.md`

- [ ] Document `TELEGRAM_ADMIN_USER_ID` and the approval flow.
- [ ] Add a safe startup error when the admin ID is missing in review mode.
- [ ] Run `pytest -q` and verify PASS.
- [ ] Deploy to Railway with `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID`, and `TELEGRAM_ADMIN_USER_ID` set as secrets.
- [ ] Verify the worker starts and receives Telegram updates.
- [ ] Perform one controlled end-to-end test: draft -> review message -> approve -> channel post.
- [ ] Verify duplicate approval does not create a second channel post.
- [ ] Commit `docs: document manual Telegram approval flow`.

# Uzbekistan News Agent — MVP Design

## Goal
Build a Railway-hosted news agent for the Telegram channel “Узбекистан слушает”. The agent continuously discovers relevant Uzbekistan news, evaluates reliability and duplication, writes original bilingual posts (Russian + Uzbek), and publishes approved items to Telegram.

## Editorial policy
- Sources: official government/agency sources, established Uzbekistan media, relevant international media.
- Social/Telegram posts may be used as leads, not sole confirmation for factual claims.
- Important stories should be corroborated by an independent source where practical.
- Unconfirmed but credible breaking reports may be published with an explicit “requires confirmation” label and monitored for later confirmation.
- Never present rumors as established facts.
- Do not reproduce source articles verbatim; generate concise original summaries with source attribution.

## Publishing behavior
- Continuous monitoring.
- Breaking/high-priority items publish immediately.
- Routine items publish when editorial value is sufficient.
- Agent determines volume dynamically and suppresses duplicates/low-value items.
- Every post contains Russian and Uzbek versions.
- Existing Telegram posts can be updated when an unconfirmed report becomes confirmed.

## Architecture
1. News collectors gather RSS/API/web source items.
2. Normalizer extracts title, URL, timestamp, source, text/summary and metadata.
3. Deduplication checks canonical URLs and semantic similarity against stored items.
4. Fact/reliability classifier assigns confidence and publication status.
5. AI editor produces structured RU/UZ copy and source attribution.
6. Telegram publisher sends/updates channel posts.
7. Persistent database stores source items, normalized stories, publication state, hashes, timestamps and Telegram message IDs.
8. Scheduler/worker runs continuously on Railway with retry/backoff and structured logs.

## MVP boundaries
Included: collection, normalization, deduplication, confidence classification, bilingual editing, Telegram publication/update, persistence, retries/logging, configuration through environment variables.

Excluded from MVP: automated video generation, advertising workflow, public admin dashboard, advanced analytics. These will be separate later modules.

## Secrets
- TELEGRAM_BOT_TOKEN: Railway secret variable.
- TELEGRAM_CHANNEL_ID or configured channel username: Railway variable.
- OPENAI_API_KEY: dedicated key for this project, stored only in Railway.

No secrets are committed to GitHub.

## Reliability and failure handling
- Source failures are isolated; one unavailable source must not stop the worker.
- AI/API failures use bounded retries with exponential backoff.
- Telegram failures are retried without creating duplicate posts where possible.
- Database operations are idempotent.
- Logs include story/source IDs and error categories, but never secret values.

## Success criteria
- Agent can run continuously on Railway.
- New relevant stories are detected without repeated publication.
- Posts are bilingual RU/UZ and cite their source(s).
- Breaking stories receive higher priority.
- Unconfirmed stories are clearly labeled and can be updated after confirmation.
- Restarting the service does not lose publication history or create routine duplicates.

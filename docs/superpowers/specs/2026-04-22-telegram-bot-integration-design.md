# Telegram Bot API Integration — Design Spec

**Date:** 2026-04-22
**Status:** Approved

## Goal

Add real Telegram Bot integration to the JobCRM app so that when a user forwards job postings to the Telegram bot in a private chat, they automatically appear as new jobs in the CRM.

## Architecture

Single Python process combining FastAPI + python-telegram-bot:

```
Telegram User Chat ──forward job posts──► Bot (polling, asyncio task)
                                              │ parseTelegramMessage()
                                              ▼
                                        SQLite (jobs.db)
                                        + resumes/ dir
                                              ▲
                                              │ REST API
                                        FastAPI (:8000)
                                        serves index.html + /api/*
                                              ▲
                                              │ fetch() + polling
                                        Browser (index.html)
```

**Startup:** `python main.py` initializes SQLite, starts Telegram bot polling as a background asyncio task, and starts the FastAPI server on port 8000.

**Message flow:**
1. User forwards a job post to the bot in Telegram
2. Bot handler calls `parseTelegramMessage()` (Python port)
3. Parsed job inserted into SQLite with status `New`
4. Frontend polls `GET /api/jobs?since_id=<last_id>` every 10s
5. New jobs appear with a toast notification

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serve index.html |
| GET | `/api/jobs` | List jobs (filters: `status`, `search`, `sort`, `since_id`) |
| GET | `/api/jobs/:id` | Get single job |
| POST | `/api/jobs` | Create job (manual add from inbox) |
| PUT | `/api/jobs/:id` | Update job |
| DELETE | `/api/jobs/:id` | Delete job |
| POST | `/api/jobs/:id/resume` | Upload resume (multipart/form-data, max 5MB, .pdf/.doc/.docx) |
| DELETE | `/api/jobs/:id/resume` | Remove resume |
| GET | `/api/jobs/:id/resume` | Download resume |
| POST | `/api/jobs/:id/ai-summary` | Generate AI summary |
| POST | `/api/jobs/:id/ai-fit` | Run fit analysis |
| GET | `/api/settings` | Get settings |
| PUT | `/api/settings` | Update settings |
| POST | `/api/import` | Bulk import jobs from JSON |
| GET | `/api/export` | Export all data as JSON |

All responses are JSON. Errors return `{"detail": "..."}` with appropriate HTTP status codes (422 for bad input, 404 for missing, 500 for server errors).

## SQLite Schema

### `jobs` table

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | UUID |
| raw_message | TEXT | Full Telegram text |
| role_title | TEXT | Parsed role |
| company_name | TEXT | Parsed company |
| location | TEXT | Parsed location |
| salary | TEXT | Parsed salary |
| job_type | TEXT | Parsed type |
| apply_link | TEXT | Apply URL |
| source | TEXT | Default "Telegram" |
| status | TEXT | New, Reviewing, Will Apply, Applied, Interviewing, Offer, Rejected |
| fit_score | INTEGER | 0–5 |
| interest_score | INTEGER | 0–5 |
| priority_score | INTEGER | fit × interest |
| date_received | TEXT | ISO 8601 |
| date_reviewed | TEXT | ISO 8601, nullable |
| date_applied | TEXT | ISO 8601, nullable |
| resume_path | TEXT | File path on disk, nullable |
| resume_version_name | TEXT | |
| cover_letter | TEXT | |
| notes | TEXT | |
| response_received | TEXT | "yes" / "no" |
| stage_reached | TEXT | No Response, Screening, Interview, Final Round |
| rejection_reason | TEXT | |
| ai_summary | TEXT | JSON array |
| ai_requirements | TEXT | JSON array |
| ai_fit | TEXT | JSON object |

### `settings` table

| Column | Type | Notes |
|--------|------|-------|
| key | TEXT PK | |
| value | TEXT | |

## Enhanced Telegram Parser

Real messages from crypto/Web3 job channels have emoji-prefixed fields and channel footer noise.

**Parsing strategy (in priority order):**

1. **Noise stripping:** Remove everything from `📌 New here?`, `⚠️ DYOR`, `❗️ I'm not hiring` to end of message
2. **Emoji-based field extraction:** Scan for emoji prefixes:
   - `💼 Hiring:` → role + company
   - `📍` → location
   - `💰` → salary
   - `🧑‍💻` → job type
   - `🔑 Requirements:` → requirements section
   - `📩 To apply:` → apply link
   - `💡 Perks & Benefits:` → benefits section
3. **First-line role parsing (fallback):** Strip emojis, split on ` - `, ` at `, ` | `
4. **Apply link:** Take URL after `📩 To apply:` or first URL near "apply" keyword — not LinkedIn "original post" or channel promo links
5. **Regex fallback:** Salary (`$X–$Y`), URLs, job type keywords as in current JS parser

## Frontend Changes

- Replace all `localStorage` calls with `fetch()` to REST API
- Add polling: every 10s, `GET /api/jobs?since_id=<last_seen_id>` to detect new Telegram jobs
- Show toast "New job from Telegram!" on new job arrival
- Resume upload via `POST /api/jobs/:id/resume` instead of localStorage base64
- Manual "paste & parse" inbox flow stays, but posts to `POST /api/jobs`
- Remove placeholder Python snippet from inbox page
- Show "Server disconnected" banner when API unreachable, auto-retry polling

## Configuration

- `.env` file: `TELEGRAM_BOT_TOKEN`, `PORT` (default 8000)
- `requirements.txt`: `fastapi`, `uvicorn`, `python-telegram-bot`, `python-dotenv`, `aiosqlite`

## Error Handling

- Invalid bot token: log error and exit with clear message
- Bot polling: auto-reconnect on network errors (built into python-telegram-bot)
- API: 422 for bad input, 404 for missing jobs, 500 with detail for server errors
- Frontend: "Server disconnected" banner with auto-retry when API unreachable

## Security

- Bot token in `.env`, never exposed to frontend
- No auth on API (local personal tool on localhost)
- CORS: same-origin only (frontend served by same FastAPI process)
- Resume uploads: max 5MB, `.pdf`/`.doc`/`.docx` only

## File Structure

```
Job Application CRM/
├── main.py              # FastAPI app + bot startup
├── bot.py               # Telegram bot handler + parser
├── database.py          # SQLite operations
├── parser.py            # parseTelegramMessage() + enhanced emoji parsing
├── ai.py                # Summary + fit analysis (ported from JS)
├── requirements.txt
├── .env                 # TELEGRAM_BOT_TOKEN, PORT
├── index.html           # Frontend (modified to use API)
├── resumes/             # Uploaded resume files
└── jobs.db              # SQLite database (created at runtime)
```

# Telegram Bot API Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real Telegram Bot integration so forwarded job posts automatically appear in the CRM via a Python backend with SQLite.

**Architecture:** Single Python process (FastAPI + python-telegram-bot). FastAPI serves the frontend and REST API. The Telegram bot polls for messages in a background asyncio task. All data lives in SQLite. Frontend fetches from the API instead of localStorage.

**Tech Stack:** Python 3.10+, FastAPI, uvicorn, python-telegram-bot, aiosqlite, python-dotenv

---

## File Structure

```
Job Application CRM/
├── main.py              # FastAPI app factory + startup (serves HTML, mounts API, starts bot)
├── bot.py               # Telegram bot handler, calls parser on incoming messages
├── database.py          # All SQLite operations (init, CRUD, settings)
├── parser.py            # parseTelegramMessage() with emoji-based + fallback parsing
├── ai.py                # Summary generation + fit analysis (ported from JS)
├── requirements.txt     # Python dependencies
├── .env                 # TELEGRAM_BOT_TOKEN, PORT
├── .gitignore           # Ignore .env, jobs.db, resumes/, __pycache__
├── index.html           # Frontend (modified: API calls replace localStorage)
├── resumes/             # Uploaded resume files (created at runtime)
└── jobs.db              # SQLite database (created at runtime)
```

---

### Task 1: Project scaffolding and dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-telegram-bot==21.5
python-dotenv==1.0.1
aiosqlite==0.20.0
```

- [ ] **Step 2: Create .env**

```
TELEGRAM_BOT_TOKEN=8788238697:AAFy-x0DmWx0UjVa44kKnrwwJZ3GoBIrpTk
PORT=8000
```

- [ ] **Step 3: Create .gitignore**

```
.env
jobs.db
resumes/
__pycache__/
*.pyc
```

- [ ] **Step 4: Install dependencies**

Run: `cd "/Users/mehran/Documents/Codes/Job Application CRM" && pip install -r requirements.txt`
Expected: All packages install successfully

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore
git commit -m "feat: add project scaffolding and dependencies"
```

---

### Task 2: Database module

**Files:**
- Create: `database.py`

- [ ] **Step 1: Write database.py with SQLite init and all CRUD operations**

```python
import aiosqlite
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"
RESUMES_DIR = Path(__file__).parent / "resumes"

VALID_STATUSES = ["New", "Reviewing", "Will Apply", "Applied", "Interviewing", "Offer", "Rejected"]
VALID_STAGES = ["No Response", "Screening", "Interview", "Final Round"]

CREATE_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    raw_message TEXT DEFAULT '',
    role_title TEXT DEFAULT '',
    company_name TEXT DEFAULT '',
    location TEXT DEFAULT '',
    salary TEXT DEFAULT '',
    job_type TEXT DEFAULT '',
    apply_link TEXT DEFAULT '',
    source TEXT DEFAULT 'Telegram',
    status TEXT DEFAULT 'New',
    fit_score INTEGER DEFAULT 0,
    interest_score INTEGER DEFAULT 0,
    priority_score INTEGER DEFAULT 0,
    date_received TEXT NOT NULL,
    date_reviewed TEXT,
    date_applied TEXT,
    resume_path TEXT,
    resume_version_name TEXT DEFAULT '',
    cover_letter TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    response_received TEXT DEFAULT 'no',
    stage_reached TEXT DEFAULT 'No Response',
    rejection_reason TEXT DEFAULT '',
    ai_summary TEXT,
    ai_requirements TEXT,
    ai_fit TEXT
)
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
"""


async def init_db():
    RESUMES_DIR.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_JOBS_TABLE)
        await db.execute(CREATE_SETTINGS_TABLE)
        await db.commit()


async def get_jobs(status: str = None, search: str = None, sort: str = "date_desc", since_id: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []

        if status and status != "all":
            query += " AND status = ?"
            params.append(status)

        if search:
            query += " AND (role_title LIKE ? OR company_name LIKE ? OR location LIKE ? OR notes LIKE ? OR raw_message LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term, term, term])

        if since_id:
            query += " AND date_received > (SELECT date_received FROM jobs WHERE id = ?)"
            params.append(since_id)

        if sort == "date_asc":
            query += " ORDER BY date_received ASC"
        elif sort == "priority":
            query += " ORDER BY priority_score DESC"
        elif sort == "fit":
            query += " ORDER BY fit_score DESC"
        else:
            query += " ORDER BY date_received DESC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_job(job_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_job(job_data: dict) -> dict:
    if "id" not in job_data or not job_data["id"]:
        import time, random
        job_data["id"] = f"{int(time.time()):36}{random.randbytes(3).hex()}"

    if "date_received" not in job_data or not job_data["date_received"]:
        job_data["date_received"] = datetime.utcnow().isoformat() + "Z"

    job_data["priority_score"] = (job_data.get("fit_score", 0) or 0) * (job_data.get("interest_score", 0) or 0)

    fields = [k for k in job_data.keys() if k != "resume_file"]
    placeholders = ", ".join(["?"] * len(fields))
    columns = ", ".join(fields)
    values = []
    for f in fields:
        v = job_data[f]
        if isinstance(v, (dict, list)):
            v = json.dumps(v)
        elif v is None:
            v = None
        values.append(v)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"INSERT INTO jobs ({columns}) VALUES ({placeholders})", values)
        await db.commit()

    return await get_job(job_data["id"])


async def update_job(job_id: str, updates: dict) -> dict:
    if "fit_score" in updates or "interest_score" in updates:
        job = await get_job(job_id)
        if job:
            fit = updates.get("fit_score", job.get("fit_score", 0) or 0)
            interest = updates.get("interest_score", job.get("interest_score", 0) or 0)
            updates["priority_score"] = (fit or 0) * (interest or 0)

    set_clauses = []
    values = []
    for k, v in updates.items():
        if k == "id":
            continue
        if isinstance(v, (dict, list)):
            v = json.dumps(v)
        set_clauses.append(f"{k} = ?")
        values.append(v)

    values.append(job_id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = ?", values)
        await db.commit()

    return await get_job(job_id)


async def delete_job(job_id: str) -> bool:
    job = await get_job(job_id)
    if job and job.get("resume_path"):
        resume_file = Path(job["resume_path"])
        if resume_file.exists():
            resume_file.unlink()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        await db.commit()
        return cursor.rowcount > 0


async def get_setting(key: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else ""


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()


async def get_all_settings() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}


async def get_status_counts() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status")
        rows = await cursor.fetchall()
        return {row["status"]: row["count"] for row in rows}


async def import_jobs(jobs_data: list):
    async with aiosqlite.connect(DB_PATH) as db:
        for job in jobs_data:
            try:
                fields = [k for k in job.keys() if k not in ("resume_file",)]
                placeholders = ", ".join(["?"] * len(fields))
                columns = ", ".join(fields)
                values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in [job[f] for f in fields]]
                await db.execute(f"INSERT OR REPLACE INTO jobs ({columns}) VALUES ({placeholders})", values)
            except Exception:
                continue
        await db.commit()
```

- [ ] **Step 2: Verify module loads**

Run: `cd "/Users/mehran/Documents/Codes/Job Application CRM" && python -c "import database; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add database.py
git commit -m "feat: add database module with SQLite CRUD operations"
```

---

### Task 3: Enhanced Telegram parser

**Files:**
- Create: `parser.py`

- [ ] **Step 1: Write parser.py with emoji-based extraction + fallback heuristics + noise stripping**

```python
import re
from datetime import datetime


STOP_WORDS = set(
    "that this with from have will been they their about would could should which where when "
    "what your there being having doing some very just more also than then each every both most "
    "other such only same into over after before between through during without within along "
    "these those because since while although however therefore thus hence still already yet "
    "even much many well back then once here why how all any few nor not own too the and for "
    "are but not you who can had her its was our out day get has him his how its let may new now "
    "old put say she too use via a an i me my we he it of to in is on at by or as if no up do be am".split()
)

# Noise markers that signal the end of useful job content
NOISE_MARKERS = [
    "📌 New here?",
    "⚠️ DYOR",
    "❗️ I'm not hiring",
    "❗️ I'm not hiring myself",
    "🌎 My Web3 world",
    "💬 Want to collaborate",
]

# Emoji prefixes for structured field extraction
EMOJI_PATTERNS = {
    "hiring": re.compile(r"💼\s*Hiring:\s*(.+)", re.IGNORECASE),
    "location": re.compile(r"📍\s*(.+?)(?:\s*[\|│]\s*|$)", re.IGNORECASE),
    "salary": re.compile(r"💰\s*(.+?)(?:\s*[\|│]\s*|$)", re.IGNORECASE),
    "job_type": re.compile(r"🧑‍💻\s*(.+?)(?:\s*[\|│]\s*|$)", re.IGNORECASE),
    "requirements": re.compile(r"🔑\s*Requirements:\s*(.+?)(?=💡|📩|🔗|📌|⚠️|❗|$)", re.DOTALL | re.IGNORECASE),
    "apply": re.compile(r"📩\s*To apply:\s*(.+?)(?:\n|$)", re.IGNORECASE),
    "perks": re.compile(r"💡\s*Perks\s*&\s*Benefits:\s*(.+?)(?=📩|🔗|📌|⚠️|❗|$)", re.DOTALL | re.IGNORECASE),
    "original_post": re.compile(r"🔗\s*Original post:\s*(https?://[^\s]+)", re.IGNORECASE),
}

SALARY_RE = re.compile(r"\$[\d,.]+k?\s*[-–—to]+\s*\$?[\d,.]+k?", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s)\]>]+")
JOB_TYPE_PATTERNS = [
    (re.compile(r"\bfull[- ]?time\b", re.I), "Full-time"),
    (re.compile(r"\bpart[- ]?time\b", re.I), "Part-time"),
    (re.compile(r"\bcontract\b", re.I), "Contract"),
    (re.compile(r"\bfreelance\b", re.I), "Freelance"),
]

LOC_KW_RE = re.compile(r"(?:location|loc|based in|office|where)\s*[:\-–]\s*([^\n,;]{2,40})", re.I)


def _strip_noise(raw: str) -> str:
    """Remove channel footer noise from message."""
    for marker in NOISE_MARKERS:
        idx = raw.find(marker)
        if idx != -1:
            raw = raw[:idx]
    return raw.strip()


def _extract_emoji_fields(raw: str) -> dict:
    """Extract fields from emoji-prefixed lines."""
    result = {}
    for key, pattern in EMOJI_PATTERNS.items():
        m = pattern.search(raw)
        if m:
            result[key] = m.group(1).strip()
    return result


def _parse_first_line(line: str) -> tuple[str, str]:
    """Parse role and company from the first line of a message."""
    # Strip emojis, bold markers, leading symbols
    fl = re.sub(r"[\U0001F300-\U0001F9FF\U00002600-\U000026FF\U00002700-\U000027BF\U0000FE00-\U0000FE0F\U0001F000-\U0001FFFF]", "", line)
    fl = re.sub(r"\*{1,2}", "", fl)
    fl = re.sub(r"^[\s\-—–:•·▪▸►→]+", "", fl).strip()
    fl = re.sub(r"^(hiring|looking for|position):\s*", "", fl, flags=re.I).strip()

    seps = [(" at ", False), (" @ ", False), (" — ", True), (" – ", True), (" - ", True), (" | ", True), (": ", True)]
    for sep, swap in seps:
        if sep in fl:
            parts = [p.strip() for p in fl.split(sep)]
            if len(parts) >= 2:
                if not swap:
                    return parts[0], sep.join(parts[1:]).strip()
                else:
                    longer_first = len(parts[0]) >= len(parts[1])
                    role = parts[0] if longer_first else parts[1]
                    company = parts[1] if longer_first else parts[0]
                    return role, company
    return fl, ""


def parse_telegram_message(raw: str) -> dict:
    """Parse a raw Telegram message into structured job data."""
    cleaned = _strip_noise(raw)
    emoji_fields = _extract_emoji_fields(cleaned)
    lines = [l for l in cleaned.split("\n") if l.strip()]

    # --- Role + Company ---
    role_title = ""
    company_name = ""
    if "hiring" in emoji_fields:
        hiring_text = emoji_fields["hiring"]
        # "Copywriter - BoDoggos" or "Senior Engineer at Stripe"
        role_title, company_name = _parse_first_line(hiring_text)
    if not role_title and lines:
        role_title, company_name = _parse_first_line(lines[0])

    # --- Location ---
    location = ""
    if "location" in emoji_fields:
        loc_text = emoji_fields["location"]
        # Remove "Posted X hours ago" patterns from location line
        loc_text = re.sub(r"\s*[|│]\s*🕐.*$", "", loc_text).strip()
        # Remove "Posted..." patterns
        loc_text = re.sub(r"\s*Posted\s+.*$", "", loc_text, flags=re.I).strip()
        location = loc_text
    if not location:
        loc_match = LOC_KW_RE.search(cleaned)
        if loc_match:
            location = loc_match.group(1).strip()
    if not location:
        is_remote = re.search(r"\bremote\b", cleaned, re.I)
        is_hybrid = re.search(r"\bhybrid\b", cleaned, re.I)
        if is_remote:
            location = "Remote / Hybrid" if is_hybrid else "Remote"

    # --- Salary ---
    salary = ""
    if "salary" in emoji_fields:
        salary = emoji_fields["salary"].strip()
    if not salary:
        salary_match = SALARY_RE.search(cleaned)
        if salary_match:
            salary = salary_match.group(0)

    # --- Job Type ---
    job_type = ""
    if "job_type" in emoji_fields:
        job_type = emoji_fields["job_type"].strip()
    if not job_type:
        found_types = [val for pat, val in JOB_TYPE_PATTERNS if pat.search(cleaned)]
        job_type = ", ".join(dict.fromkeys(found_types))  # deduplicate preserving order

    # --- Apply Link ---
    apply_link = ""
    if "apply" in emoji_fields:
        apply_match = URL_RE.search(emoji_fields["apply"])
        if apply_match:
            apply_link = apply_match.group(0)
    if not apply_link:
        # Find URLs, prefer ones near "apply" keyword
        all_urls = URL_RE.findall(cleaned)
        if all_urls:
            # Take last URL (often the apply link), but exclude known non-apply patterns
            apply_link = all_urls[-1]
            # If the last URL is a linkedin "original post" or channel promo, try earlier ones
            non_apply_patterns = ["linkedin.com/posts/", "t.me/", "telegram.me/"]
            for url in reversed(all_urls):
                if not any(p in url for p in non_apply_patterns):
                    apply_link = url
                    break

    return {
        "raw_message": raw,
        "role_title": role_title,
        "company_name": company_name,
        "location": location,
        "salary": salary,
        "job_type": job_type,
        "apply_link": apply_link,
        "source": "Telegram",
        "status": "New",
        "fit_score": 0,
        "interest_score": 0,
        "priority_score": 0,
        "date_received": datetime.utcnow().isoformat() + "Z",
        "date_reviewed": None,
        "date_applied": None,
        "resume_path": None,
        "resume_version_name": "",
        "cover_letter": "",
        "notes": "",
        "response_received": "no",
        "stage_reached": "No Response",
        "rejection_reason": "",
        "ai_summary": None,
        "ai_requirements": None,
        "ai_fit": None,
    }
```

- [ ] **Step 2: Test parser with the real crypto/Web3 message**

Run: `cd "/Users/mehran/Documents/Codes/Job Application CRM" && python -c "
from parser import parse_telegram_message
msg = '''💼 Hiring: Copywriter - BoDoggos
📍 Remote (Global) | 🕐 Posted 4 hours ago - April 22, 2026 | 💰 \$2,000–\$3,000/month | 🧑‍💻 Part-Time / Contract

Nifty Metaverse Inc., a Miami-based media company in the crypto and Web3 space, produces podcasts, short-form video, and tweets. The company is seeking a skilled X/Twitter Ghostwriter to transform long-form content into high-performing posts that authentically match each creator voice.

🔑 Requirements:
- Deep immersion in Crypto Twitter culture, tone, memes, and inside jokes
- Proven ability to ghostwrite authentically in others voices without defaulting to own style
- Strong listening skills and editorial instincts to identify shareable content

💡 Perks & Benefits:
- \$2,000–\$3,000 per month based on experience and output
- Flexible part-time contract (~15–20 hours/week)
- Remote position with room to grow if performing well

📩 To apply: Send your X/Twitter handle (yours or one you have ghostwritten for), a short sample (3 tweets + 1 thread based on any recent crypto podcast clip or article showing voice capture), and a few direct sentences on why you are the right fit: https://cryptojobslist.com/jobs/copywriter-at-bodoggos

🔗 Original post: https://www.linkedin.com/posts/featured-opportunity-bodoggos-is-hiring-share-7452541360068386817-igbF

📌 New here? Subscribe and mute notifications to avoid noise.
⚠️ DYOR! I don't verify jobs.
❗️ I'm not hiring myself! I just sharing fresh real Web3 jobs daily.
'''
result = parse_telegram_message(msg)
print('role:', result['role_title'])
print('company:', result['company_name'])
print('location:', result['location'])
print('salary:', result['salary'])
print('type:', result['job_type'])
print('apply:', result['apply_link'])
assert result['role_title'] == 'Copywriter'
assert result['company_name'] == 'BoDoggos'
assert 'Remote' in result['location']
assert '2,000' in result['salary']
assert 'cryptojobslist.com' in result['apply_link']
assert 'linkedin.com' not in result['apply_link']
print('ALL TESTS PASSED')
"`
Expected: `ALL TESTS PASSED`

- [ ] **Step 3: Test parser fallback with a plain-format message**

Run: `cd "/Users/mehran/Documents/Codes/Job Application CRM" && python -c "
from parser import parse_telegram_message
msg = '''Senior Frontend Engineer at Stripe

We are looking for a Senior Frontend Engineer to join our Payments team.

Salary: \$180,000 – \$250,000
Location: Remote (US)
Type: Full-time

Apply: https://stripe.com/careers/senior-frontend-2024
'''
result = parse_telegram_message(msg)
print('role:', result['role_title'])
print('company:', result['company_name'])
print('salary:', result['salary'])
print('location:', result['location'])
assert result['role_title'] == 'Senior Frontend Engineer'
assert result['company_name'] == 'Stripe'
assert '180' in result['salary']
print('FALLBACK TESTS PASSED')
"`
Expected: `FALLBACK TESTS PASSED`

- [ ] **Step 4: Commit**

```bash
git add parser.py
git commit -m "feat: add enhanced Telegram parser with emoji extraction and noise stripping"
```

---

### Task 4: AI analysis module

**Files:**
- Create: `ai.py`

- [ ] **Step 1: Write ai.py porting the JS tokenize/generateSummary/analyzeFit logic**

```python
import re

STOP_WORDS = set(
    "that this with from have will been they their about would could should which where when "
    "what your there being having doing some very just more also than then each every both most "
    "other such only same into over after before between through during without within along "
    "these those because since while although however therefore thus hence still already yet "
    "even much many well back then once here why how all any few nor not own too the and for "
    "are but not you who can had her its was our out day get has him his how its let may new now "
    "old put say she too use via a an i me my we he it of to in is on at by or as if no up do be am".split()
)


def tokenize(text: str) -> list[str]:
    cleaned = (text or "").lower()
    cleaned = re.sub(r"[^a-z0-9\s#+.-]", " ", cleaned)
    tokens = cleaned.split()
    return [w for w in tokens if len(w) > 2 and w not in STOP_WORDS]


def generate_summary(raw: str) -> dict:
    lines = [l for l in (raw or "").split("\n") if l.strip() and len(l.strip()) > 15]

    scored = []
    for i, line in enumerate(lines):
        s = 0
        if i < 3:
            s += 3
        if re.search(r"looking|seeking|hire|join|build|work|role|position|responsible|deliver", line, re.I):
            s += 2
        if re.search(r"\d+\+?\s*years?", line, re.I):
            s += 1
        if re.search(r"require|must|need|should|essential|critical", line, re.I):
            s += 1
        if len(line) > 200:
            s -= 1
        scored.append({"line": line.strip(), "score": s})

    scored.sort(key=lambda x: x["score"], reverse=True)
    summary = [f"• {s['line']}" for s in scored[:3]]

    req_lines = [
        l for l in lines
        if re.search(r"require|must|need|should|experience|proficient|familiar|knowledge|skill|expertise|strong|excellent", l, re.I)
    ]
    requirements = [re.sub(r"^[-•*]\s*", "", l).strip() for l in req_lines[:8]]

    return {"summary": summary, "requirements": requirements}


def analyze_fit(raw: str, base_resume: str) -> dict | None:
    if not base_resume or len(base_resume.strip()) < 20:
        return None

    job_tokens = set(tokenize(raw))
    res_tokens = set(tokenize(base_resume))

    matched = []
    missing = []
    for t in job_tokens:
        if t in res_tokens:
            matched.append(t)
        else:
            missing.append(t)

    meaningful_missing = [w for w in missing if len(w) > 3][:15]
    meaningful_matched = [w for w in matched if len(w) > 3][:15]
    ratio = len(matched) / max(1, len(job_tokens))
    fit_score = min(5, max(1, round(ratio * 8)))

    return {
        "fitScore": fit_score,
        "matched": meaningful_matched,
        "missing": meaningful_missing,
        "ratio": round(ratio * 100),
    }
```

- [ ] **Step 2: Verify module loads and produces output**

Run: `cd "/Users/mehran/Documents/Codes/Job Application CRM" && python -c "
from ai import generate_summary, analyze_fit
result = generate_summary('Senior Frontend Engineer at Stripe\n\nWe are looking for a Senior Frontend Engineer to join our Payments team.\n\nRequirements:\n- 5+ years React/TypeScript experience\n- Strong understanding of web performance')
print('summary count:', len(result['summary']))
print('reqs count:', len(result['requirements']))
assert len(result['summary']) > 0
fit = analyze_fit('React TypeScript engineer', 'I know React and TypeScript well')
print('fit score:', fit['fitScore'])
assert fit is not None
print('AI MODULE OK')
"`
Expected: `AI MODULE OK`

- [ ] **Step 3: Commit**

```bash
git add ai.py
git commit -m "feat: add AI analysis module (summary + fit analysis)"
```

---

### Task 5: Telegram bot handler

**Files:**
- Create: `bot.py`

- [ ] **Step 1: Write bot.py with message handler that parses and stores jobs**

```python
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

from database import create_job
from parser import parse_telegram_message

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context):
    """Handle incoming messages forwarded to the bot."""
    if not update.message or not update.message.text:
        return

    raw = update.message.text
    logger.info(f"Received Telegram message: {raw[:80]}...")

    try:
        parsed = parse_telegram_message(raw)
        job = await create_job(parsed)
        logger.info(
            f"Stored job: {job.get('role_title', 'Untitled')} at {job.get('company_name', 'Unknown')} (id={job['id']})"
        )
        await update.message.reply_text(
            f"✅ Job added to CRM!\n\n"
            f"📋 {job.get('role_title', 'Untitled')}\n"
            f"🏢 {job.get('company_name', 'Unknown')}\n"
            f"📍 {job.get('location', 'N/A')}\n"
            f"💰 {job.get('salary', 'N/A')}\n\n"
            f"Review it at: http://localhost:8000"
        )
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        await update.message.reply_text(f"❌ Failed to process job: {str(e)[:100]}")


def create_bot_app(token: str) -> Application:
    """Create and configure the Telegram bot application."""
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
```

- [ ] **Step 2: Verify module loads**

Run: `cd "/Users/mehran/Documents/Codes/Job Application CRM" && python -c "import bot; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add bot.py
git commit -m "feat: add Telegram bot handler that parses and stores incoming jobs"
```

---

### Task 6: FastAPI application with REST API

**Files:**
- Create: `main.py`

- [ ] **Step 1: Write main.py with all API endpoints, HTML serving, and bot startup**

```python
import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ai import analyze_fit, generate_summary
from bot import create_bot_app
from database import (
    RESUMES_DIR,
    create_job,
    delete_job,
    get_all_settings,
    get_job,
    get_jobs,
    get_setting,
    get_status_counts,
    import_jobs,
    init_db,
    set_setting,
    update_job,
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
PORT = int(os.getenv("PORT", "8000"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

INDEX_PATH = Path(__file__).parent / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    # Seed sample data if DB is empty
    existing = await get_jobs()
    if not existing:
        await _seed_sample_data()

    # Start Telegram bot polling in background
    if BOT_TOKEN:
        bot_app = create_bot_app(BOT_TOKEN)
        asyncio.create_task(_run_bot(bot_app))
        logger.info("Telegram bot polling started")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot disabled")

    yield

    # Shutdown: bot stops automatically


async def _run_bot(bot_app):
    """Run the Telegram bot polling loop."""
    try:
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        # Keep running until cancelled
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
    except Exception as e:
        logger.error(f"Bot error: {e}")


async def _seed_sample_data():
    """Insert sample jobs if the database is empty."""
    samples = [
        {
            "raw_message": "Senior Frontend Engineer at Stripe\n\nWe are looking for a Senior Frontend Engineer to join our Payments team. You will build and maintain critical payment interfaces used by millions of businesses worldwide.\n\nRequirements:\n- 5+ years React/TypeScript experience\n- Strong understanding of web performance optimization\n- Experience with payment systems preferred\n- Excellent communication skills\n\nSalary: $180,000 – $250,000\nLocation: Remote (US)\nType: Full-time\n\nApply: https://stripe.com/careers/senior-frontend-2024",
            "role_title": "Senior Frontend Engineer", "company_name": "Stripe",
            "location": "Remote (US)", "salary": "$180,000 – $250,000",
            "job_type": "Full-time", "apply_link": "https://stripe.com/careers/senior-frontend-2024",
            "status": "Applied", "fit_score": 4, "interest_score": 5,
            "date_received": "2025-01-15T10:30:00Z",
            "date_reviewed": "2025-01-15T14:00:00Z",
            "date_applied": "2025-01-16T09:00:00Z",
            "resume_version_name": "resume_stripe_v2.pdf",
            "cover_letter": "Excited to contribute to payment infrastructure used globally.",
            "notes": "Strong fit. React + TS alignment is excellent. Check payment domain knowledge.",
            "response_received": "yes", "stage_reached": "Interview",
        },
        {
            "raw_message": "Backend Developer — Notion\n\nJoin Notion to help build the next generation of productivity tools. We need someone passionate about distributed systems and real-time collaboration.\n\nWhat you need:\n- 3+ years Go or Rust\n- Distributed systems experience\n- PostgreSQL, Redis\n- CI/CD pipelines\n\n$160k–$210k · San Francisco / Remote · Full-time\n\nhttps://notion.so/careers/backend-dev",
            "role_title": "Backend Developer", "company_name": "Notion",
            "location": "San Francisco / Remote", "salary": "$160k–$210k",
            "job_type": "Full-time", "apply_link": "https://notion.so/careers/backend-dev",
            "status": "Will Apply", "fit_score": 3, "interest_score": 4,
            "date_received": "2025-01-18T08:15:00Z",
            "date_reviewed": "2025-01-18T11:00:00Z",
            "notes": "Interesting product. Need to highlight distributed systems experience.",
        },
        {
            "raw_message": "Full Stack Developer @ Vercel\n\nWe are hiring a Full Stack Developer to work on our deployment platform. You will ship features used by millions of developers.\n\nRequirements:\n- React, Next.js proficiency\n- Node.js backend experience\n- TypeScript must\n- AWS or GCP familiarity\n\nSalary: $170,000 - $230,000\nRemote-first\nFull-time\n\nApply here: https://vercel.com/careers/full-stack",
            "role_title": "Full Stack Developer", "company_name": "Vercel",
            "location": "Remote-first", "salary": "$170,000 - $230,000",
            "job_type": "Full-time", "apply_link": "https://vercel.com/careers/full-stack",
            "status": "New", "fit_score": 0, "interest_score": 0,
            "date_received": "2025-01-20T14:45:00Z",
        },
        {
            "raw_message": "Lead UI Engineer | Figma\n\nFigma is looking for a Lead UI Engineer to drive our design system forward. You will lead a small team building component libraries and design tooling.\n\nMust have:\n- 7+ years frontend experience\n- Design systems expertise\n- WebGL or Canvas knowledge a plus\n- Leadership experience\n\nComp: $200k–$280k + equity\nSan Francisco / Hybrid\nFull-time\n\nhttps://figma.com/careers/lead-ui",
            "role_title": "Lead UI Engineer", "company_name": "Figma",
            "location": "San Francisco / Hybrid", "salary": "$200k–$280k",
            "job_type": "Full-time", "apply_link": "https://figma.com/careers/lead-ui",
            "status": "Reviewing", "fit_score": 3, "interest_score": 5,
            "date_received": "2025-01-19T09:00:00Z",
            "date_reviewed": "2025-01-19T15:30:00Z",
            "notes": "Dream role. Need to prepare design systems portfolio.",
        },
        {
            "raw_message": "DevOps Engineer at Datadog\n\nLooking for a DevOps Engineer to manage our monitoring infrastructure at scale.\n\n- Kubernetes, Terraform, Ansible\n- AWS/GCP experience\n- CI/CD pipeline design\n- On-call rotation required\n\n$150k-$190k · NYC / Remote · Full-time\nhttps://datadog.com/jobs/devops",
            "role_title": "DevOps Engineer", "company_name": "Datadog",
            "location": "NYC / Remote", "salary": "$150k-$190k",
            "job_type": "Full-time", "apply_link": "https://datadog.com/jobs/devops",
            "status": "Rejected", "fit_score": 2, "interest_score": 2,
            "date_received": "2025-01-10T11:00:00Z",
            "date_reviewed": "2025-01-10T16:00:00Z",
            "rejection_reason": "Not aligned with career direction. Too infrastructure-focused.",
        },
        {
            "raw_message": "Frontend Developer — Linear\n\nHelp us build the fastest project management tool. We value craft, speed, and simplicity.\n\n- React + TypeScript\n- Performance obsession\n- CSS animations expertise\n- Small team, high ownership\n\n$140k-$190k · Remote · Full-time\nhttps://linear.app/careers/frontend",
            "role_title": "Frontend Developer", "company_name": "Linear",
            "location": "Remote", "salary": "$140k-$190k",
            "job_type": "Full-time", "apply_link": "https://linear.app/careers/frontend",
            "status": "Interviewing", "fit_score": 5, "interest_score": 5,
            "date_received": "2025-01-08T07:30:00Z",
            "date_reviewed": "2025-01-08T10:00:00Z",
            "date_applied": "2025-01-09T08:00:00Z",
            "resume_version_name": "resume_linear_v3.pdf",
            "notes": "Went great! Going to final round next week.",
            "response_received": "yes", "stage_reached": "Final Round",
        },
    ]
    for job_data in samples:
        await create_job(job_data)
    await set_setting("base_resume", "Senior Frontend Engineer with 6 years of experience in React, TypeScript, and modern web technologies. Built performant UIs for SaaS products serving 100k+ users. Proficient in Next.js, Tailwind CSS, Webpack, testing with Jest and Cypress. Experience with Node.js, PostgreSQL, REST APIs, GraphQL. Strong skills in performance optimization, accessibility, and design system development. Led teams of 3-5 engineers. Familiar with AWS, Docker, CI/CD pipelines.")
    logger.info("Sample data seeded")


app = FastAPI(lifespan=lifespan)


# ===== Serve frontend =====

@app.get("/")
async def serve_index():
    return FileResponse(INDEX_PATH)


# ===== Jobs API =====

@app.get("/api/jobs")
async def list_jobs(
    status: str = Query(None),
    search: str = Query(None),
    sort: str = Query("date_desc"),
    since_id: str = Query(None),
):
    jobs = await get_jobs(status=status, search=search, sort=sort, since_id=since_id)
    # Deserialize JSON fields
    for job in jobs:
        for field in ("ai_summary", "ai_requirements", "ai_fit"):
            if job.get(field) and isinstance(job[field], str):
                try:
                    job[field] = json.loads(job[field])
                except (json.JSONDecodeError, TypeError):
                    pass
    return jobs


@app.get("/api/jobs/{job_id}")
async def read_job(job_id: str):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    for field in ("ai_summary", "ai_requirements", "ai_fit"):
        if job.get(field) and isinstance(job[field], str):
            try:
                job[field] = json.loads(job[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return job


@app.post("/api/jobs")
async def add_job(job_data: dict):
    # Handle timestamps for status transitions
    now = datetime.utcnow().isoformat() + "Z"
    status = job_data.get("status", "New")
    if status in ("Reviewing",) and not job_data.get("date_reviewed"):
        job_data["date_reviewed"] = now
    if status in ("Applied",) and not job_data.get("date_applied"):
        job_data["date_applied"] = now
    job = await create_job(job_data)
    return job


@app.put("/api/jobs/{job_id}")
async def edit_job(job_id: str, updates: dict):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    now = datetime.utcnow().isoformat() + "Z"
    new_status = updates.get("status")

    # Auto-set dates on status transitions
    if new_status == "Reviewing" and not job.get("date_reviewed") and not updates.get("date_reviewed"):
        updates["date_reviewed"] = now
    if new_status == "Applied" and not job.get("date_applied") and not updates.get("date_applied"):
        updates["date_applied"] = now

    updated = await update_job(job_id, updates)
    return updated


@app.delete("/api/jobs/{job_id}")
async def remove_job(job_id: str):
    deleted = await delete_job(job_id)
    if not deleted:
        raise HTTPException(404, "Job not found")
    return {"ok": True}


# ===== Resume API =====

@app.post("/api/jobs/{job_id}/resume")
async def upload_resume(job_id: str, file: UploadFile = File(...)):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # Validate file
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 5MB)")

    allowed_exts = (".pdf", ".doc", ".docx")
    filename = file.filename or "resume.pdf"
    if not any(filename.lower().endswith(ext) for ext in allowed_exts):
        raise HTTPException(400, "Only PDF, DOC, DOCX files allowed")

    # Save file
    safe_name = f"{job_id}_{filename}"
    filepath = RESUMES_DIR / safe_name
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 5MB)")

    filepath.write_bytes(content)

    # Update job record
    await update_job(job_id, {"resume_path": str(filepath), "resume_version_name": filename})
    return {"ok": True, "filename": filename}


@app.delete("/api/jobs/{job_id}/resume")
async def remove_resume(job_id: str):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    if job.get("resume_path"):
        resume_file = Path(job["resume_path"])
        if resume_file.exists():
            resume_file.unlink()
        await update_job(job_id, {"resume_path": None, "resume_version_name": ""})

    return {"ok": True}


@app.get("/api/jobs/{job_id}/resume")
async def download_resume(job_id: str):
    job = await get_job(job_id)
    if not job or not job.get("resume_path"):
        raise HTTPException(404, "Resume not found")

    filepath = Path(job["resume_path"])
    if not filepath.exists():
        raise HTTPException(404, "Resume file missing on disk")

    return FileResponse(filepath, filename=job.get("resume_version_name", filepath.name))


# ===== AI API =====

@app.post("/api/jobs/{job_id}/ai-summary")
async def run_ai_summary(job_id: str):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    result = generate_summary(job["raw_message"] or "")
    await update_job(job_id, {
        "ai_summary": result["summary"],
        "ai_requirements": result["requirements"],
    })
    return result


@app.post("/api/jobs/{job_id}/ai-fit")
async def run_ai_fit(job_id: str):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    base_resume = await get_setting("base_resume")
    if not base_resume or len(base_resume.strip()) < 20:
        raise HTTPException(400, "Set your base resume in Settings first")

    result = analyze_fit(job["raw_message"] or "", base_resume)
    if not result:
        raise HTTPException(400, "Could not analyze fit")

    await update_job(job_id, {"ai_fit": result})
    return result


# ===== Settings API =====

@app.get("/api/settings")
async def read_settings():
    settings = await get_all_settings()
    return settings


@app.put("/api/settings")
async def write_settings(settings: dict):
    for key, value in settings.items():
        await set_setting(key, value)
    return await get_all_settings()


# ===== Import/Export =====

@app.get("/api/export")
async def export_data():
    jobs = await get_jobs()
    settings = await get_all_settings()
    for job in jobs:
        for field in ("ai_summary", "ai_requirements", "ai_fit"):
            if job.get(field) and isinstance(job[field], str):
                try:
                    job[field] = json.loads(job[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        # Don't export resume file contents
        job.pop("resume_file", None)
    return {"jobs": jobs, "settings": settings}


@app.post("/api/import")
async def import_data(data: dict):
    if "jobs" not in data or not isinstance(data["jobs"], list):
        raise HTTPException(400, "Invalid format: expected {jobs: [...]}")

    await import_jobs(data["jobs"])

    if data.get("settings"):
        for key, value in data["settings"].items():
            await set_setting(key, value)

    return {"imported": len(data["jobs"])}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
```

- [ ] **Step 2: Start the server and verify it boots**

Run: `cd "/Users/mehran/Documents/Codes/Job Application CRM" && python main.py &`
Then: `curl -s http://localhost:8000/api/jobs | python -m json.tool | head -20`
Expected: JSON array of sample jobs

- [ ] **Step 3: Verify API endpoints work**

Run: `curl -s http://localhost:8000/api/settings | python -m json.tool`
Expected: JSON with `base_resume` key

Run: `curl -s -X POST http://localhost:8000/api/jobs -H "Content-Type: application/json" -d '{"raw_message":"Test Job at TestCo","role_title":"Test Job","company_name":"TestCo"}' | python -m json.tool`
Expected: JSON of the created job

- [ ] **Step 4: Stop the test server**

Run: `pkill -f "python main.py"`

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "feat: add FastAPI application with REST API and bot startup"
```

---

### Task 7: Frontend — Replace localStorage with API calls

**Files:**
- Modify: `index.html` (the entire `<script>` section)

This is the largest task. The frontend currently reads/writes everything from `localStorage`. We need to replace all data operations with `fetch()` calls to the REST API, add polling for new Telegram jobs, and show a connection status indicator.

- [ ] **Step 1: Replace the DATABASE section with async API functions**

Replace the entire `// ========== DATABASE ==========` block (from `let DB = ...` through `saveSettings(s)...`) with:

```javascript
// ========== API ==========
let API_BASE = '';
let lastSeenJobId = null;
let serverConnected = true;

async function api(path, opts = {}) {
  try {
    const res = await fetch(API_BASE + path, {
      headers: { 'Content-Type': 'application/json', ...opts.headers },
      ...opts,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'API error');
    }
    if (res.status === 204) return null;
    serverConnected = true;
    updateConnectionBanner();
    return res.json();
  } catch (e) {
    if (e.message === 'Failed to fetch') {
      serverConnected = false;
      updateConnectionBanner();
    }
    throw e;
  }
}

async function getJobs() { return api('/api/jobs'); }
async function getJobsFiltered(status, search, sort) {
  const params = new URLSearchParams();
  if (status && status !== 'all') params.set('status', status);
  if (search) params.set('search', search);
  if (sort) params.set('sort', sort);
  return api('/api/jobs?' + params.toString());
}
async function getJob(id) { return api('/api/jobs/' + id); }
async function saveJob(job) {
  if (job.id) return api('/api/jobs/' + job.id, { method: 'PUT', body: JSON.stringify(job) });
  return api('/api/jobs', { method: 'POST', body: JSON.stringify(job) });
}
async function deleteJobAsync(id) { return api('/api/jobs/' + id, { method: 'DELETE' }); }
async function getSettings() { return api('/api/settings'); }
async function saveSettings(s) { return api('/api/settings', { method: 'PUT', body: JSON.stringify(s) }); }
```

- [ ] **Step 2: Add connection banner and polling functions**

Add after the API section:

```javascript
function updateConnectionBanner() {
  let banner = document.getElementById('conn-banner');
  if (!banner) return;
  banner.style.display = serverConnected ? 'none' : 'flex';
}

async function pollNewJobs() {
  if (!serverConnected) return;
  try {
    const jobs = await api('/api/jobs?sort=date_desc');
    if (jobs.length > 0) {
      const newestId = jobs[0].id;
      if (lastSeenJobId && newestId !== lastSeenJobId) {
        const newJobs = jobs.filter(j => !lastSeenJobId || j.date_received > jobs.find(j2 => j2.id === lastSeenJobId)?.date_received);
        if (newJobs.length > 0) {
          toast(`${newJobs.length} new job${newJobs.length > 1 ? 's' : ''} from Telegram!`, 'info');
          lastSeenJobId = newestId;
          if (currentPage === 'dashboard' || currentPage === 'jobs' || currentPage === 'inbox') render();
        }
      }
      if (!lastSeenJobId) lastSeenJobId = newestId;
    }
  } catch (e) { /* poll will retry */ }
}

setInterval(pollNewJobs, 10000);
```

- [ ] **Step 3: Add the connection banner HTML element**

Inside `<body>`, right before `<!-- Toasts -->`, add:

```html
<div id="conn-banner" class="fixed top-0 left-0 right-0 z-50 bg-red-900/90 text-red-200 text-center py-2 text-sm font-medium hidden" style="display:none;">
  <i class="fa-solid fa-plug-circle-xmark mr-2"></i> Server disconnected — make sure <code>python main.py</code> is running
</div>
```

- [ ] **Step 4: Make all render functions async and update data fetching**

Change every render function that calls `getJobs()` or `getJob()` to use `await`:

- `renderDashboard()`: change `const jobs = getJobs()` to `const jobs = await getJobs()`
- `renderJobs()`: change `let jobs = getJobs()` to `let jobs = await getJobsFiltered(statusFilter, searchQuery, sortOrder)`
- `renderJobDetail()`: change `const job = getJob(selectedJobId)` to `const job = await getJob(selectedJobId)`
- `renderInbox()`: change the `getJobs()` call to `await getJobs()`
- `renderSettings()`: change `getSettings()` to `await getSettings()`
- `render()`: change to `async function render()` and use `await` on all render calls

- [ ] **Step 5: Update all action functions to use async API calls**

Replace every action function:

- `updateField()`: `const job = await getJob(id)` then `await saveJob(job)`
- `updateScore()`: `const job = await getJob(id)` then `await saveJob(job)`
- `advanceStatus()`: `const job = await getJob(id)` then `job.status = newStatus` then `await saveJob(job)`
- `doReject()`: `await saveJob(job)` instead of `saveJob(job)`
- `doDelete()`: `await deleteJobAsync(id)` instead of `deleteJob(id)`
- `runSummary()`: `await api('/api/jobs/' + id + '/ai-summary', { method: 'POST' })`
- `runFitAnalysis()`: `await api('/api/jobs/' + id + '/ai-fit', { method: 'POST' })`
- `uploadResume()`: use `FormData` + `fetch(API_BASE + '/api/jobs/' + id + '/resume', { method: 'POST', body: formData })`
- `removeResume()`: `await api('/api/jobs/' + id + '/resume', { method: 'DELETE' })`
- `confirmAddParsed()`: `await saveJob(parsed)`
- `quickAdd()`: `await saveJob(parsed)`
- `saveBaseResume()`: `await saveSettings({ base_resume: ... })`
- `exportData()`: `const data = await api('/api/export')` then download
- `importData()`: `await api('/api/import', { method: 'POST', body: JSON.stringify(data) })`
- `doClear()`: delete all jobs one by one or add a clear endpoint
- `resetSampleData()`: just reload the page after re-seeding

- [ ] **Step 6: Update sidebar stats to use async API**

Change `updateNav()` to use `await getJobs()` for sidebar stat counts.

- [ ] **Step 7: Remove the placeholder Telegram Python snippet from inbox page**

In `renderInbox()`, remove the entire `<!-- Telegram Setup Info -->` block and replace with:

```html
<div class="bg-surface border border-brd rounded-lg p-5 mt-6">
  <h2 class="text-xs font-semibold uppercase tracking-wide text-zinc-400 mb-3">Telegram Bot Status</h2>
  <div class="flex items-center gap-2 text-sm">
    <span class="w-2 h-2 rounded-full pulse-dot ${serverConnected ? 'bg-emerald-400' : 'bg-red-400'}"></span>
    <span class="text-zinc-300">${serverConnected ? 'Server connected' : 'Server disconnected'}</span>
  </div>
  <p class="text-xs text-zinc-500 mt-2">Forward job posts to your Telegram bot. They will appear here automatically within 10 seconds.</p>
</div>
```

- [ ] **Step 8: Remove the seed data / localStorage functions**

Delete `loadDB()`, `saveDB()`, `seedSampleData()`, `makeJob()`, and all references to `DB`, `localStorage`.

- [ ] **Step 9: Verify the full app loads and works**

Run: `cd "/Users/mehran/Documents/Codes/Job Application CRM" && python main.py &`
Then open `http://localhost:8000` in a browser. Verify:
- Dashboard loads with sample jobs
- Clicking a job opens detail view
- Changing status works
- Scoring sliders work
- Search and filter work
- Settings page shows base resume

- [ ] **Step 10: Stop server and commit**

```bash
pkill -f "python main.py"
git add index.html
git commit -m "feat: migrate frontend from localStorage to REST API with polling"
```

---

### Task 8: End-to-end integration test

**Files:**
- No new files

- [ ] **Step 1: Start the server**

Run: `cd "/Users/mehran/Documents/Codes/Job Application CRM" && python main.py &`
Wait for: "Uvicorn running on http://0.0.0.0:8000"

- [ ] **Step 2: Verify all API endpoints respond correctly**

Run:
```bash
# List jobs
curl -s http://localhost:8000/api/jobs | python -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} jobs')"

# Get single job
JOB_ID=$(curl -s http://localhost:8000/api/jobs | python -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
curl -s http://localhost:8000/api/jobs/$JOB_ID | python -c "import sys,json; d=json.load(sys.stdin); print(d['role_title'])"

# Update a job
curl -s -X PUT http://localhost:8000/api/jobs/$JOB_ID -H "Content-Type: application/json" -d '{"notes":"Integration test note"}' | python -c "import sys,json; d=json.load(sys.stdin); print(d['notes'])"

# Get settings
curl -s http://localhost:8000/api/settings | python -c "import sys,json; d=json.load(sys.stdin); print('base_resume' in d)"

# AI summary
curl -s -X POST http://localhost:8000/api/jobs/$JOB_ID/ai-summary | python -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('summary',[])))"

# Export
curl -s http://localhost:8000/api/export | python -c "import sys,json; d=json.load(sys.stdin); print(f'export: {len(d[\"jobs\"])} jobs')"
```
Expected: All commands return valid data

- [ ] **Step 3: Stop the server**

Run: `pkill -f "python main.py"`

- [ ] **Step 4: Commit (no changes, just verification)**

If any fixes were needed, commit them.

---

### Task 9: Final cleanup and documentation

**Files:**
- No new files needed, just verify everything

- [ ] **Step 1: Verify .env is in .gitignore**

Run: `grep -q ".env" "/Users/mehran/Documents/Codes/Job Application CRM/.gitignore" && echo "OK" || echo "MISSING"`
Expected: `OK`

- [ ] **Step 2: Verify the project structure is correct**

Run: `ls -la "/Users/mehran/Documents/Codes/Job Application CRM/"`
Expected: `main.py`, `bot.py`, `database.py`, `parser.py`, `ai.py`, `requirements.txt`, `.env`, `.gitignore`, `index.html`

- [ ] **Step 3: Final commit if any cleanup needed**

```bash
git add -A
git commit -m "chore: final cleanup for telegram bot integration"
```

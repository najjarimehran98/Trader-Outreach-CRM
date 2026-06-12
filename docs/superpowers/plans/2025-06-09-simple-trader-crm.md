# Simple Trader CRM Implementation Plan

> **Goal**: Transform Job Application CRM → Trader Acquisition CRM without AI or external APIs
> **Approach**: Simple, clean, deployable to GitHub
> **Date**: 2025-06-09

---

## SECTION 1: CURRENT ARCHITECTURE REVIEW

### What We Have

FastAPI backend + vanilla JS frontend. Single `jobs` table with job application fields. Workflow: Job Found → Research → Applied → Interview → Offer → Rejected.

### What We Need

Replace `jobs` table with `traders` table. New workflow: Trader Found → Research → Contacted → Replied → Interested → Meeting Scheduled → Negotiation → Onboarding → Active Creator → Rejected/No Response.

Key changes:
- Job fields → Trader fields (name, platform, performance metrics, social links, etc.)
- 7 statuses → 11 trader statuses
- Add scoring (6 x 1-10 scales, calculated fit score)
- Add outreach logging (what we sent to whom)
- No AI. Manual notes only.
- Remove Telegram bot (no auto-ingestion)
- Keep UI similar but adapt for traders

---

## SECTION 2: REUSABLE COMPONENTS

**KEEP**:
- FastAPI structure (`main.py`)
- Database layer pattern (`database.py`)
- Frontend design system (Apple dark theme)
- API CRUD pattern
- File upload pattern (if we keep attachments)
- Import/Export
- Settings management

**REMOVE**:
- `bot.py` (Telegram bot)
- All AI functions (`ai.py`, `/api/*/ai-*` endpoints)

**REFACTOR**:
- `parser.py`: Rename `parse_telegram_message()` → `parse_trader_profile()` and make it generic text parser for "Quick Paste" feature in Discovery page. Keep both Python and JavaScript versions.

---

## SECTION 3: REQUIRED REFACTORS

### Database Schema

New `traders` table:

```sql
CREATE TABLE traders (
    id TEXT PRIMARY KEY,
    trader_name TEXT NOT NULL,
    profile_url TEXT UNIQUE,
    platform TEXT DEFAULT 'Manual',
    location TEXT DEFAULT '',
    language TEXT DEFAULT '',
    followers INTEGER DEFAULT 0,
    copiers INTEGER DEFAULT 0,
    assets_under_management REAL DEFAULT 0.0,
    monthly_return REAL DEFAULT 0.0,
    yearly_return REAL DEFAULT 0.0,
    maximum_drawdown REAL DEFAULT 0.0,
    risk_score INTEGER DEFAULT 0,
    strategy_type TEXT DEFAULT '',
    twitter TEXT DEFAULT '',
    telegram TEXT DEFAULT '',
    discord TEXT DEFAULT '',
    youtube TEXT DEFAULT '',
    website TEXT DEFAULT '',
    contact_method TEXT DEFAULT '',
    contact_info TEXT DEFAULT '',
    first_contact_date TEXT,
    last_contact_date TEXT,
    outreach_attempts INTEGER DEFAULT 0,
    audience_strength INTEGER DEFAULT 0,
    trading_consistency INTEGER DEFAULT 0,
    communication_quality INTEGER DEFAULT 0,
    crypto_knowledge INTEGER DEFAULT 0,
    likelihood_to_join INTEGER DEFAULT 0,
    brand_value INTEGER DEFAULT 0,
    fit_score INTEGER DEFAULT 0, -- calculated weighted avg
    creator_score INTEGER DEFAULT 0, -- admin override
    research_notes TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    status TEXT DEFAULT 'Trader Found',
    pipeline_stage TEXT DEFAULT 'Research',
    conversion_date TEXT,
    rejection_date TEXT,
    rejection_reason TEXT DEFAULT '',
    date_added TEXT NOT NULL,
    date_updated TEXT NOT NULL,
    date_researched TEXT,
    date_contacted TEXT,
    date_replied TEXT,
    date_interested TEXT,
    date_meeting_scheduled TEXT,
    date_negotiation_started TEXT,
    date_onboarded TEXT
);
```

**Indexes**:
```sql
CREATE INDEX idx_traders_platform ON traders(platform);
CREATE INDEX idx_traders_status ON traders(status);
CREATE INDEX idx_traders_fit_score ON traders(fit_score DESC);
CREATE INDEX idx_traders_date_added ON traders(date_added DESC);
```

**Valid statuses**: Trader Found, Researching, Contacted, Replied, Interested, Meeting Scheduled, Negotiation, Onboarding, Active Creator, Rejected, No Response

**Valid stages**: Research, Outreach, Follow-up, Interview, Due Diligence, Contract, Setup, Active, Closed

### API Changes

Rename all `/api/jobs` to `/api/traders`.

Add new endpoints:
- `POST /api/traders/{id}/outreach` - log outreach (date, method, notes) → creates record in outreach_logs table
- `GET /api/traders/stats` - dashboard metrics
- (No timeline endpoint - timeline derived on frontend from date fields + outreach logs)

Remove: `/api/jobs/{id}/resume` (no resumes)

Keep: `/api/settings`, `/api/export`, `/api/import`

### Frontend Changes

**Pages**:
1. Dashboard → Trader metrics + funnel chart + platform breakdown
2. Jobs List → Traders List (new filters: platform, fit score, risk score)
3. Job Detail → Trader Detail (all new fields, two-column layout)
4. Inbox → Discovery (manual entry only, no Telegram bot)
5. Settings → add scoring weights

**Components**:
- Platform badge (brand colors)
- Score gauges (1-10 sliders with visual bars)
- Outreach log (list of sent messages)
- Activity timeline

**State**: Convert to `state` object (cleaner than globals)

---

## SECTION 4: DATABASE MIGRATION PLAN

**Fresh start approach** (recommended):
1. Backup `jobs.db` to `jobs.backup.db`
2. Run SQL migration to create `traders` table with indexes
3. No data migration (different domain)
4. Optional: Load small sample data (5-10 traders)

**Migration script**: `migrations/001_create_traders.sql`

**Database.py changes**:
- Rename all functions: `get_jobs` → `get_traders`, `create_job` → `create_trader`, etc.
- Update field names (role_title → trader_name, company_name → N/A, etc.)
- Add `calculate_fit_score(trader, weights)` - weighted average of 6 scores
- Add `get_traders_stats()` - counts by status, platform, conversion rate
- Add `log_outreach(trader_id, method, notes)` - inserts into new `outreach_logs` table (optional) or append to trader.notes

**New table** for outreach history (clean separation):
```sql
CREATE TABLE outreach_logs (
    id TEXT PRIMARY KEY,
    trader_id TEXT NOT NULL,
    date_sent TEXT NOT NULL,
    method TEXT NOT NULL, -- email, telegram, twitter, discord, linkedin, other
    notes TEXT DEFAULT '',
    FOREIGN KEY (trader_id) REFERENCES traders(id)
);
```
Note: `platform` field (where trader trades) vs `contact_method` (how we reached them) are separate. Platform = eToro/MQL5/etc. Contact method = email/telegram/twitter/etc.

---

## SECTION 5: BACKEND CHANGES

### Files to Modify

1. **`database.py`**:
   - Replace all `jobs` SQL with `traders`
   - Update field mappings
   - Add `calculate_fit_score()`
   - Add `get_stats()`
   - Update ID generation (same pattern)
   - Keep async, keep connection pooling

2. **`main.py`**:
   - Rename routes: `/api/jobs` → `/api/traders`
   - Add `/api/traders/stats` endpoint
   - Add `/api/traders/{id}/outreach` endpoint
   - Remove `/api/jobs/{id}/resume` endpoints
   - Update all handlers to use trader fields
   - Update Pydantic models (if any) or dict schemas
   - Update import/export to use traders

3. **`parser.py`**:
   - Rename `parse_telegram_message()` → `parse_trader_profile()`
   - Make it generic: extract trader_name, location, social links, metrics from any pasted text
   - Keep for Discovery page "Quick Paste" feature

4. **`bot.py`**: **DELETE** - no Telegram bot

5. **`ai.py`**: **DELETE** - no AI

6. **`requirements.txt`**: No changes (still FastAPI, aiosqlite)

7. **`main.py`**: Remove `bot.py` import and startup

8. **`settings` table**: Add new keys:
   - `scoring_weights.audience_strength` (float, default 1.0)
   - `scoring_weights.trading_consistency` (float, default 1.0)
   - `scoring_weights.communication_quality` (float, default 1.0)
   - `scoring_weights.crypto_knowledge` (float, default 1.0)
   - `scoring_weights.likelihood_to_join` (float, default 1.0)
   - `scoring_weights.brand_value` (float, default 1.0)
   - `platforms.enabled` (JSON list, default ["Manual", "Telegram", "eToro", "MQL5", "TradingView", "ZuluTrade"])

### Fit Score Calculation

```python
def calculate_fit_score(trader, weights):
    # trader has 6 score fields (1-10 each)
    # weights is dict from settings with 6 keys
    total = 0
    max_possible = 0
    for field in ['audience_strength', 'trading_consistency', 'communication_quality',
                  'crypto_knowledge', 'likelihood_to_join', 'brand_value']:
        score = trader.get(field, 0)
        weight = weights.get(field, 1.0)
        total += score * weight
        max_possible += 10 * weight
    if max_possible == 0:
        return 0
    return int(round((total / max_possible) * 100))
```

Store in `fit_score` field (0-100).

---

## SECTION 6: FRONTEND CHANGES

### Design System Additions (`design-system.css`)

Add platform colors:
```css
:root {
  --platform-etoro: #1ebc9d;
  --platform-mql5: #102447;
  --platform-myfxbook: #2a9d8f;
  --platform-zulutrade: #ff6b35;
  --platform-darwinex: #00a4e4;
  --platform-naga: #6a4c93;
  --platform-tradingview: #131722;
  --platform-fxblue: #2196f3;
  --platform-telegram: #0088cc;
  --platform-twitter: #1da1f2;
  --platform-discord: #5865f2;
  --platform-manual: #8e8e93;
}
```

Add score bar styles (horizontal bars for 1-10 sliders)

### Page Updates

**1. Dashboard (`renderDashboard()`)**:
- Total Traders count
- Active Pipeline count (status not in [Active Creator, Rejected, No Response])
- Total Outreach Attempts (sum of outreach_attempts)
- Reply Rate (Replied / Contacted) as percentage
- Funnel: horizontal bars for each status with percentages
- Platform Distribution: bar chart with platform colors
- Recent High-Priority: traders with fit_score >= 70

**2. Traders List (`renderTraders()`)**:
- Filters: status (11 options), platform (dynamic), min fit (0-100), max risk (0-10), search (name, url, notes), stage (optional)
- Columns: Platform badge | Name | Fit score (0-100 bar) | Status pill | Last contact | Outreach count
- Sort: date_added, fit_score, last_contact
- Row click → detail, Quick actions: Advance status, Log outreach

**3. Trader Detail (`renderTraderDetail()`)**:

Two-column layout:

**Left column**:
- Header: Name, Platform badge, Profile URL, Status dropdown, Stage dropdown, Fit score visualization
- Basic Info: location, language, strategy type, contact method/info
- Performance: followers, copiers, AUM, monthly_return, yearly_return, max_drawdown, risk_score (all read-only metrics)
- Social: twitter, telegram, discord, youtube, website
- Scoring (6 sliders 1-10): audience_strength, trading_consistency, communication_quality, crypto_knowledge, likelihood_to_join, brand_value + calculated fit_score displayed
- Outreach Log: list of logged messages (from outreach_logs table) + button to log new outreach (modal with date, method dropdown, notes)

**Right column (sidebar)**:
- Research Notes (textarea)
- Tags (comma-separated input)
- Creator Score (admin override 0-100)
- Quick Actions: Mark as Contacted, Mark as Replied, Mark as Interested, Mark as Meeting Scheduled, Mark as Negotiation, Mark as Onboarding, Mark as Active Creator, Mark as Rejected (with reason)
- Audit dates (all date_* fields, read-only)

**Modals**:
- Log Outreach: date picker, method dropdown (email/telegram/twitter/discord/linkedin/other), notes textarea
- Quick Status Change: confirm and update status + relevant date field automatically

**4. Discovery (`renderDiscovery()`)**:
- Title: "Add Trader"
- Two tabs:
  - **Manual Entry**: Form with required fields (name, platform, profile_url, optional performance metrics, scoring)
  - **Quick Paste**: Textarea for bulk paste (like old Telegram parser but generic) → parse basic fields → create trader
- Save button creates trader via API

**5. Settings (`renderSettings()`)**:
- **Scoring Weights**: 6 sliders (0.0-3.0) with reset to defaults (all 1.0)
- **Platforms**: List of enabled platforms with toggles (from `platforms.enabled` setting)
- **Data Management**: Export/Import/Clear/Load Sample Data

### JavaScript Refactor

**Wrap entire script in IIFE** to avoid globals.

**State object**:
```javascript
const state = {
  currentPage: 'dashboard',
  selectedTraderId: null,
  filters: { status: 'all', platform: 'all', minFit: 0, search: '' },
  sort: 'date_desc',
  traders: [],
  settings: {},
  lastSeenTraderId: null
};
```

**API object**:
```javascript
const API = {
  async getTraders(params) { return api('/api/traders?' + new URLSearchParams(params)); },
  async getTrader(id) { return api('/api/traders/' + id); },
  async createTrader(data) { return api('/api/traders', {method: 'POST', body: JSON.stringify(data)}); },
  async updateTrader(id, data) { return api('/api/traders/' + id, {method: 'PUT', body: JSON.stringify(data)}); },
  async deleteTrader(id) { return api('/api/traders/' + id, {method: 'DELETE'}); },
  async getStats() { return api('/api/traders/stats'); },
  async logOutreach(id, data) { return api('/api/traders/' + id + '/outreach', {method: 'POST', body: JSON.stringify(data)}); },
  async getSettings() { return api('/api/settings'); },
  async saveSettings(data) { return api('/api/settings', {method: 'PUT', body: JSON.stringify(data)}); }
};
```

**Utils**:
- `platformColor(platform)` - returns CSS var
- `statusColor(status)` - returns color name
- `fitScoreColor(score)` - red <50, yellow <70, green >=70
- `formatDate()`, `formatRelativeTime()`

**Refactor existing render functions** to use state and API.

### Parser Refactor

Keep `parser.py` but rename `parse_telegram_message()` → `parse_trader_profile()` and make it generic. It should extract trader_name, platform (if detectable from context), location, social links, basic metrics from any pasted text. Keep both Python (backend) and JavaScript (frontend) versions in sync. Used by Discovery page "Quick Paste" tab.

---

## SECTION 7: AI FEATURE DESIGN

**None. No AI. Removing all AI features.** ✓

---

## SECTION 8: IMPLEMENTATION ROADMAP

### Week 1: Backend Foundation

**Tasks**:
1. Create `migrations/001_create_traders.sql` with full schema + indexes
2. Rename `jobs` table functions in `database.py`:
   - `create_job()` → `create_trader()`
   - `get_jobs()` → `get_traders()` (accept new filters)
   - `get_job()` → `get_trader()`
   - `update_job()` → `update_trader()` (recalc fit_score)
   - `delete_job()` → `delete_trader()`
   - Update all SQL: `jobs` → `traders`, field names
   - Add `calculate_fit_score(trader, weights)` helper
   - Add `get_stats()` function returning:
     ```python
     {
       'total': count,
       'active_pipeline': count,
       'total_outreach': sum(outreach_attempts),
       'reply_rate': replied / contacted,
       'by_status': {status: count, ...},
       'by_platform': {platform: count, ...},
       'conversion_rate': active_creators / total
     }
     ```
3. Add `log_outreach(trader_id, method, notes)` - append to `research_notes` with timestamp
4. Update `main.py`:
   - Rename all routes: `/api/jobs` → `/api/traders`
   - Add `GET /api/traders/stats` → returns `get_stats()`
   - Add `POST /api/traders/{id}/outreach` → calls `log_outreach()` then updates `outreach_attempts++`, `last_contact_date`
   - Remove `/api/jobs/{id}/resume` routes
   - Remove `bot.py` import and startup code
   - Update request handlers to use trader schema
   - Update `_deserialize_json_fields()` for trader fields
5. Delete `bot.py` file
6. Delete `ai.py` file or keep minimal (but not used)
7. Add default settings keys in `init_db()`:
   ```sql
   INSERT OR IGNORE INTO settings (key, value) VALUES
   ('scoring_weights.audience_strength', '1.0'),
   ('scoring_weights.trading_consistency', '1.0'),
   ...
   ('platforms.enabled', '["Manual","Telegram","eToro","MQL5","TradingView","ZuluTrade","Myfxbook","Darwinex","NAGA","FXBlue","Twitter","Discord"]');
   ```
8. Test with Swagger: CRUD works, stats returns dict, outreach logs correctly.

**Success criteria**: All trader CRUD working, stats endpoint, settings have defaults.

---

### Week 2: Frontend Core

**Tasks**:
1. Update `design-system.css`:
   - Add platform brand color variables (12 platforms)
   - Add score bar component styles
   - Add status colors for 11 statuses
2. Refactor `index.html` JavaScript:
   - Wrap in IIFE
   - Extract `state` object
   - Extract `API` object
   - Extract `Utils` (platformColor, statusColor, formatDate, etc.)
   - Ensure no globals leaked
3. Update `renderDashboard()`:
   - Replace all job metrics with trader metrics
   - Build funnel chart (CSS horizontal bars, calculate percentages)
   - Build platform breakdown (iterate `by_platform` from stats)
   - Build recent high-priority list (fit_score >= 70)
   - Show reply rate percentage
4. Update `renderTraders()`:
   - Add platform filter (dropdown from `settings.platforms.enabled`)
   - Add min fit score slider
   - Update columns: platform badge, name, fit score bar, status pill, last contact, outreach count
   - Update search to include name, profile_url, notes, tags
   - Implement quick action: "Log outreach" button per row → opens modal, POSTs to outreach endpoint
   - Implement quick status advance (dropdown per row): when changed, PATCH trader with new status + set appropriate date field
5. Update `renderTraderDetail()`:
   - Full two-column layout
   - Left: header + basic info + performance (read-only) + social links + scoring sliders (6) + fit score display + outreach log + timeline
   - Right: research notes + tags + creator score + quick action buttons + audit dates
   - Implement outreach logging modal: date (default now), method dropdown, notes → POST /outreach → refresh trader data
   - Implement all quick action buttons: each sets status + auto-fills relevant date field + saves
   - Update all input bindings to trader fields
   - Add fit score live preview when sliders change (without save)
6. Update `renderDiscovery()` (rename from Inbox):
   - Change "Telegram Parser" tab to "Quick Paste"
   - Keep parser but output trader fields
   - Add "Manual Entry" tab with form
   - On save, POST `/api/traders`
7. Update `renderSettings()`:
   - Remove AI section
   - Add Scoring Weights: 6 sliders (1.0 default, range 0-3), show example "With all sliders at 1.5, fit score = average × weight"
   - Load weights from settings, save on change
   - Add Platforms section: list enabled platforms with toggles (checkboxes), save to `platforms.enabled`
   - Keep export/import/clear/sample data but for traders
8. Update `api()` calls:
   - Change paths from `/api/jobs` to `/api/traders`
   - Add calls to `/api/traders/stats`, `/api/traders/{id}/outreach`
   - Update polling to fetch traders, compare `lastSeenTraderId`
9. Update navigation: "Jobs" → "Traders", "Inbox" → "Discovery"
10. Load sample data feature:
    - Create `sample_data/sample_traders.json` with 5-10 diverse traders
    - "Load Sample" button: DELETE all traders, POST all sample traders
    - Show confirmation dialog first

**Testing**:
- End-to-end: Dashboard shows stats, Traders list shows sample data (after load), Detail edit saves, Outreach logging works, Settings weights persist.
- Responsive: Check mobile layout of trader detail (stack columns)

**Success criteria**: Complete UI transformation with all trader features working. Sample data loads.

---

### Week 3: Polish & Deployment

**Tasks**:
1. Input validation:
   - Add checks: `profile_url` must be valid URL if provided, scores 0-10, dates valid ISO
   - Show error messages in UI if API returns 400
2. Error handling:
   - Add try/catch in API calls, show toasts on failure
   - Handle 404 on trader not found
3. Security (basic):
   - Add `uvicorn` config: `host="0.0.0.0"`, `port=8000`
   - Document that this is local/trusted network only (no auth)
4. Dockerize:
   - Create `Dockerfile`:
     ```dockerfile
     FROM python:3.11-slim
     WORKDIR /app
     COPY requirements.txt .
     RUN pip install -r requirements.txt
     COPY . .
     CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
     ```
   - Create `docker-compose.yml` (optional but nice):
     ```yaml
     version: '3.8'
     services:
       trader-crm:
         build: .
         ports:
           - "8000:8000"
         volumes:
           - ./data:/app/data
         # No environment variables needed (no Telegram, no AI)
     ```
   - Update `.dockerignore` (exclude `jobs.db`, `resumes/`, `__pycache__`)
5. README updates:
   - What it is (Trader Acquisition CRM)
   - How to run: `python main.py` or `docker-compose up`
   - How to access: http://localhost:8000
   - Data stored in `traders.db` (SQLite)
   - No dependencies beyond requirements.txt
6. GitHub actions (optional): None needed, just push code.
7. Sample data script: `scripts/load_sample_data.py` that inserts 5-10 traders with varied platforms, scores, statuses.
8. Remove Telegram bot references from code entirely.
9. Update UI strings: "Job" → "Trader", "Application" → "Outreach", etc.
10. Final testing: all CRUD, import/export, settings save, sample data load, reset.

**Success criteria**: `docker build` works, app runs in browser, all features functional, clean codebase ready for GitHub.

---

## SECTION 9: FILE CHANGES SUMMARY

### Files to Modify

| File | Changes |
|------|---------|
| `database.py` | Rename functions, update SQL to `traders`, add `calculate_fit_score()`, `get_stats()`, `log_outreach()` |
| `main.py` | Rename routes, add `/stats` and `/outreach` endpoint, remove resume routes, remove bot import, update handlers |
| `parser.py` | Optional: adapt to trader output (keep for Discovery Quick Paste) |
| `index.html` | Complete rewrite of render functions for trader schema, add state/API objects, update all UI |
| `design-system.css` | Add platform colors, score bar styles, new status pill colors |
| `requirements.txt` | No changes |
| `.env` | Remove `TELEGRAM_BOT_TOKEN` (optional, can keep but unused) |
| `jobs.db` | Delete, replaced by `traders.db` |

### Files to Delete

| File | Reason |
|------|--------|
| `bot.py` | Telegram bot no longer needed |
| `ai.py` | No AI features |
| `resumes/` directory (if exists) | Not using file attachments |

### Files to Create

| File | Purpose |
|------|---------|
| `migrations/001_create_traders.sql` | Database migration |
| `sample_data/sample_traders.json` | Demo dataset (5-10 traders) |
| `Dockerfile` | Container build |
| `docker-compose.yml` | Easy local run |
| `scripts/load_sample_data.py` | Python script to load sample data |
| `README.md` (updated) | Documentation |

### Optional Files (if keeping parser)

| File | Changes |
|------|---------|
| `parser.py` | Rename `parse_telegram_message()` output fields: role_title → trader_name, company_name → omit, add platform="Telegram" if detected |

---

## SECTION 10: TECHNICAL DECISIONS

1. **No AI**: Manual scoring only. Users fill 6 sliders themselves. Fit score calculated automatically from those 6.
2. **No Telegram bot**: Manual entry only. Email/DM sending is manual - we just log what was sent.
3. **Outreach logging**: Append timestamped entry to `research_notes` OR create separate `outreach_logs` table. **Decision**: Separate `outreach_logs` table for clean history.
4. **Sample data**: Small set (5-10 traders) with varied platforms (eToro, MQL5, Manual), statuses, and scores. Realistic but fake.
5. **Deployment**: Dockerfile + docker-compose. Also supports `python main.py` directly.
6. **Platform brand colors**: Hardcode 12 platforms in CSS. Simple, no dynamic loading.
7. **Scoring weights**: 6 sliders (0.0-3.0) in settings, default 1.0 each. Fit score = weighted average × 100/10.
8. **Timeline feature**: Removed - not needed for this version
9. **Duplicate detection**: `profile_url` must be unique. If user tries to create duplicate, return 409 Conflict. (Simple approach)
10. **File attachments**: Not included. Keep it simple.

---

## SECTION 11: TESTING CHECKLIST

- [ ] `GET /api/traders` returns list
- [ ] `POST /api/traders` creates new trader, sets date_added
- [ ] `PUT /api/traders/{id}` updates fields, recalculates fit_score, sets date_updated
- [ ] `DELETE /api/traders/{id}` removes trader
- [ ] `GET /api/traders/stats` returns correct dict
- [ ] `POST /api/traders/{id}/outreach` appends to outreach_logs table, increments outreach_attempts, updates last_contact_date
- [ ] Import/Export roundtrip works with traders
- [ ] Dashboard shows correct funnel percentages
- [ ] Settings weights saved and applied
- [ ] Platform toggles work
- [ ] Sample data loads without errors
- [ ] UI responsive on mobile
- [ ] `docker-compose up` starts app
- [ ] No AI or Telegram bot code remains

---

## SECTION 12: APPROVAL & EXECUTION

This plan is **ready**. It removes all complexity:
- No AI
- No external APIs
- Simple scoring
- Outreach logging only
- Sample data included
- GitHub-ready with Docker

**Next**: Ready to create detailed TDD task breakdown and execute.

Do you approve this simplified plan? Any last tweaks before I start writing the detailed implementation tasks?

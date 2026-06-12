# Trader Acquisition CRM Transformation Plan

> **Status**: Strategic Design Document - Awaiting Approval
> **Objective**: Transform Job Application CRM into Trader Acquisition CRM for DeFi copy-trading marketplace
> **Date**: 2025-06-09

---

## EXECUTIVE SUMMARY

This document provides a comprehensive plan to transform the existing Job Application CRM into a Trader Acquisition CRM. The transformation involves:

- **Data Model**: Replace job-centric tables with trader-centric profiles
- **Workflow**: Redefine pipeline stages for trader recruitment
- **UI**: Adapt all pages, forms, and dashboards for trader management
- **AI**: Expand from simple keyword matching to sophisticated trader analysis and outreach generation
- **Scalability**: Prepare for multi-platform data ingestion and automated discovery

---

## SECTION 1: CURRENT ARCHITECTURE REVIEW

### 1.1 Overall Architecture

The current system is a monolithic Python FastAPI backend with an embedded vanilla JavaScript frontend. It uses SQLite for persistence and operates as a local-only application with no authentication. The architecture is simple but effective for a single-user desktop CRM.

**Key Characteristics**:
- Single-file frontend (`index.html`, 1,165 lines) with manual SPA routing
- Async backend with clean separation: `main.py` (API), `database.py` (DAL), `parser.py` (Telegram parsing), `ai.py` (heuristics), `bot.py` (Telegram integration)
- SQLite database with `jobs` table and `settings` key-value store
- No migrations - schema created on startup with `CREATE TABLE IF NOT EXISTS`
- No tests, no validation layer, no authentication

### 1.2 Current Data Model

The `jobs` table centers around **job postings** with:
- Core fields: `role_title`, `company_name`, `location`, `salary`, `job_type`, `apply_link`
- Workflow: `status` (7 values), `stage_reached` (4 values), dates
- Scoring: `fit_score`, `interest_score`, `priority_score` (product)
- Application tracking: `resume_path`, `cover_letter`, `response_received`
- AI analysis: `ai_summary`, `ai_requirements`, `ai_fit` (JSON strings)
- Source tracking: `source` (default 'Telegram'), `raw_message`

### 1.3 Current Workflow

```
Job Found → Research → Applied → Interview → Offer → Rejected
```

Statuses: New → Reviewing → Will Apply → Applied → Interviewing → Offer → Rejected

This linear hiring flow is inappropriate for trader recruitment, which requires:
- Multi-touch outreach
- Relationship building
- Negotiation phase
- Onboarding complexity
- Ongoing creator management

### 1.4 Current AI Implementation

The existing `ai.py` uses simplistic keyword-based heuristics:
- `generate_summary()`: Scores lines based on position and keywords, extracts top 3
- `analyze_fit()`: Token matching between job description and base resume, calculates overlap ratio

This is **not true AI** - it's rule-based text processing. For trader acquisition, we need:
- LLM integration for profile analysis
- Outreach message generation
- Negotiation intelligence
- Meeting preparation

### 1.5 Current Frontend Components

**Pages** (all in `index.html`):
1. Dashboard - metrics, status chart, recent jobs
2. Jobs - list with filters, search, sort
3. Job Detail - full editing, AI analysis, resume upload
4. Inbox - Telegram parser with preview
5. Settings - base resume, import/export

**Components** (inline, not modular):
- Sidebar with navigation and stats
- Job cards with avatars, priority dots, status pills
- Job detail form with sliders, fields, sections
- Modal dialogs (toasts, confirmations)
- Parser preview form

**State Management**: Global variables, no reactivity system

### 1.6 Technical Strengths to Preserve

- Clean async architecture
- Separation of concerns (DB, API, parser, AI)
- Polished Apple-inspired design system
- Comprehensive API coverage
- Telegram integration pattern
- Client-side duplicate parser (useful for preview)

### 1.7 Technical Debt to Address

- No database migrations (schema changes will be manual)
- Parser logic duplicated (Python/JS)
- No input validation/sanitization
- No error handling
- Global state management
- No authentication
- No unit tests
- Hardcoded localhost in Telegram bot
- Exposed Telegram token in `.env` (should have example)

---

## SECTION 2: REUSABLE COMPONENTS

### 2.1 Backend Infrastructure (KEEP AS-IS)

These components require minimal changes:

1. **FastAPI Server** (`main.py` structure)
   - Lifespan management pattern
   - Route organization
   - File upload handling
   - API response format

2. **Database Layer** (`database.py` pattern)
   - Async aiosqlite wrapper functions
   - Connection pooling via `get_db()`
   - CRUD operations
   - Settings key-value store pattern

3. **Telegram Bot Integration** (`bot.py`)
   - Message handler structure
   - Reply pattern with link to web UI
   - Background polling

4. **Settings Management**
   - Key-value store pattern
   - Bulk update endpoint
   - Base resume storage

5. **Import/Export System**
   - JSON export/import pattern
   - Data backup/restore

6. **File Upload Pattern**
   - Resume storage and retrieval
   - File validation (type, size)
   - Cleanup on delete

### 2.2 Frontend Infrastructure (REFACTOR)

These patterns should be preserved but modernized:

1. **Design System** (`design-system.css`)
   - Color palette (surface, raised, accent)
   - Typography (Inter, JetBrains Mono)
   - Status colors
   - Component styles (pills, cards, sliders)
   - Responsive breakpoints
   - **Action**: Extend with new trader-specific colors and components

2. **API Layer** (JavaScript `api()` function)
   - Fetch wrapper with error handling
   - Connection monitoring
   - **Action**: Keep pattern, add new endpoints

3. **Polling Mechanism**
   - `setInterval(pollNewJobs, 10000)`
   - `lastSeenJobId` comparison
   - Toast notifications
   - **Action**: Update to poll new traders instead of jobs

4. **Modal/Toast System**
   - Overlay and container patterns
   - Animation timing
   - **Action**: Reuse for trader-specific dialogs

5. **Filter/Sort UI Patterns**
   - Tab-based filters
   - Search input
   - Sort dropdown
   - **Action**: Adapt for trader fields

### 2.3 Parser Pattern (DUPLICATE -> SHARED)

Current: Parser logic duplicated in `parser.py` and JavaScript

**Proposed**: Create a shared parser module or ensure both implementations stay synchronized. For now, maintain both but document they must evolve together.

### 2.4 AI Heuristics Pattern (REPLACE)

Current: Local token matching

**Proposed**: Keep the interface (`generate_summary()`, `analyze_fit()`) but replace implementation with LLM calls. This maintains API compatibility while upgrading capabilities.

---

## SECTION 3: REQUIRED REFACTORS

### 3.1 Database Schema Transformation

**Strategy**: Rename and repurpose `jobs` table to `traders` with new fields. Preserve existing data by creating new table and optional migration script.

**Approach**:
1. Create new `traders` table with trader-specific schema
2. Optionally migrate existing `jobs` data (as historical reference) or archive it
3. Update all database queries to use `traders` table
4. Update foreign keys if any (none currently exist)

**Why not alter table**: Clean slate avoids column bloat and confusion. Old job data can be kept in separate `jobs_archive` table if needed for reference.

### 3.2 API Renaming and Evolution

**Strategy**: Rename `/api/jobs/*` to `/api/traders/*`. Keep old endpoints temporarily for backward compatibility (return 410 Gone) if any external integrations exist.

**New endpoints to add**:
- POST `/api/traders/{id}/score` - update scoring
- POST `/api/traders/{id}/outreach` - log outreach attempt
- GET `/api/traders/{id}/timeline` - get activity history
- POST `/api/traders/import/{platform}` - platform-specific importers (future)

**Settings enhancements**:
- Add scoring weights configuration
- Add outreach templates
- Add platform-specific API keys (for future importers)

### 3.3 Frontend Page Transformations

**Page-by-page mapping**:

| Current Page | New Page | Changes Required |
|--------------|----------|------------------|
| Dashboard | Dashboard | Replace job metrics with trader acquisition metrics |
| Jobs List | Traders List | Change columns, filters, styling |
| Job Detail | Trader Detail | Complete form redesign with trader fields |
| Inbox | Discovery/Import | Parser becomes one of many import sources |
| Settings | Settings | Add AI config, scoring weights, templates |

### 3.4 State Management Refactor

**Current**: Global `let` variables

**Proposed**: Simple state object with change events:

```javascript
const state = {
  currentPage: 'dashboard',
  selectedTraderId: null,
  filters: { status: 'all', search: '', platform: 'all' },
  sort: 'date_desc'
};

function setState(updates) {
  Object.assign(state, updates);
  render();
}
```

**Why**: Prevents inconsistent state during rapid updates, enables computed values, easier testing.

### 3.5 Code Organization Refactor

**Current**: All code in one HTML file

**Proposed**: Keep single file (to maintain simplicity) but clearly separate sections with comments:
- State management
- API layer
- Page render functions
- Component render functions
- Event handlers
- Utility functions

**Alternative (if acceptable)**: Split into multiple files for better maintainability, but this adds build complexity. Recommend staying with single file for now.

### 3.6 Parser Logic Synchronization

**Current**: Two separate implementations

**Action**: Document that both `parser.py` and client-side parser must be updated together. Extract common regex patterns to shared constants if we split frontend later.

---

## SECTION 4: DATABASE MIGRATION PLAN

### 4.1 New `traders` Table Schema

```sql
CREATE TABLE traders (
    -- Identity
    id TEXT PRIMARY KEY,
    trader_name TEXT NOT NULL,
    profile_url TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL DEFAULT 'Manual',
    location TEXT DEFAULT '',
    language TEXT DEFAULT '',

    -- Performance Metrics
    followers INTEGER DEFAULT 0,
    copiers INTEGER DEFAULT 0,
    assets_under_mangement REAL DEFAULT 0.0,
    monthly_return REAL DEFAULT 0.0,
    yearly_return REAL DEFAULT 0.0,
    maximum_drawdown REAL DEFAULT 0.0,
    risk_score INTEGER DEFAULT 0,  -- 1-10
    strategy_type TEXT DEFAULT '', -- 'Liquidity Pool', 'Copy Trading', 'Arbitrage', etc.

    -- Social Links
    twitter TEXT DEFAULT '',
    telegram TEXT DEFAULT '',
    discord TEXT DEFAULT '',
    youtube TEXT DEFAULT '',
    website TEXT DEFAULT '',

    -- Outreach Tracking
    contact_method TEXT DEFAULT '', -- 'email', 'telegram', 'twitter', 'discord'
    contact_info TEXT DEFAULT '',  -- actual contact address
    first_contact_date TEXT,
    last_contact_date TEXT,
    outreach_attempts INTEGER DEFAULT 0,

    -- Internal Scoring (configurable weights applied in UI)
    audience_strength INTEGER DEFAULT 0,  -- 1-10
    trading_consistency INTEGER DEFAULT 0, -- 1-10
    communication_quality INTEGER DEFAULT 0, -- 1-10
    crypto_knowledge INTEGER DEFAULT 0, -- 1-10
    likelihood_to_join INTEGER DEFAULT 0, -- 1-10
    brand_value INTEGER DEFAULT 0, -- 1-10
    fit_score INTEGER DEFAULT 0, -- calculated weighted total (0-100)
    priority_score INTEGER DEFAULT 0, -- fit × urgency factors
    creator_score INTEGER DEFAULT 0, -- admin override

    -- Notes & AI
    research_notes TEXT DEFAULT '',
    tags TEXT DEFAULT '', -- comma-separated
    ai_summary TEXT,
    ai_strengths TEXT,
    ai_weaknesses TEXT,
    ai_fit_assessment TEXT,
    ai_recommendations TEXT,
    ai_negotiation_risks TEXT,

    -- Workflow
    status TEXT DEFAULT 'Trader Found', -- see statuses below
    pipeline_stage TEXT DEFAULT 'Research', -- see stages below
    conversion_date TEXT, -- when became Active Creator
    rejection_date TEXT,
    rejection_reason TEXT DEFAULT '',

    -- Audit
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

**Valid statuses** (pipeline state):
- `Trader Found` - discovered, not yet evaluated
- `Researching` - actively researching profile
- `Contacted` - initial outreach sent
- `Replied` - responded positively
- `Interested` - expressed interest
- `Meeting Scheduled` - calendar invite sent
- `Negotiation` - in discussions
- `Onboarding` - completing setup
- `Active Creator` - successfully onboarded
- `Rejected` - explicitly declined
- `No Response` - no reply after multiple attempts

**Valid pipeline stages** (granular progress):
- `Research` - initial research phase
- `Outreach` - initial contact
- `Follow-up` - subsequent communications
- `Interview` - meeting/ interview completed
- `Due Diligence` - vetting phase
- `Contract` - agreement negotiation
- `Setup` - technical onboarding
- `Active` - live on platform
- `Closed` - final state (Rejected/Active)

**Indexes to add**:
```sql
CREATE INDEX idx_traders_platform ON traders(platform);
CREATE INDEX idx_traders_status ON traders(status);
CREATE INDEX idx_traders_fit_score ON traders(fit_score DESC);
CREATE INDEX idx_traders_date_added ON traders(date_added DESC);
CREATE INDEX idx_traders_last_contact ON traders(last_contact_date);
```

### 4.2 Migration Strategy

**Option A: Fresh Start (Recommended for MVP)**
1. Backup `jobs.db` as `jobs.archive.db`
2. Create new `traders` table
3. Start with empty dataset
4. Maintain old app as reference if needed

**Option B: Data Migration (If Historical Jobs Data is Critical)**
1. Create `jobs_archive` table with old schema
2. Move all existing `jobs` data to `jobs_archive`
3. Create new `traders` table
4. Optionally map some job fields to trader fields (but mapping is poor fit)

**Recommended**: Option A. Job applications are not traders. Fresh start with new data collection.

### 4.3 Database Migration Script

Create `migrations/001_initial_traders_schema.sql`:

```sql
-- Create traders table
CREATE TABLE IF NOT EXISTS traders (
    id TEXT PRIMARY KEY,
    trader_name TEXT NOT NULL,
    profile_url TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL DEFAULT 'Manual',
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
    fit_score INTEGER DEFAULT 0,
    priority_score INTEGER DEFAULT 0,
    creator_score INTEGER DEFAULT 0,
    research_notes TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    ai_summary TEXT,
    ai_strengths TEXT,
    ai_weaknesses TEXT,
    ai_fit_assessment TEXT,
    ai_recommendations TEXT,
    ai_negotiation_risks TEXT,
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_traders_platform ON traders(platform);
CREATE INDEX IF NOT EXISTS idx_traders_status ON traders(status);
CREATE INDEX IF NOT EXISTS idx_traders_fit_score ON traders(fit_score DESC);
CREATE INDEX IF NOT EXISTS idx_traders_date_added ON traders(date_added DESC);
CREATE INDEX IF NOT EXISTS idx_traders_last_contact ON traders(last_contact_date);

-- Settings table (keep existing, add new keys)
-- No changes needed - just add new keys via application
```

Update `database.py`:
1. Rename `create_job()` → `create_trader()`
2. Rename `get_jobs()` → `get_traders()`
3. Rename `get_job()` → `get_trader()`
4. Rename `update_job()` → `update_trader()`
5. Rename `delete_job()` → `delete_trader()`
6. Update field names in all functions
7. Add `get_setting()`/`set_setting()` for scoring weights
8. Keep same async patterns

### 4.4 Settings Schema Extensions

Add new keys to `settings` table:

| Key | Type | Description | Default |
|-----|------|-------------|---------|
| `scoring_weights.audience_strength` | float | Weight for audience score | 1.0 |
| `scoring_weights.trading_consistency` | float | Weight for consistency score | 1.0 |
| `scoring_weights.communication_quality` | float | Weight for comms score | 1.0 |
| `scoring_weights.crypto_knowledge` | float | Weight for crypto knowledge | 1.0 |
| `scoring_weights.likelihood_to_join` | float | Weight for join probability | 1.0 |
| `scoring_weights.brand_value` | float | Weight for brand value | 1.0 |
| `outreach_templates.linkedin` | text | LinkedIn message template | "" |
| `outreach_templates.twitter_dm` | text | Twitter DM template | "" |
| `outreach_templates.email` | text | Email template | "" |
| `outreach_templates.telegram` | text | Telegram message template | "" |
| `platforms.enabled` | JSON list | Which platforms are tracked | ["Manual"] |
| `ai.enabled` | boolean | Whether AI features are enabled | true |
| `ai.provider` | string | "heuristic" or "openai" or "anthropic" | "heuristic" |
| `ai.api_key` | string | API key for LLM provider | "" |
| `pipeline.show_archived` | boolean | Show rejected in lists | false |

---

## SECTION 5: BACKEND CHANGES

### 5.1 New API Endpoints (Trader Management)

All existing job endpoints to be renamed and adapted.

**New/modified endpoints**:

| Method | Path | Handler | Changes |
|--------|------|---------|---------|
| GET | `/api/traders` | `list_traders()` | Accept new filters: `platform`, `status`, `pipeline_stage`, `min_fit_score`, `max_risk_score` |
| GET | `/api/traders/{id}` | `get_trader()` | Return trader object with all new fields |
| POST | `/api/traders` | `create_trader()` | Accept trader fields, generate ID, set `date_added`, `date_updated` |
| PUT | `/api/traders/{id}` | `update_trader()` | Update fields, set `date_updated`, recalc `priority_score` |
| DELETE | `/api/traders/{id}` | `delete_trader()` | Delete trader, cleanup attachments if any |
| POST | `/api/traders/{id}/outreach` | `log_outreach()` | New: increment `outreach_attempts`, update `last_contact_date`, add to notes |
| GET | `/api/traders/{id}/timeline` | `get_timeline()` | New: return chronological activity log |
| POST | `/api/traders/{id}/score` | `update_scores()` | New: update scoring fields, calculate weighted `fit_score` |
| GET | `/api/traders/stats` | `get_stats()` | New: dashboard metrics (counts by status, platform breakdown, conversion rates) |

**Resume-like attachments**: Future consideration for trader onboarding documents. For now, no file upload per trader. If needed, pattern from jobs can be reused.

### 5.2 AI Endpoint Enhancements

**Existing**:
- POST `/api/jobs/{id}/ai-summary` → `run_ai_summary()`
- POST `/api/jobs/{id}/ai-fit` → `run_ai_fit()`

**New/modified**:

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | `/api/traders/{id}/ai-analyze` | `analyze_trader()` | New comprehensive analysis: summary, strengths, weaknesses, fit assessment, recommendations, negotiation risks |
| POST | `/api/traders/ai-outreach` | `generate_outreach()` | New: generate personalized outreach message based on trader profile and selected template |
| POST | `/api/traders/ai-meeting-prep` | `prepare_meeting()` | New: generate meeting prep doc (summary, discussion points, suggested offer) |
| POST | `/api/traders/{id}/ai-renegotiate` | `analyze_objections()` | New: analyze objections and suggest counter-arguments |

**Implementation strategy**:

1. **Phase 1**: Keep heuristic AI but extend it to trader fields
   - Reuse `ai.py` functions with new prompts
   - Simulate LLM output with templates

2. **Phase 2**: Integrate LLM API (OpenAI/Anthropic)
   - Add `ai.provider` and `ai.api_key` to settings
   - Create `llm_client.py` module
   - Update AI functions to call LLM if configured, else fallback to heuristics

3. **Prompt engineering**: Craft system prompts for each AI function that take trader profile as input.

**Settings needed**:
- `ai.provider` = "openai", "anthropic", "heuristic"
- `ai.api_key` = stored securely
- `ai.model` = "gpt-4-turbo", "claude-3-opus", etc.
- `ai.max_tokens` = 1000
- `ai.temperature` = 0.7

### 5.3 Import/Export Enhancements

**Existing**:
- GET `/api/export` - export all jobs as JSON
- POST `/api/import` - import jobs from JSON

**New**:
- Keep same endpoints but work with `traders` table
- Add platform-specific import format adapters (future)
- Add validation: `profile_url` must be unique per platform

### 5.4 Settings Endpoint Extensions

**New settings keys** (see Section 4.4):
- Scoring weights
- Outreach templates
- Platform enablement
- AI configuration

Endpoint remains: GET `/api/settings` and PUT `/api/settings`

### 5.5 Database Layer Refactor (`database.py`)

**Changes**:
1. Rename all `job*` functions to `trader*`
2. Update all SQL queries from `jobs` to `traders`
3. Update field mapping dictionaries
4. Add helper: `calculate_priority_score(trader)` - weighted sum of scored fields
5. Add helper: `apply_scoring_weights(scores, weights)` - reads from settings
6. Add function: `get_distinct_platforms()` - for filter dropdowns
7. Add function: `get_trader_by_profile_url(platform, url)` - deduplication
8. Add transaction support for bulk operations (future)

**Keep same patterns**:
- Async/await
- aiosqlite connection management
- JSON serialization for complex fields
- Timestamp auto-generation

### 5.6 ID Generation

**Current**: `f"{int(time.time()):x}{random.randbytes(3).hex()}"`

**Keep this pattern**. IDs should remain opaque strings.

### 5.7 File Structure Changes

Add migration directory:
```
migrations/
  001_initial_traders_schema.sql
```

Add LLM client (future):
```
llm_client.py
  - class LLMProvider (base)
  - class OpenAIProvider
  - class AnthropicProvider
  - function generate_analysis(profile)
  - function generate_outreach(profile, template_type)
```

---

## SECTION 6: FRONTEND CHANGES

### 6.1 Design System Extensions

Add to `design-system.css`:

**New color tokens**:
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

**New component styles**:
- Platform badges with brand colors
- Score breakdown bars (1-10 scales)
- Timeline component for activity history
- Outreach log entry cards

### 6.2 Dashboard Page (`renderDashboard()`)

**Replace metrics**:

| Current (Jobs) | New (Traders) |
|----------------|---------------|
| Total jobs | Total Traders |
| New + Reviewing | Active Pipeline (excluding Active Creator & Rejected) |
| Applications sent | Outreach Attempts Total |
| Response rate | Reply Rate (Replied / Contacted) |

**New charts**:

1. **Pipeline Funnel** (horizontal bar chart)
   - Trader Found → Researching → Contacted → Replied → Interested → Meeting Scheduled → Negotiation → Onboarding → Active Creator
   - Show counts and drop-off rates

2. **Platform Distribution** (pie/bar)
   - Count by platform (eToro, MQL5, etc.)
   - Color-coded by platform brand

3. **Conversion Metrics**
   - Contact → Reply rate
   - Reply → Interested rate
   - Interested → Meeting rate
   - Meeting → Active rate
   - Overall conversion (Found → Active)

4. **Recent High-Priority Traders** (list)
   - Traders with `fit_score >= 80` or `priority_score >= threshold`
   - Show name, platform, fit score, status

5. **Activity Timeline** (mini line chart)
   - Traders added over time (last 30 days)
   - Overlay with conversions

### 6.3 Traders List Page (`renderTraders()`)

**Filter changes**:

| Filter | Options |
|--------|---------|
| Status | Trader Found, Researching, Contacted, Replied, Interested, Meeting Scheduled, Negotiation, Onboarding, Active Creator, Rejected, No Response, All |
| Pipeline Stage | Research, Outreach, Follow-up, Interview, Due Diligence, Contract, Setup, Active, Closed, All |
| Platform | Dynamic from DB: eToro, MQL5, Myfxbook, ZuluTrade, Darwinex, NAGA, TradingView, FXBlue, Telegram, Twitter, Discord, Manual, All |
| Min Fit Score | 0-100 slider |
| Max Risk Score | 0-10 slider |

**Search**: Search `trader_name`, `profile_url`, `research_notes`, `tags`

**Sort options**:
- `date_added_desc` (default)
- `date_added_asc`
- `fit_score_desc`
- `priority_score_desc`
- `last_contact_date_desc`

**Columns**:
- Trader name (with platform badge)
- Platform badge (brand color)
- Fit score (0-100, colored: red<50, yellow<70, green≥70)
- Status pill
- Last contact (relative time)
- Outreach attempts count

**Row actions**: Click to open detail, Quick status advance, Quick contact log

### 6.4 Trader Detail Page (`renderTraderDetail()`)

**Layout**: Two-column responsive grid

**Left Column (3/4)**:

1. **Header Section**
   - Trader name (large, editable)
   - Platform badge (editable dropdown)
   - Profile URL (clickable, editable)
   - Status dropdown
   - Pipeline stage dropdown
   - Fit score visualization (gauge or progress bar 0-100)

2. **Basic Information Card**
   - Location (editable)
   - Language (editable)
   - Strategy type (editable dropdown)
   - Contact method (editable)
   - Contact info (editable, masked for privacy)

3. **Performance Metrics Card** (grid 2x4)
   - Followers (number input)
   - Copiers (number input)
   - AUM (assets under management) (currency input)
   - Monthly return (%) (number with ±)
   - Yearly return (%) (number with ±)
   - Max drawdown (%) (number)
   - Risk score (1-10 slider)
   - Trading consistency (1-10 slider) - separate from risk

4. **Social Links Card** (grid 2x3)
   - Twitter URL
   - Telegram link/invite
   - Discord invite
   - YouTube channel
   - Website
   - Other

5. **Scoring Card**
   - Audience strength (1-10 slider) - based on followers/reach
   - Communication quality (1-10 slider) - based on interactions
   - Crypto knowledge (1-10 slider) - subjective assessment
   - Likelihood to join (1-10 slider) - prediction
   - Brand value (1-10 slider) - reputation assessment
   - Creator score (1-100 slider) - admin override/override fit
   - **Auto-calculated**: Fit score (weighted sum of above, 0-100)
   - **Auto-calculated**: Priority score (fit × urgency factor)

   *Note: Show formula and weights from settings*

6. **Activities & Outreach Log**
   - List of outreach attempts with date, method, notes
   - Form to log new outreach: date, method, notes, outcome
   - Show timeline of status changes

7. **Meeting Preparation** (if Meeting Scheduled)
   - Button: "Generate Meeting Prep"
   - Display AI-generated summary, discussion points, suggested offer

**Right Column (1/4 or sidebar)**:

1. **Research Notes**
   - Large textarea (auto-expand)
   - Rich text? Plain text for now

2. **Tags**
   - Token input: Add/remove tags
   - Common tags dropdown: 'KOL', 'Influencer', 'Quant', 'DeFi', 'NFT', 'High Risk', 'Low Risk', 'Quick Flip', 'Long-term'

3. **AI Analysis Buttons**
   - "Analyze Profile" → populates ai_summary, ai_strengths, ai_weaknesses, ai_fit_assessment, ai_recommendations
   - "Analyze Negotiation" → populates ai_negotiation_risks
   - "Generate Outreach" → opens modal to select template type

4. **AI Results Display** (collapsible sections)
   - Summary
   - Strengths
   - Weaknesses
   - Fit Assessment
   - Recommendations
   - Negotiation Risks

5. **Action Buttons**
   - Advance status (→ next)
   - Mark as Active Creator
   - Mark as Rejected (with reason)
   - Schedule Meeting (opens calendar modal)
   - Send Outreach (integrates with outreach generator)

6. **Audit Fields** (read-only, collapsible)
   - Date added
   - Date updated
   - Dates for each pipeline milestone
   - Active creator date
   - Rejection date

**Modal Dialogs**:

1. **Outreach Generator Modal**
   - Select template: LinkedIn, Twitter DM, Email, Telegram
   - Preview generated message
   - Edit before sending
   - Send button → logs outreach + updates `last_contact_date`, `outreach_attempts`, `status` (if first contact)

2. **Meeting Scheduler Modal**
   - Date/time picker
   - Meeting link (Zoom/Google Meet/Telegram)
   - Agenda notes
   - Save → updates `date_meeting_scheduled`, `status` → "Meeting Scheduled"

3. **Quick Contact Log Modal**
   - Method: Email/Telegram/Twitter/Discord/Other
   - Notes
   - Outcome: No response / Positive / Negative / Maybe
   - Based on outcome, suggest status updates

### 6.5 Settings Page Changes

**Sections**:

1. **AI Configuration**
   - Provider dropdown: Heuristic / OpenAI / Anthropic
   - API key input (masked)
   - Model selection (based on provider)
   - Temperature slider
   - Test connection button

2. **Scoring Weights**
   - Six sliders (0-5): Audience strength, Trading consistency, Communication quality, Crypto knowledge, Likelihood to join, Brand value
   - Sum should equal certain value? No, flexible weighted sum
   - Reset to defaults button
   - Example: "Current trader with all 5s would have fit_score = Σ(score × weight)"

3. **Outreach Templates**
   - 4 textareas with rich placeholders:
     - `{{trader_name}}`
     - `{{platform}}`
     - `{{strategy_type}}`
     - `{{followers}}`
     - `{{monthly_return}}`
     - `{{summary}}`
   - Preview button (with sample data)
   - Save templates

4. **Platform Management**
   - List of enabled platforms with toggle switches
   - Add custom platform button (for future importers)
   - Reorder priority (drag-and-drop if feasible, otherwise up/down)

5. **Data Management** (same as before but traders)
   - Export traders (JSON)
   - Import traders (JSON)
   - Clear all data (with confirmation)
   - Load sample data (for demos)

6. **Stats**
   - Total traders
   - Database size
   - Traders per platform
   - Avg fit score
   - Conversion rate

### 6.6 Inbox Page Transformation

**Rename to "Discovery" or "Import"**

**Purpose**: Central place to add traders from various sources

**Current**: Telegram parser only

**New**:

1. **Source Selector** (tabs or cards)
   - Telegram Message (existing parser)
   - Manual Entry
   - CSV Import (future)
   - Platform API Import (future - disabled until built)

2. **Telegram Parser** (keep existing but adapt output)
   - Input textarea
   - Parse & Preview button
   - Preview shows trader fields (not job fields)
   - Quick Add button → `POST /api/traders`
   - Pre-fill: platform="Telegram", source="Telegram", date_added=now

3. **Manual Entry Form**
   - Form with all required trader fields
   - Save directly to API

4. **CSV Import** (future, placeholder UI)
   - File upload
   - Template download
   - Map columns to fields

5. **Platform Importers** (future, placeholder UI)
   - Cards for each platform: eToro, MQL5, etc.
   - "Connect" button → OAuth flow placeholder

**Note**: Keep Telegram parser exactly as-is for MVP but output trader schema.

### 6.7 Navigation Updates

**Sidebar**:
- Dashboard
- Traders (replace "Jobs")
- Discovery (replace "Inbox")
- Settings
- Theme toggle (keep)

**Badge counts**:
- Dashboard: Total traders
- Traders: Filtered count (e.g., Active Pipeline)
- Discovery: Quick add (no count)

### 6.8 JavaScript Refactor Plan

**Current state**: All code in global scope in `index.html`

**Refactor steps**:

1. **Wrap in IIFE or module pattern** to avoid global namespace
2. **Extract state object**:

```javascript
const state = {
  currentPage: 'dashboard',
  selectedTraderId: null,
  filters: {
    status: 'all',
    pipelineStage: 'all',
    platform: 'all',
    minFitScore: 0,
    maxRiskScore: 100,
    search: ''
  },
  sort: 'date_added_desc',
  traders: [], // cache
  lastSeenTraderId: null,
  serverConnected: true,
  settings: {}
};
```

3. **Create render functions per page**:
   - `renderDashboard()`
   - `renderTradersList()`
   - `renderTraderDetail()`
   - `renderDiscovery()`
   - `renderSettings()`

4. **Create component functions**:
   - `TraderCard(trader)`
   - `TraderRow(trader)`
   - `PlatformBadge(platform)`
   - `StatusPill(status)`
   - `ScoreGauge(score)`
   - `TimelineEntry(entry)`

5. **Event handlers**:
   - `handleNavigation(page)`
   - `handleFilterChange(filter, value)`
   - `handleSortChange(sort)`
   - `handleSearch(query)`
   - `handleTraderSelect(id)`
   - `handleTraderSave(updates)`
   - `handleOutreachGeneration(traderId, template)`

6. **API layer** (extract to separate object):

```javascript
const API = {
  async getTraders(params) { ... },
  async getTrader(id) { ... },
  async createTrader(data) { ... },
  async updateTrader(id, data) { ... },
  async deleteTrader(id) { ... },
  async getStats() { ... },
  async getSettings() { ... },
  async saveSettings(settings) { ... },
  async generateOutreach(traderId, template) { ... },
  async analyzeTrader(traderId) { ... }
};
```

7. **Utilities**:
   - `formatDate()`, `formatRelativeTime()`
   - `platformColor(platform)` - returns CSS variable
   - `statusConfig(status)` - returns color, label
   - `calculateFitScore(trader, weights)` - client-side preview
   - `parseTelegramMessage(text)` - move outside render function

8. **Remove duplicate parser**: Extract the client-side parser to a function `parseTelegramMessage(text)` and call from both Inbox page and any other place. Keep in sync with `parser.py`.

### 6.9 Adaptive UI Patterns

**Responsive grid adjustments**:
- Dashboard: 1 → 2 → 4 columns for stat cards
- Trader detail: Single column on mobile, split 50/50 on desktop
- Lists: Full width on mobile, add sidebar filters on desktop (>1024px)

**Platform brand colors**: Map platform names to CSS color variables (see 6.1). If platform not in map, use `--platform-manual`.

**Status pills**: Keep existing style but add new statuses. Map each status to color:
- Trader Found: gray
- Researching: blue
- Contacted: cyan
- Replied: teal
- Interested: green
- Meeting Scheduled: yellow
- Negotiation: orange
- Onboarding: purple
- Active Creator: green (bold)
- Rejected: red
- No Response: gray (outline)

### 6.10 Empty States

Add missing empty states:
- No traders found (illustration + message)
- No AI analysis yet (button to run)
- No outreach logged yet (prompt to log)
- No upcoming meetings

---

## SECTION 7: AI FEATURE DESIGN

### 7.1 Current State Analysis

The existing `ai.py` provides:
- `generate_summary(raw_message)` - extracts 3 key lines
- `analyze_fit(raw_message, base_resume)` - token overlap scoring

This is **heuristic-based**, not LLM-based. For trader acquisition, we need sophisticated understanding of:
- Trading strategies and performance metrics
- Social influence and audience quality
- Brand alignment potential
- Negotiation dynamics
- Personalized outreach at scale

### 7.2 Target AI Capabilities

1. **Trader Profile Analysis**
   - Input: `profile_url` or pasted profile text + performance data
   - Output:
     - Strategy summary (2-3 sentences)
     - Key strengths (bulleted, 3-5 items)
     - Key weaknesses / risks (bulleted, 2-4 items)
     - Fit assessment (paragraph explaining why they would/wouldn't be a good fit for OUR marketplace specifically)
     - Recruitment recommendations (e.g., "Emphasize our non-custodial nature", "Highlight our revenue share", "Be prepared to discuss slippage tolerance")
     - Suggested communication approach (formal/casual, direct/indirect)
     - Estimated likelihood to join (1-10, with confidence interval)
   - Use case: Research phase, before outreach

2. **Outreach Generation**
   - Input: trader profile + selected template type + optional custom notes
   - Output: personalized message in chosen format (LinkedIn, Twitter DM, Email, Telegram)
   - Should:
     - Reference specific metrics (monthly return, AUM, strategy type)
     - Mention something specific from their profile
     - Include clear value proposition for them
     - Have appropriate length for channel
     - Include call-to-action
     - Be customizable with manual overrides
   - Use case: First contact or follow-up

3. **Negotiation Assistant**
   - Input: trader profile + conversation history + objections raised
   - Output:
     - List of potential objections they might raise
     - Counter-arguments for each objection
     - Concession recommendations (what we can/cannot offer)
     - Risk assessment: probability of deal failure
     - Suggested next steps
   - Use case: During negotiation phase

4. **Meeting Preparation**
   - Input: trader profile + previous outreach + any notes
   - Output:
     - 30-second trader summary
     - 3-5 discussion topics (personalized)
     - Suggested offer package (revenue share, bonuses, exclusivity)
     - Questions to ask them
     - Red flags to watch for
   - Use case: Before scheduled meeting

5. **Onboarding Complexity Assessment**
   - Input: trader's current setup (platforms they use, technical indicators, etc.)
   - Output:
     - Estimated time to onboard
     - Technical hurdles (e.g., "They use TradingView pine scripts - will need conversion")
     - Resource requirements (dev time, support)
     - Success probability
   - Use case: After agreement, before activation

### 7.3 Implementation Architecture

**Phase 1: Heuristic Simulation (MVP)**

Keep `ai.py` but extend with template-based responses:

```python
def analyze_trader_heuristic(trader):
    """Return mock AI analysis based on rule-based scoring."""
    score = trader.get('fit_score', 50)
    if score >= 80:
        strength = ["High performer", "Strong track record", "Large following"]
        weakness = ["May be selective", "Higher expectations"]
        recommendation = "Prioritize outreach, offer competitive terms"
    elif score >= 60:
        strength = ["Solid performance", "Growing audience"]
        weakness = ["Limited track record", " niche strategy"]
        recommendation = "Standard outreach, highlight platform benefits"
    else:
        strength = []
        weakness = ["Low metrics", "Unproven strategy"]
        recommendation = "Monitor, low priority for now"

    return {
        'summary': f"{trader['trader_name']} is a {trader['strategy_type']} trader on {trader['platform']} with {trader['followers']} followers.",
        'strengths': strength,
        'weaknesses': weakness,
        'fit_assessment': "Moderate fit based on metrics.",
        'recommendations': recommendation,
        'likelihood': int(score),
        'negotiation_risks': ["May require higher revenue share", "Longer decision timeline"]
    }
```

**Phase 2: LLM Integration**

Add `llm_client.py`:

```python
class LLMProvider(Protocol):
    def generate(self, prompt: str, system_prompt: str = None) -> str: ...

class OpenAIProvider:
    def __init__(self, api_key, model="gpt-4-turbo"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt, system_prompt=None):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content

class AnthropicProvider:
    # Similar structure using anthropic SDK
    ...

# Factory
def get_llm_provider(settings):
    provider = settings.get('ai.provider', 'heuristic')
    if provider == 'openai':
        return OpenAIProvider(api_key=settings['ai.api_key'], model=settings.get('ai.model', 'gpt-4-turbo'))
    elif provider == 'anthropic':
        return AnthropicProvider(...)
    else:
        return None  # heuristic fallback
```

**System prompts** (store in `prompts/` directory or in code):

`prompts/profile_analysis.txt`:
```
You are an expert trader recruitment analyst for a DeFi copy-trading marketplace.
Analyze the provided trader profile and produce:

1. STRATEGY SUMMARY (2-3 sentences): What they do, their edge, their audience.
2. STRENGTHS (bullet list, 3-5 items): Performance, reach, consistency, innovation, etc.
3. WEAKNESSES (bullet list, 2-4 items): Risks, gaps, red flags.
4. FIT ASSESSMENT: How well they align with our marketplace (non-custodial, DeFi-native, copy-trading focused). Are they a good cultural/technical fit?
5. RECOMMENDATIONS: Specific recruitment strategy - what to emphasize in outreach, what offers might appeal, potential objections to anticipate.
6. LIKELIHOOD (1-10): Numeric estimate of probability they would join.
7. NEGOTIATION RISKS: What terms might they demand? What are our leverage points?

Trader Profile:
{trader_profile_json}
```

`prompts/outreach_generation.txt`:
```
Write a personalized {channel} outreach message to {trader_name}, a {strategy_type} trader on {platform} with {followers} followers and {yearly_return}% yearly return.

Their profile summary: {summary}

Our value proposition: We are a non-custodial DeFi copy-trading marketplace where traders can publish strategies and earn 70% of copied trader profits (or commission-based). We offer access to DeFi-native capital and community.

Use this template structure:
{template}

Adapt the template to be specific to this trader. Reference their actual metrics. Be concise and professional appropriate for {channel}.

Channel constraints:
- LinkedIn: 300-1000 characters, professional tone
- Twitter DM: 280 characters max, casual but respectful
- Email: 500-1500 characters, professional with clear subject line suggestion
- Telegram: conversational, shorter

Output format:
Subject: [if email]
Message:
```

**AI endpoints implementation**:

```python
@app.post("/api/traders/{id}/ai-analyze")
async def analyze_trader(id: str):
    trader = await get_trader(id)
    settings = await get_all_settings()

    llm_provider = get_llm_provider(settings)
    prompt = build_profile_prompt(trader)

    if llm_provider:
        result = llm_provider.generate(prompt, load_prompt('profile_analysis.txt'))
    else:
        result = analyze_trader_heuristic(trader)

    # Parse result into structured fields
    analysis = parse_analysis_result(result)

    await update_trader(id, {
        'ai_summary': analysis['summary'],
        'ai_strengths': json.dumps(analysis['strengths']),
        'ai_weaknesses': json.dumps(analysis['weaknesses']),
        'ai_fit_assessment': analysis['fit_assessment'],
        'ai_recommendations': analysis['recommendations'],
        'ai_negotiation_risks': json.dumps(analysis['negotiation_risks']),
        'date_updated': datetime.utcnow().isoformat()
    })

    return analysis
```

**Frontend integration**:
- Call AI endpoints via `api()` function
- Display loading states (spinner on button, skeleton UI)
- Show results in structured cards
- Allow manual edit of AI results (they're suggestions, not gospel)
- Keep version history? Not for MVP.

### 7.4 Outreach Templates with Variables

**Template engine**: Simple string replacement with regex

```python
def render_outreach_template(template: str, trader: dict, custom_vars: dict = None) -> str:
    variables = {
        'trader_name': trader['trader_name'],
        'platform': trader['platform'],
        'strategy_type': trader['strategy_type'],
        'followers': f"{trader['followers']:,}",
        'copiers': f"{trader['copiers']:,}",
        'aum': f"${trader['assets_under_management']:,.0f}",
        'monthly_return': f"{trader['monthly_return']:+.1f}%",
        'yearly_return': f"{trader['yearly_return']:+.1f}%",
        'summary': trader.get('ai_summary', 'No summary available'),
        'my_name': 'Growth Team',  # from settings?
    }
    if custom_vars:
        variables.update(custom_vars)

    for key, value in variables.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))

    return template
```

**Frontend preview**: Same function in JavaScript for WYSIWYG editing.

### 7.5 Scoring Model Redesign

**Current**: `priority_score = fit_score * interest_score` (both 1-5)

**New**: Configurable weighted sum of 6 scores

Formula:
```python
fit_score = (
    audience_strength * w1 +
    trading_consistency * w2 +
    communication_quality * w3 +
    crypto_knowledge * w4 +
    likelihood_to_join * w5 +
    brand_value * w6
) / (w1 + w2 + w3 + w4 + w5 + w6) * 10  # normalize to 0-100
```

Where each weight is from settings (default 1.0 each → simple average × 10).

**Priority score**:
```python
priority_score = fit_score * urgency_factor
urgency_factor based on:
- Freshness: newly added = 1.5x for first 7 days
- Status: Meeting Scheduled = 1.3x, Negotiation = 1.2x
- Tags: contains 'Urgent' = 1.5x
- Custom admin override field: priority_multiplier
```

**Implementation**:
- Backend calculates on every `update_trader()` and stores
- Frontend displays live when sliders change (preview)
- Settings UI to adjust weights

### 7.6 AI Usage Tracking

Log AI calls in `settings` or separate `ai_logs` table for debugging/cost tracking:

```sql
CREATE TABLE ai_logs (
    id TEXT PRIMARY KEY,
    trader_id TEXT,
    endpoint TEXT,  -- 'analyze', 'outreach', 'meeting_prep', 'objections'
    provider TEXT,  -- 'heuristic', 'openai', 'anthropic'
    tokens_used INTEGER,
    cost REAL,
    timestamp TEXT,
    success INTEGER,
    error TEXT
);
```

**Decision**: Defer to V2 to avoid complexity. For now, simple logging in application console.

---

## SECTION 8: IMPLEMENTATION ROADMAP

### Phase 1: Database & Backend Foundation (Week 1-2)

**Goals**: New schema, API endpoints, basic CRUD

**Tasks**:

1. **Create migration SQL** (`migrations/001_initial_traders_schema.sql`)
2. **Update `database.py`**:
   - Rename functions (`create_job` → `create_trader`)
   - Update all SQL to reference `traders` table
   - Add `calculate_fit_score()` helper
   - Add `calculate_priority_score()` helper
   - Add `get_distinct_platforms()`
   - Add `get_trader_by_profile_url()` for deduplication
3. **Update `main.py`**:
   - Rename all routes from `/api/jobs` to `/api/traders`
   - Rename handler functions
   - Update request/response models (Pydantic or dicts)
   - Add new endpoints: `/api/traders/stats`, `/api/traders/{id}/outreach`, `/api/traders/{id}/timeline`
   - Remove `/api/jobs/{id}/resume` (no resumes in V1)
   - Keep `/api/settings` but add new settings
   - Keep `/api/export` and `/api/import` but for traders
4. **Create `ai.py` extensions**:
   - `analyze_trader_heuristic(trader)` - new function
   - `generate_outreach_heuristic(trader, template_type)` - new function
   - `prepare_meeting_heuristic(trader)` - new function
   - Keep existing `generate_summary()` and `analyze_fit()` for backward compatibility (may deprecate)
5. **Add new AI endpoints** in `main.py`:
   - POST `/api/traders/{id}/ai-analyze`
   - POST `/api/traders/ai-outreach`
   - POST `/api/traders/ai-meeting-prep`
6. **Update `parser.py`**:
   - Keep function names but adapt output to trader schema
   - Output dict with trader fields instead of job fields
   - Add `platform="Telegram"` default
   - Parse trader_name (instead of company_name)
   - Parse strategy hints from message (if present)
7. **Settings updates**:
   - Add default values for new settings keys in `init_db()` or separate migration
   - Ensure settings endpoint accepts new keys
8. **Testing**:
   - Manual: Use Swagger UI at `http://localhost:8000/docs`
   - Create traders via API
   - Test all CRUD operations
   - Test AI endpoints
   - Verify stats calculation
   - Test import/export roundtrip

**Success criteria**: All `GET /api/traders`, `POST /api/traders`, `PUT /api/traders/{id}`, `DELETE /api/traders/{id}` working. Stats endpoint returns platform breakdown. Settings endpoints accept new keys.

**Deliverable**: Backend fully supporting trader management with AI heuristics.

---

### Phase 2: Frontend Core Pages (Week 3-4)

**Goals**: Adapt UI to trader data model

**Tasks**:

1. **Update design system** (`design-system.css`):
   - Add platform brand colors as CSS variables
   - Add score gauge styles
   - Add timeline component styles
   - Add new status pill colors
2. **Refactor JavaScript state management** (non-breaking if possible):
   - Wrap code in IIFE
   - Extract `state` object
   - Extract `API` object
   - Extract `Utils` object
   - Ensure no breaking changes to existing `render*` functions (they'll be replaced)
3. **Dashboard page** (`renderDashboard()`):
   - Replace all job metrics with trader metrics
   - Implement pipeline funnel chart (using Tailwind bars)
   - Implement platform distribution chart (using colored bars)
   - Implement conversion rate calculator
   - Implement recent high-priority list
   - Show traders added over time (simple count by date)
4. **Traders List page** (`renderTradersList()`):
   - Update filters (status, platform, min fit, max risk)
   - Update search fields (trader_name, profile_url, notes, tags)
   - Update columns (platform badge, fit score, status, last contact, outreach attempts)
   - Implement platform badge component with brand colors
   - Implement fit score gauge component
   - Add row action buttons (quick status change, quick contact)
   - Implement sort by fit_score, priority_score
5. **Trader Detail page** (`renderTraderDetail()`):
   - Implement full two-column layout
   - Build all cards (Basic Info, Performance, Social, Scoring, Activities, AI Results)
   - Implement all form fields with proper input types
   - Implement save functionality with optimistic updates
   - Implement AI analysis buttons and result display
   - Implement outreach generator modal with template selection
   - Implement meeting scheduler modal
   - Implement quick contact log modal
   - Add status/pipeline stage dropdowns
   - Add timeline display
6. **Discovery page** (`renderDiscovery()`):
   - Rename from "Inbox" in nav
   - Update UI to show source selector tabs
   - Keep Telegram parser as first tab
   - Add Manual Entry tab with trader form
   - Add CSV Import tab (placeholder)
   - Add Platform Importers placeholder
7. **Settings page** (`renderSettings()`):
   - Update sections: AI Config, Scoring Weights, Outreach Templates, Platform Management, Data Management
   - Implement weight sliders with live fit score preview
   - Implement template textareas with variable help text
   - Implement platform toggle list
   - Update export/import to use traders
8. **Navigation**:
   - Update sidebar menu items
   - Update badge counts
   - Update active state indicators
9. **API layer updates**:
   - Update all `api()` calls from `/api/jobs` to `/api/traders`
   - Add new API methods for AI, stats, outreach, timeline
   - Update polling to use new trader endpoints
   - Handle new settings keys
10. **Parser synchronization**:
    - Ensure client-side `parseTelegramMessage()` matches `parser.py` output
    - Test roundtrip: paste Telegram message → preview → save → API → DB

**Testing**:
- Manual: Navigate all pages, test all features
- Verify data persistence
- Test filtering and search
- Test AI generation (should use heuristic)
- Test outreach generation
- Test file upload (optional - if no resumes, may skip)
- Test import/export

**Success criteria**: All 5 pages functional with trader data. AI buttons generate outputs (heuristic). Outreach generator produces messages. Settings save weights and templates.

**Deliverable**: Complete frontend transformation with all trader features.

---

### Phase 3: AI Enhancement (LLM Integration) (Week 5)

**Goals**: Replace heuristics with real LLM analysis

**Prerequisites**: Phase 1 & 2 complete, API keys obtained

**Tasks**:

1. **Create `llm_client.py`**:
   - Implement `LLMProvider` interface
   - Implement `OpenAIProvider`
   - Implement `AnthropicProvider`
   - Implement factory function `get_llm_provider(settings)`
   - Add error handling and rate limiting (basic)
   - Add token counting and cost estimation
2. **Create `prompts/` directory** with markdown files:
   - `profile_analysis.txt`
   - `outreach_generation.txt`
   - `meeting_preparation.txt`
   - `objection_handling.txt`
   - `onboarding_assessment.txt`
3. **Update AI endpoint handlers** in `main.py`:
   - Detect provider from settings
   - Instantiate LLM provider
   - Read system prompt from file
   - Call LLM, handle errors gracefully
   - Parse LLM response (expect JSON or structured text)
   - Fallback to heuristic if LLM fails or not configured
4. **Add AI logging** (optional):
   - Log each call to console or `ai_logs` table
   - Track tokens, cost, duration
5. **Update frontend**:
   - Add loading indicators (spinner) on AI buttons
   - Show error messages if AI fails
   - Allow retry
   - Option to edit AI results before saving
6. **Settings UI**:
   - Add provider selection dropdown
   - Add API key input (masked)
   - Add model selection (different options per provider)
   - Add temperature slider
   - Add "Test Connection" button
7. **Testing**:
   - Test with OpenAI API key
   - Test with Anthropic API key
   - Test fallback to heuristic when no API key
   - Verify output quality
   - Measure token usage

**Success criteria**: AI features produce sophisticated, context-aware outputs using LLM. Fallback to heuristic works.

**Deliverable**: Production-ready AI integration with configurable providers.

---

### Phase 4: Importers & Automation Prep (Week 6)

**Goals**: Foundation for automated trader discovery

**Note**: Full importers are future roadmap. This phase prepares architecture.

**Tasks**:

1. **Design importer architecture**:
   ```
   importers/
     __init__.py
     base.py - BaseImporter class (interface)
     telegram.py - TelegramImporter (existing parser)
     etoro.py - EtoroImporter (stub)
     mql5.py - MQL5Importer (stub)
     csv.py - CSVImporter (stub)
   ```
2. **Implement `BaseImporter`**:
   - Method: `import_from_source(source_data: dict) -> Trader`
   - Validation: ensure required fields, check `profile_url` uniqueness
   - Deduplication: skip if trader with same platform+profile_url exists
   - Return: trader dict or None
3. **Refactor `parser.py`** into `importers/telegram.py`:
   - Keep same logic
   - Subclass `BaseImporter`
   - Implement `parse()` method
4. **Add API endpoint** (future-proof):
   - POST `/api/traders/import` with `{ source: "telegram", data: {...} }`
   - Disabled in UI until multiple importers exist
5. **Discovery page UI**:
   - Add cards for each platform importer
   - Each card shows: platform name, status (Coming Soon), Connect button (disabled)
   - Telegram importer is active
6. **Settings page**:
   - Add platform management: enable/disable importers
   - Add API key storage for each platform (future)
7. **Future roadmap document**:
   - Outline work for each platform importer
   - Estimate effort
   - Identify API constraints (e.g., eToro may not have public API)

**Success criteria**: Clean importer architecture in place. Telegram impporter works as before. UI primed for future expansion.

**Deliverable**: Extensible importer framework ready for Phase 2-4 development.

---

### Phase 5: Polish & Production Readiness (Week 7)

**Goals**: Refinements, error handling, security, documentation

**Tasks**:

1. **Input validation**:
   - Add Pydantic models for all API inputs
   - Validate email/URL formats
   - Validate number ranges (0-100 for scores, positive for counts)
   - Sanitize text fields (prevent XSS if any HTML rendering in future)
2. **Error handling**:
   - Add try/except blocks in API routes
   - Return proper HTTP status codes
   - Log errors with traceback
   - User-friendly error messages in frontend
3. **Security hardening**:
   - Add CORS configuration (allow only localhost for now)
   - Add request size limits
   - Rate limiting on AI endpoints (to control costs)
   - API key validation for OpenAI/Anthropic
   - Warn if `.env` contains exposed keys
4. **Testing**:
   - Manual test all workflows end-to-end
   - Edge cases: null fields, very long text, special characters
   - Import/export roundtrip
   - AI failure simulation
5. **Documentation**:
   - Update README with new setup instructions
   - Document settings keys
   - Document API (Swagger auto-doc is good, enhance descriptions)
   - Document deployment steps (if any)
6. **Performance**:
   - Add DB indexes (already in migration SQL)
   - Optimize slow queries (add EXPLAIN analysis)
   - Consider pagination for large trader lists (currently loads all)
7. **UI/UX polish**:
   - Check mobile responsiveness
   - Add loading spinners for async operations
   - Add confirmation dialogs for destructive actions
   - Add undo for delete (maybe)
   - Keyboard shortcuts? (optional)
8. **Telegram bot updates**:
   - Update reply message to link to trader detail page (not job)
   - Parse trader-specific fields from Telegram
   - Consider different message formats for traders vs jobs
9. **Sample data generator**:
   - Script to create dummy traders for testing
   - Various profiles, platforms, scores
10. **Backup strategy**:
    - Document manual backup (copy jobs.db)
    - Consider auto-backup on startup

**Success criteria**: Application is robust, documented, and ready for day-to-day use.

**Deliverable**: Production-quality trader CRM.

---

## SECTION 9: QUESTIONS REQUIRING CLARIFICATION

Before proceeding with implementation, I need answers to the following:

### Q1: AI Provider Selection

**Question**: Which LLM provider(s) should we integrate? Options:
- OpenAI (GPT-4, GPT-4-turbo, GPT-3.5-turbo)
- Anthropic (Claude 3 Opus, Sonnet, Haiku)
- Both (user selectable in settings)
- None (stick with heuristics for now)

**Impact**: Determines `llm_client.py` implementation and cost structure.

### Q2: Platform Importer Prioritization

**Question**: Which platforms should we build importers for first (after Telegram)?
1. eToro (most popular copy-trading)
2. MQL5 (large forex community)
3. TradingView (massive user base)
4. ZuluTrade (signal copying)
5. Darwinex (quant-focused)

**Impact**: Determines which APIs to research and integrate first in Phase 4.

### Q3: Authentication & Multi-User

**Question**: Should we add user authentication? The current app is single-user local.
- Option A: Keep single-user, no auth (simple)
- Option B: Add basic username/password for local use
- Option C: Multi-tenant with team sharing (future roadmap)

**Impact**: Major architecture change if multi-user needed. Affects data isolation, UI, deployment.

### Q4: Deployment Model

**Question**: How should this be deployed?
- Option A: Local desktop app (current model - run `python main.py` locally)
- Option B: Docker container (self-hosted)
- Option C: Cloud deployment (AWS/Heroku/Railway) with shared links
- Option D: Keep local but add optional cloud sync

**Impact**: Affects security, CORS, database location, authentication needs.

### Q5: Data Privacy & Compliance

**Question**: Are there compliance requirements?
- GDPR: traders may be EU residents - need data deletion capability
- Data retention: How long to keep rejected trader records?
- Source data copyright: Are we storing publicly available profile data? Need to consider terms of service of source platforms.

**Impact**: May require anonymization, deletion workflows, consent tracking.

### Q6: Outreach Integration

**Question**: Should outreach be sent directly from the CRM or just logged?
- Option A: Generate message text only - user copies to platform manually
- Option B: Integrate with platform APIs to send directly (e.g., Telegram Bot API, Twitter API)
- Option C: Both - generate and optionally send if API keys provided

**Impact**: Requires platform API integrations, OAuth flows, rate limiting handling.

### Q7: Scoring Model Configurability

**Question**: How configurable should the scoring weights be?
- Option A: Admin can adjust all 6 weights (already planned)
- Option B: Fixed formula, not editable
- Option C: Allow custom formulas per user role (e.g., junior vs senior BD)

**Impact**: Complexity of settings UI and calculation engine.

### Q8: Pipeline Customization

**Question**: Should the pipeline stages (Research, Outreach, Negotiation, etc.) be customizable per organization, or fixed?
- Option A: Fixed as defined (simpler)
- Option B: Admin can add/edit/delete stages
- Option C: Users can customize their own pipeline view

**Impact**: Database structure would need `pipeline_stages` table if dynamic. Adds complexity.

### Q9: Mobile App

**Question**: Is a mobile app needed?
- The current web UI is responsive but not PWA.
- Could be wrapped in Capacitor or similar for native feel.

**Impact**: Additional tech stack, build process.

### Q10: Sample Data & Demo Mode

**Question**: Should we include a "Load Sample Data" feature like the original?
- Current app has "Load Sample Data" button that deletes DB and loads fake jobs.
- Should we include realistic trader sample data for demos?

**Impact**: Need to create realistic sample trader profiles.

### Q11: Timeline Feature

**Question**: The timeline shows activity history. What events should be tracked?
- Status changes
- Score updates
- Outreach logged
- AI analysis run
- Meeting scheduled/completed
- Onboarding milestones
- Notes added

Should every edit create a timeline entry? Or only significant events?

**Impact**: Database may need `timeline_events` table if we want full audit trail. Or can derive from notes/date fields.

### Q12: Duplicate Detection

**Question**: How should we handle duplicate traders?
- Current plan: `profile_url` is unique per platform.
- What about multiple traders with same name but different URLs?
- Same trader across multiple platforms? Should we merge?

**Impact**: Deduplication logic in importers and create_trader validation.

### Q13: File Attachments

**Question**: The original app had resume uploads. Should traders have attachments?
- Onboarding documents (KYC, contracts)
- Screenshots of performance
- Strategy documentation
- Video introductions

**Impact**: Need to decide on file storage strategy (local FS vs S3), add file table, update API.

### Q14: Notification System

**Question**: Should we add reminders/notifications?
- "Follow up with X in 3 days"
- "Meeting with Y in 1 hour"
- "Trader Z hasn't replied in 7 days"

**Impact**: Need scheduling system, email/push notifications, calendar integration.

---

## NEXT STEPS

1. **Answer the questions** above to refine the plan.
2. **Review the architecture** - any gaps or concerns?
3. **Prioritize** - is the 5-week plan realistic? Should phases overlap?
4. **Approve** the plan before any implementation begins.
5. **Implementation** will follow the writing-plans skill, breaking each phase into bite-sized tasks with TDD approach.

---

## APPROVAL REQUIRED

This plan is ready for review. Please provide:

1. Answers to the 14 questions above
2. Any modifications to the scope/phasing
3. Authorization to proceed with implementation using the superpowers execution workflow

**Once approved, I will create detailed task-level plans for each phase following TDD principles and execute them using the subagent-driven-development skill.**

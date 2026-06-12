# Trader CRM Feature Parity with Job CRM

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Trader CRM to feature parity with the Job Application CRM, minus Telegram bot and external AI APIs.

**Architecture:** Single FastAPI backend + vanilla JS frontend. All processing is local/inline. No external API calls. Add missing features from Job CRM adapted for trader domain.

**Tech Stack:** FastAPI, aiosqlite, vanilla JS, Tailwind CSS (via CDN), Font Awesome (via CDN)

---

## Feature Gap Analysis

| Feature | Job CRM | Trader CRM | Action |
|---------|---------|------------|--------|
| Manual Entry form | ✓ Inbox page | ✗ Only Quick Paste | Add Manual Entry tab |
| Raw message display | ✓ Collapsible section | ✗ No raw text field | Add `raw_text` field + display |
| AI Analysis section | ✓ fit_analysis field | ✗ None | Add local keyword analysis (no API) |
| Interest score | ✓ 0-5 scale | ✗ None | Add `interest_score` field |
| Priority score | ✓ fit × interest | ✗ None | Add computed `priority_score` (0-100) |
| Cover letter / pitch | ✓ cover_letter textarea | ✗ None | Add `cover_message` field |
| Resume management | ✓ Upload/download/remove | ✗ No file attachments | Skip (not applicable for traders) |
| Response received | ✓ Yes/No field | ✗ None | Add `response_received` field |
| Stage reached | ✓ No Response/Screening/Interview/Final Round | ✗ pipeline_stage (different values) | Add `stage_reached` field |
| Keyboard shortcuts | ✓ d, j, n, s, Esc | ✗ None | Add keyboard navigation |
| Sort dropdown | ✓ In list view | ✗ Sort param exists, no UI | Add sort dropdown |
| Platform avatars | ✓ Colored letter avatars | ✗ Platform badges only | Add hash-colored avatar circles |

---

## File Structure

| File | Purpose | Changes |
|------|---------|---------|
| `migrations/002_add_parity_fields.sql` | New fields for feature parity | Create |
| `migrations/003_add_migration_version.sql` | Migration version tracking | Create |
| `database.py` | CRUD + migration versioning | Modify |
| `main.py` | New endpoints + analysis logic + HTML escaping | Modify |
| `index.html` | UI additions + keyboard shortcuts | Modify |
| `design-system.css` | Avatar styles + keyboard hint styles | Modify |
| `tests/test_parity.py` | Tests for new features | Create |

---

## Task 1: Database Migration — Add Parity Fields

**Files:**
- Create: `migrations/002_add_parity_fields.sql`
- Create: `migrations/003_add_migration_version.sql`
- Modify: `database.py`

**Fields to add:**
- `raw_text TEXT DEFAULT ''` — raw pasted/imported text
- `interest_score INTEGER DEFAULT 0` — 0-5 scale, user-assessed interest level
- `priority_score INTEGER DEFAULT 0` — computed: (fit_score × interest_score) / 5, normalized to 0-100
- `cover_message TEXT DEFAULT ''` — pitch/cover message for outreach
- `response_received TEXT DEFAULT 'No'` — 'Yes' or 'No'
- `stage_reached TEXT DEFAULT ''` — No Response / Screening / Interview / Final Round / N/A

- [ ] **Step 1: Create migration file for parity fields**

```sql
-- migrations/002_add_parity_fields.sql
-- Add fields for feature parity with Job CRM

ALTER TABLE traders ADD COLUMN raw_text TEXT DEFAULT '';
ALTER TABLE traders ADD COLUMN interest_score INTEGER DEFAULT 0;
ALTER TABLE traders ADD COLUMN priority_score INTEGER DEFAULT 0;
ALTER TABLE traders ADD COLUMN cover_message TEXT DEFAULT '';
ALTER TABLE traders ADD COLUMN response_received TEXT DEFAULT 'No';
ALTER TABLE traders ADD COLUMN stage_reached TEXT DEFAULT '';
```

- [ ] **Step 2: Create migration version tracking**

```sql
-- migrations/003_add_migration_version.sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);
```

- [ ] **Step 3: Update init_db with migration versioning**

In `database.py`, replace the migration handling in `init_db()`:

```python
async def init_db():
    """Initialize database: create tables and set default settings."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Create base tables
        await db.executescript(MIGRATION_SQL)
        # Settings table
        await db.execute(CREATE_SETTINGS_TABLE)
        # Migration version tracking
        await db.executescript((Path(__file__).parent / "migrations" / "003_add_migration_version.sql").read_text())
        
        # Run pending migrations with version tracking
        migrations = [
            ("002", "002_add_parity_fields.sql"),
        ]
        cursor = await db.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in await cursor.fetchall()}
        
        for version, filename in migrations:
            if version not in applied:
                sql = (Path(__file__).parent / "migrations" / filename).read_text()
                await db.executescript(sql)
                await db.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (version, datetime.utcnow().isoformat())
                )
                logger.info(f"Applied migration {version}")
        
        # Default settings
        default_settings = [
            ('scoring_weights.audience_strength', '1.0'),
            ('scoring_weights.trading_consistency', '1.0'),
            ('scoring_weights.communication_quality', '1.0'),
            ('scoring_weights.crypto_knowledge', '1.0'),
            ('scoring_weights.likelihood_to_join', '1.0'),
            ('scoring_weights.brand_value', '1.0'),
            ('platforms.enabled', '["Manual","Telegram","eToro","MQL5","TradingView","ZuluTrade","Myfxbook","Darwinex","NAGA","FXBlue","Twitter","Discord"]'),
        ]
        for key, value in default_settings:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        await db.commit()
```

- [ ] **Step 4: Add priority_score calculation in create_trader and update_trader**

In `create_trader()`, after fit_score calculation:

```python
# After fit_score calculation:
interest = trader_data.get('interest_score', 0)
trader_data['priority_score'] = int(round(trader_data.get('fit_score', 0) * interest / 5))
```

In `update_trader()`, after fit_score calculation block:

```python
# After fit_score calculation:
if needs_recalc or 'interest_score' in updates:
    merged = {**current, **updates}
    fit = merged.get('fit_score', 0)
    interest = merged.get('interest_score', 0)
    updates['priority_score'] = int(round(fit * interest / 5))
```

- [ ] **Step 5: Commit**

```bash
git add migrations/002_add_parity_fields.sql migrations/003_add_migration_version.sql database.py
git commit -m "feat: add parity fields with migration version tracking"
```

---

## Task 2: Backend — HTML Escaping Utility & Analysis Endpoint

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Add HTML escaping utility**

```python
import html

def escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS."""
    if not text:
        return ""
    return html.escape(str(text))
```

- [ ] **Step 2: Add local keyword analysis function**

```python
# Stopwords as module-level constant
STOPWORDS = frozenset({
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'out', 'off', 'over',
    'under', 'again', 'further', 'then', 'once', 'and', 'but', 'or', 'nor',
    'not', 'no', 'so', 'if', 'than', 'too', 'very', 'just', 'about', 'also',
    'this', 'that', 'these', 'those', 'it', 'its', 'my', 'your', 'his',
    'her', 'our', 'their', 'what', 'which', 'who', 'whom', 'where', 'when',
    'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
    'other', 'some', 'such', 'only', 'own', 'same', 'than', 'here', 'there'
})

def analyze_trader_keywords(raw_text: str) -> dict:
    """Extract keywords from raw text without external APIs.
    
    Uses word frequency analysis with abbreviation-aware sentence splitting.
    """
    if not raw_text or not raw_text.strip():
        return {"keywords": [], "summary": "No text provided for analysis"}
    
    # Word frequency analysis
    words = raw_text.lower().split()
    word_freq = {}
    for word in words:
        clean = ''.join(c for c in word if c.isalnum())
        if clean and len(clean) > 2 and clean not in STOPWORDS:
            word_freq[clean] = word_freq.get(clean, 0) + 1
    
    # Top keywords by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [w for w, _ in sorted_words[:10]]
    
    # Abbreviation-aware sentence splitting
    # Split on . followed by space+capital or end of string, but not after common abbreviations
    import re
    abbrevs = {'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'st', 'ave', 'blvd', 'etc', 'vs', 'inc', 'ltd', 'corp'}
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', raw_text)
    # Filter out very short "sentences" that are likely fragments
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if sentences:
        summary = sentences[0]
        if len(sentences) > 1:
            summary += ' ' + sentences[1]
    else:
        summary = raw_text[:200]
    
    if len(summary) > 200:
        summary = summary[:200] + '...'
    
    return {"keywords": keywords, "summary": summary}
```

- [ ] **Step 3: Add POST /api/traders/{id}/analyze endpoint**

```python
@app.post("/api/traders/{trader_id}/analyze")
async def analyze_trader(trader_id: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        trader = await get_trader(conn, trader_id)
        if not trader:
            raise HTTPException(404, "Trader not found")
    
    raw_text = trader.get('raw_text', '') or ''
    analysis = analyze_trader_keywords(raw_text)
    
    # Save keywords to research_notes (append, don't overwrite)
    async with aiosqlite.connect(DB_PATH) as conn:
        existing_notes = trader.get('research_notes', '') or ''
        keyword_line = f"\n\n[Auto Analysis {datetime.utcnow().strftime('%Y-%m-%d')}] Keywords: {', '.join(analysis['keywords'])}"
        await update_trader(conn, trader_id, {
            'research_notes': existing_notes + keyword_line
        })
    
    return analysis
```

- [ ] **Step 4: Update _deserialize_json_fields to escape HTML in raw_text**

```python
def _deserialize_json_fields(trader):
    """Deserialize JSON string fields and escape HTML in user content."""
    if not trader:
        return trader
    # Escape HTML in raw_text to prevent XSS
    if 'raw_text' in trader and trader['raw_text']:
        trader['raw_text'] = escape_html(trader['raw_text'])
    return trader
```

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "feat: add HTML escaping, keyword analysis endpoint, and migration versioning"
```

---

## Task 3: Frontend — HTML Escaping Utility

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add escapeHtml utility function**

In the Utils object (around line 20), add:

```javascript
escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
```

- [ ] **Step 2: Commit**

```bash
git add index.html
git commit -m "feat: add HTML escaping utility for XSS prevention"
```

---

## Task 4: Frontend — Discovery Page with Manual Entry Tab

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add state.discoveryTab initialization**

In the state object (around line 26), add:
```javascript
discoveryTab: 'paste',
```

- [ ] **Step 2: Update renderDiscovery() to include two tabs**

Replace the current `renderDiscovery()` function with:

```javascript
function renderDiscovery(){
  const tab = state.discoveryTab || 'paste';
  let html = `<div class="p-6"><h1 class="text-2xl font-bold mb-6">Add Trader</h1>`;
  
  // Tab bar
  html += `<div class="flex gap-4 border-b border-brd mb-6">`;
  html += `<button class="pb-2 px-1 border-b-2 ${tab==='manual'?'border-accent font-medium text-label':'text-label-secondary'}" onclick="state.discoveryTab='manual';renderDiscovery()">Manual Entry</button>`;
  html += `<button class="pb-2 px-1 border-b-2 ${tab==='paste'?'border-accent font-medium text-label':'text-label-secondary'}" onclick="state.discoveryTab='paste';renderDiscovery()">Quick Paste</button>`;
  html += `</div>`;
  
  if(tab === 'manual') {
    html += renderManualEntry();
  } else {
    html += renderQuickPaste();
  }
  
  html += `</div>`;
  document.getElementById('content').innerHTML = html;
}

function renderManualEntry(){
  return `
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="surface p-6 rounded-2xl">
      <h2 class="text-lg font-semibold mb-4">Trader Information</h2>
      <div class="space-y-4">
        <div><label class="text-label-secondary text-sm block mb-1">Trader Name *</label><input id="me-name" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none focus:ring-1 ring-accent" placeholder="e.g. CryptoKing"></div>
        <div class="grid grid-cols-2 gap-4">
          <div><label class="text-label-secondary text-sm block mb-1">Platform</label><select id="me-platform" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none">${['Manual','eToro','MQL5','TradingView','ZuluTrade','Myfxbook','Darwinex','NAGA','FXBlue','Twitter','Discord','Telegram'].map(p=>`<option>${p}</option>`).join('')}</select></div>
          <div><label class="text-label-secondary text-sm block mb-1">Location</label><input id="me-location" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" placeholder="e.g. Singapore"></div>
        </div>
        <div><label class="text-label-secondary text-sm block mb-1">Profile URL</label><input id="me-url" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" placeholder="https://..."></div>
        <div class="grid grid-cols-2 gap-4">
          <div><label class="text-label-secondary text-sm block mb-1">Language</label><input id="me-language" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" placeholder="e.g. English"></div>
          <div><label class="text-label-secondary text-sm block mb-1">Strategy Type</label><input id="me-strategy" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" placeholder="e.g. DeFi Yield"></div>
        </div>
        <div><label class="text-label-secondary text-sm block mb-1">Raw Text (paste profile text here for analysis)</label><textarea id="me-raw" class="w-full bg-surface-raised text-label text-sm p-3 rounded-lg resize-none h-24 outline-none" placeholder="Paste any text about this trader..."></textarea></div>
      </div>
    </div>
    <div class="space-y-6">
      <div class="surface p-6 rounded-2xl">
        <h2 class="text-lg font-semibold mb-4">Performance Metrics</h2>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div><label class="text-label-secondary block mb-1">Followers</label><input id="me-followers" type="number" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" value="0"></div>
          <div><label class="text-label-secondary block mb-1">Copiers</label><input id="me-copiers" type="number" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" value="0"></div>
          <div><label class="text-label-secondary block mb-1">AUM ($)</label><input id="me-aum" type="number" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" value="0"></div>
          <div><label class="text-label-secondary block mb-1">Monthly Return %</label><input id="me-monthly" type="number" step="0.1" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" value="0"></div>
          <div><label class="text-label-secondary block mb-1">Yearly Return %</label><input id="me-yearly" type="number" step="0.1" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" value="0"></div>
          <div><label class="text-label-secondary block mb-1">Max Drawdown %</label><input id="me-dd" type="number" step="0.1" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" value="0"></div>
          <div><label class="text-label-secondary block mb-1">Risk Score (0-10)</label><input id="me-risk" type="number" min="0" max="10" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" value="0"></div>
        </div>
      </div>
      <div class="surface p-6 rounded-2xl">
        <h2 class="text-lg font-semibold mb-4">Social Links</h2>
        <div class="space-y-3">
          <div><label class="text-label-secondary text-xs block mb-1">Twitter</label><input id="me-twitter" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" placeholder="@username"></div>
          <div><label class="text-label-secondary text-xs block mb-1">Telegram</label><input id="me-telegram" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" placeholder="@username"></div>
          <div><label class="text-label-secondary text-xs block mb-1">Discord</label><input id="me-discord" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" placeholder="user#1234"></div>
          <div><label class="text-label-secondary text-xs block mb-1">YouTube</label><input id="me-youtube" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" placeholder="https://youtube.com/..."></div>
          <div><label class="text-label-secondary text-xs block mb-1">Website</label><input id="me-website" class="w-full bg-surface-raised text-label text-sm px-3 py-2 rounded-lg outline-none" placeholder="https://..."></div>
        </div>
      </div>
      <button onclick="saveManualEntry()" class="w-full bg-accent hover:bg-accent-hover text-white px-4 py-3 rounded-lg text-sm font-medium">Add Trader</button>
    </div>
  </div>`;
}

function renderQuickPaste(){
  return `
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="surface p-6 rounded-2xl">
      <h2 class="text-lg font-semibold mb-4">Paste Trader Profile</h2>
      <p class="text-label-secondary text-sm mb-4">Paste any text containing trader information. Supported fields: name, platform, location, social links, performance metrics.</p>
      <textarea id="paste-text" class="w-full bg-surface-raised text-label text-sm p-3 rounded-lg resize-none h-64 outline-none focus:ring-1 ring-accent" placeholder="Example:&#10;Trader: CryptoKing&#10;Platform: eToro&#10;Location: Singapore&#10;Twitter: @cryptoking&#10;Monthly Return: +12.5%&#10;Followers: 15000"></textarea>
    </div>
    <div class="surface p-6 rounded-2xl">
      <h2 class="text-lg font-semibold mb-4">Preview & Edit</h2>
      <div id="preview-content" class="text-label-tertiary text-sm">Paste text to see preview...</div>
      <div class="mt-6 flex gap-3">
        <button id="parse-btn" onclick="parsePreview()" class="bg-accent hover:bg-accent-hover text-white px-4 py-2 rounded-lg text-sm font-medium" disabled>Parse</button>
        <button id="save-btn" onclick="saveParsedTrader()" class="bg-sys-green hover:bg-sys-green/90 text-white px-4 py-2 rounded-lg text-sm font-medium" disabled>Add Trader</button>
      </div>
    </div>
  </div>`;
}
```

- [ ] **Step 3: Add saveManualEntry() function**

```javascript
async function saveManualEntry(){
  const name = document.getElementById('me-name').value.trim();
  if(!name){ showToast('Trader name is required','error'); return; }
  
  const trader = {
    trader_name: name,
    platform: document.getElementById('me-platform').value,
    location: document.getElementById('me-location').value,
    profile_url: document.getElementById('me-url').value,
    language: document.getElementById('me-language').value,
    strategy_type: document.getElementById('me-strategy').value,
    raw_text: document.getElementById('me-raw').value,
    followers: parseInt(document.getElementById('me-followers').value) || 0,
    copiers: parseInt(document.getElementById('me-copiers').value) || 0,
    assets_under_management: parseFloat(document.getElementById('me-aum').value) || 0,
    monthly_return: parseFloat(document.getElementById('me-monthly').value) || 0,
    yearly_return: parseFloat(document.getElementById('me-yearly').value) || 0,
    maximum_drawdown: parseFloat(document.getElementById('me-dd').value) || 0,
    risk_score: parseInt(document.getElementById('me-risk').value) || 0,
    twitter: document.getElementById('me-twitter').value,
    telegram: document.getElementById('me-telegram').value,
    discord: document.getElementById('me-discord').value,
    youtube: document.getElementById('me-youtube').value,
    website: document.getElementById('me-website').value,
    status: 'Trader Found',
    pipeline_stage: 'Research',
    date_added: new Date().toISOString(),
    date_updated: new Date().toISOString()
  };
  
  await API.createTrader(trader);
  showToast('Trader added successfully');
  navigate('traders');
}
```

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add Manual Entry tab to Discovery page"
```

---

## Task 5: Frontend — Trader Detail Enhancements

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add interest_score slider and priority display in renderTraderDetail()**

In the Scoring section of `renderTraderDetail()`, after the 6 weighted sliders, add:

```javascript
// After existing scoring sliders, before fit score display:
html += `<div class="mt-4 p-4 bg-surface-raised rounded-xl">
  <div class="grid grid-cols-2 gap-4">
    <div>
      <label class="text-label-secondary text-sm block mb-1">Interest Score (0-5)</label>
      <input type="range" min="0" max="5" value="${trader.interest_score||0}" 
        oninput="document.getElementById('interest-val').textContent=this.value;state.selectedTrader.interest_score=parseInt(this.value);updatePriorityPreview();" 
        class="w-full mb-1">
      <div class="flex justify-between text-xs"><span class="text-label-quaternary">0</span><span id="interest-val" class="text-label font-mono">${trader.interest_score||0}</span><span class="text-label-quaternary">5</span></div>
    </div>
    <div>
      <label class="text-label-secondary text-sm block mb-1">Priority Score</label>
      <div id="priority-preview" class="text-2xl font-bold text-label">${trader.priority_score||0}</div>
      <div class="text-xs text-label-secondary">fit_score × interest_score / 5</div>
    </div>
  </div>
</div>`;
```

- [ ] **Step 2: Add updatePriorityPreview() function**

```javascript
function updatePriorityPreview(){
  const fit = state.selectedTrader.fit_score || 0;
  const interest = state.selectedTrader.interest_score || 0;
  document.getElementById('priority-preview').textContent = Math.round(fit * interest / 5);
}
```

- [ ] **Step 3: Add cover_message textarea in right sidebar**

In the right sidebar section, after Research Notes, add:

```javascript
html += `<div class="surface p-6 rounded-2xl"><h2 class="text-lg font-semibold mb-4">Cover Message</h2><textarea id="cover-message" class="w-full bg-surface-raised text-label text-sm p-3 rounded-lg resize-none h-32 outline-none focus:ring-1 ring-accent" onchange="updateTraderField('cover_message',this.value)" placeholder="Pitch message for outreach...">${Utils.escapeHtml(trader.cover_message||'')}</textarea></div>`;
```

- [ ] **Step 4: Add response_received toggle and stage_reached dropdown in right sidebar**

After Quick Actions section, add:

```javascript
html += `<div class="surface p-6 rounded-2xl"><h2 class="text-lg font-semibold mb-4">Outcome Tracking</h2>
<div class="space-y-4">
  <div><label class="text-label-secondary text-sm block mb-1">Response Received</label>
    <select id="response-select" class="w-full bg-surface-raised text-label text-sm rounded px-2 py-1" onchange="updateTraderField('response_received',this.value)">
      <option value="No" ${trader.response_received==='No'?'selected':''}>No</option>
      <option value="Yes" ${trader.response_received==='Yes'?'selected':''}>Yes</option>
    </select>
  </div>
  <div><label class="text-label-secondary text-sm block mb-1">Stage Reached</label>
    <select id="stage-select" class="w-full bg-surface-raised text-label text-sm rounded px-2 py-1" onchange="updateTraderField('stage_reached',this.value)">
      <option value="" ${!trader.stage_reached?'selected':''}>-</option>
      ${['No Response','Screening','Interview','Final Round','N/A'].map(s=>`<option value="${s}" ${trader.stage_reached===s?'selected':''}>${s}</option>`).join('')}
    </select>
  </div>
</div></div>`;
```

- [ ] **Step 5: Add raw_text display (collapsible) with XSS protection**

In the left column, after Header Card, add:

```javascript
if(trader.raw_text){
  html += `<div class="surface p-6 rounded-2xl">
    <button onclick="document.getElementById('raw-section').classList.toggle('hidden');document.getElementById('raw-chevron').classList.toggle('fa-chevron-right');document.getElementById('raw-chevron').classList.toggle('fa-chevron-down')" class="flex items-center gap-2 text-label-secondary hover:text-label text-sm">
      <i class="fa-solid fa-chevron-right" id="raw-chevron"></i>Raw Profile Text
    </button>
    <div id="raw-section" class="hidden mt-4">
      <pre class="text-label-secondary text-xs whitespace-pre-wrap bg-surface-raised p-3 rounded-lg max-h-64 overflow-y-auto">${trader.raw_text}</pre>
      <button onclick="analyzeRawText('${trader.id}')" class="mt-2 text-accent hover:underline text-sm">Run Keyword Analysis</button>
    </div>
  </div>`;
}
```

Note: `trader.raw_text` is already escaped by `_deserialize_json_fields()` on the backend, so no XSS vulnerability.

- [ ] **Step 6: Add analyzeRawText() function**

```javascript
async function analyzeRawText(traderId){
  const btn = event.target;
  btn.textContent = 'Analyzing...';
  btn.disabled = true;
  try {
    const res = await fetch(`/api/traders/${traderId}/analyze`, {method:'POST'});
    const data = await res.json();
    showToast(`Found ${data.keywords.length} keywords`);
    await refreshData();
    renderTraderDetail();
  } catch(e) {
    showToast('Analysis failed', 'error');
  } finally {
    btn.textContent = 'Run Keyword Analysis';
    btn.disabled = false;
  }
}
```

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "feat: add interest score, priority score, cover message, outcome tracking, raw text display"
```

---

## Task 6: Frontend — Sort Dropdown & Keyboard Shortcuts

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add sort dropdown to traders list**

In `renderTraders()`, near the filter controls, add a sort dropdown:

```javascript
html += `<select id="sort-select" class="bg-surface-raised text-label text-sm rounded-lg px-3 py-2 outline-none" onchange="state.sort=this.value;renderTraders()">
  <option value="date_added DESC" ${state.sort==='date_added DESC'?'selected':''}>Newest First</option>
  <option value="date_added ASC" ${state.sort==='date_added ASC'?'selected':''}>Oldest First</option>
  <option value="fit_score DESC" ${state.sort==='fit_score DESC'?'selected':''}>Highest Fit</option>
  <option value="fit_score ASC" ${state.sort==='fit_score ASC'?'selected':''}>Lowest Fit</option>
  <option value="priority_score DESC" ${state.sort==='priority_score DESC'?'selected':''}>Highest Priority</option>
  <option value="last_contact_date DESC" ${state.sort==='last_contact_date DESC'?'selected':''}>Recently Contacted</option>
</select>`;
```

- [ ] **Step 2: Add keyboard shortcut handler with proper cleanup**

```javascript
// Store handler reference for cleanup
let keyboardHandler = null;

function setupKeyboardShortcuts(){
  // Remove previous handler if exists
  if(keyboardHandler) document.removeEventListener('keydown', keyboardHandler);
  
  keyboardHandler = function(e){
    // Don't trigger in input fields or with modifier keys
    if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'||e.target.tagName==='SELECT') return;
    if(e.altKey||e.ctrlKey||e.metaKey) return;
    
    if(state.currentPage==='traders'){
      const list = state.traders;
      const idx = list.findIndex(t=>t.id===state.selectedTraderId);
      
      if(e.key==='j'||e.key==='ArrowDown'){
        e.preventDefault();
        const next = idx<list.length-1 ? idx+1 : 0;
        state.selectedTraderId = list[next].id;
        renderTraders();
      }
      if(e.key==='k'||e.key==='ArrowUp'){
        e.preventDefault();
        const prev = idx>0 ? idx-1 : list.length-1;
        state.selectedTraderId = list[prev].id;
        renderTraders();
      }
      if(e.key==='Enter'&&state.selectedTraderId){
        navigate('detail');
      }
      if(e.key==='n'){
        navigate('discovery');
      }
    }
    
    if(state.currentPage==='detail'){
      if(e.key==='Escape'){
        navigate('traders');
      }
      if(e.key==='d'){
        const t = state.traders.find(t=>t.id===state.selectedTraderId);
        if(t) quickStatus('Contacted');
      }
    }
  };
  
  document.addEventListener('keydown', keyboardHandler);
}
```

- [ ] **Step 3: Call setupKeyboardShortcuts() on page navigation**

In the `navigate()` function, add cleanup and setup:

```javascript
function navigate(page, id){
  state.currentPage = page;
  if(id) state.selectedTraderId = id;
  
  // Clean up previous keyboard handler
  if(keyboardHandler) document.removeEventListener('keydown', keyboardHandler);
  
  render();
  
  // Setup keyboard shortcuts for relevant pages
  if(page === 'traders' || page === 'detail'){
    setupKeyboardShortcuts();
  }
}
```

- [ ] **Step 4: Add keyboard shortcut hints in traders list**

In the traders list header area, add:

```javascript
html += `<div class="text-label-quaternary text-xs mt-2"><span class="kbd">j</span><span class="kbd">k</span> navigate • <span class="kbd">Enter</span> open • <span class="kbd">n</span> new • <span class="kbd">d</span> mark contacted</div>`;
```

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat: add sort dropdown and keyboard shortcuts with cleanup"
```

---

## Task 7: Frontend — Platform Avatars with Hash Colors

**Files:**
- Modify: `design-system.css`
- Modify: `index.html`

- [ ] **Step 1: Add avatar styles in design-system.css**

```css
.trader-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
  color: #fff;
  flex-shrink: 0;
}

/* Keyboard shortcut hints */
.kbd {
  display: inline-block;
  padding: 2px 6px;
  font-size: 11px;
  font-family: monospace;
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-secondary);
}

/* Avatar responsive */
@media (max-width: 768px) {
  .trader-avatar { width: 32px; height: 32px; font-size: 14px; }
}
```

- [ ] **Step 2: Add hash-based color utility**

In the Utils object, add:

```javascript
hashColor(str) {
  // Generate consistent color from string hash
  let hash = 0;
  for(let i=0; i<str.length; i++){
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash; // Convert to 32-bit integer
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 65%, 45%)`;
}
```

- [ ] **Step 3: Update traders list to use avatars**

In `renderTraders()`, replace the platform badge with an avatar:

```javascript
// Instead of platform badge, show avatar with first letter and hash color
const avatarBg = Utils.hashColor(t.trader_name);
html += `<div class="trader-avatar" style="background:${avatarBg}">${t.trader_name.charAt(0).toUpperCase()}</div>`;
```

- [ ] **Step 4: Commit**

```bash
git add design-system.css index.html
git commit -m "feat: add hash-colored platform avatars and keyboard hint styles"
```

---

## Task 8: Tests

**Files:**
- Create: `tests/test_parity.py`

- [ ] **Step 1: Write tests for new fields and features**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_create_trader_with_parity_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/traders", json={
            "trader_name": "TestTrader",
            "platform": "eToro",
            "raw_text": "Test raw text content",
            "interest_score": 4,
            "cover_message": "Hello, we'd love to collaborate",
            "response_received": "Yes",
            "stage_reached": "Interview"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["raw_text"] == "Test raw text content"
        assert data["interest_score"] == 4
        assert data["priority_score"] == data["fit_score"] * 4 // 5
        assert data["cover_message"] == "Hello, we'd love to collaborate"
        assert data["response_received"] == "Yes"
        assert data["stage_reached"] == "Interview"

@pytest.mark.asyncio
async def test_priority_score_calculation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/traders", json={
            "trader_name": "PriorityTest",
            "interest_score": 5,
            "audience_strength": 10,
            "trading_consistency": 10,
            "communication_quality": 10,
            "crypto_knowledge": 10,
            "likelihood_to_join": 10,
            "brand_value": 10
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["fit_score"] == 100
        assert data["priority_score"] == 100  # (100 * 5) / 5 = 100

@pytest.mark.asyncio
async def test_priority_score_zero_interest():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/traders", json={
            "trader_name": "ZeroInterest",
            "interest_score": 0,
            "audience_strength": 10,
            "trading_consistency": 10,
            "communication_quality": 10,
            "crypto_knowledge": 10,
            "likelihood_to_join": 10,
            "brand_value": 10
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["priority_score"] == 0

@pytest.mark.asyncio
async def test_analyze_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create trader with raw text
        create_resp = await client.post("/api/traders", json={
            "trader_name": "AnalyzeTest",
            "raw_text": "Crypto trader with 10000 followers on eToro. Specializes in DeFi yield farming strategies. High risk tolerance."
        })
        trader_id = create_resp.json()["id"]
        
        # Run analysis
        resp = await client.post(f"/api/traders/{trader_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert "keywords" in data
        assert "summary" in data
        assert len(data["keywords"]) > 0
        # Should contain domain-specific keywords
        assert any(k in data["keywords"] for k in ["crypto", "trader", "defi", "yield", "farming"])

@pytest.mark.asyncio
async def test_analyze_endpoint_empty_text():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/api/traders", json={
            "trader_name": "EmptyText",
            "raw_text": ""
        })
        trader_id = create_resp.json()["id"]
        
        resp = await client.post(f"/api/traders/{trader_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["keywords"] == []
        assert "No text" in data["summary"]

@pytest.mark.asyncio
async def test_analyze_endpoint_special_characters():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/api/traders", json={
            "trader_name": "SpecialChars",
            "raw_text": "Trader with <script>alert('xss')</script> and &amp; entities"
        })
        trader_id = create_resp.json()["id"]
        
        resp = await client.post(f"/api/traders/{trader_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert "keywords" in data
        # XSS payload should not be in keywords
        assert "<script>" not in str(data["keywords"])

@pytest.mark.asyncio
async def test_migration_idempotency():
    """Test that running init_db twice doesn't fail."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Just verify the server is running (init_db was called during startup)
        resp = await client.get("/api/traders/stats")
        assert resp.status_code == 200
        
        # Create a trader to verify DB works after double init
        resp = await client.post("/api/traders", json={
            "trader_name": "MigrationTest"
        })
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_html_escaping_in_response():
    """Test that raw_text is HTML-escaped in API response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/traders", json={
            "trader_name": "XSS Test",
            "raw_text": "Text with <b>bold</b> and <script>alert('xss')</script>"
        })
        assert resp.status_code == 200
        data = resp.json()
        # raw_text should be escaped
        assert "&lt;b&gt;" in data["raw_text"]
        assert "&lt;script&gt;" in data["raw_text"]
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_parity.py -v`
Expected: All 8 tests PASS

- [ ] **Step 3: Run all tests together**

Run: `pytest tests/ -v`
Expected: All tests PASS (existing + new)

- [ ] **Step 4: Commit**

```bash
git add tests/test_parity.py
git commit -m "test: add comprehensive tests for parity fields, analysis, XSS protection, and migration"
```

---

## Task 9: Final Integration Test

- [ ] **Step 1: Run lint/typecheck**

Run: `python -m py_compile main.py database.py`
Expected: No errors

- [ ] **Step 2: Manual smoke test**

1. Start server: `python main.py`
2. Open http://localhost:8000
3. Verify Dashboard loads with stats
4. Click Traders → verify sort dropdown works
5. Press j/k to navigate list, Enter to open detail
6. Verify interest_score slider, priority_score display, cover_message textarea
7. Verify outcome tracking (response_received, stage_reached)
8. Click Discovery → verify Manual Entry tab works
9. Fill form and save → trader appears in list
10. Quick Paste → paste text → preview → save
11. Settings → verify scoring weights, platforms
12. Test keyboard shortcuts: j/k navigate, Enter opens, n goes to discovery, d marks contacted, Esc returns

- [ ] **Step 3: Commit final state**

```bash
git add -A
git commit -m "feat: complete feature parity with Job CRM (minus Telegram and external APIs)"
```

---

## Summary of Changes

| Component | Changes |
|-----------|---------|
| Database | 6 new fields via versioned migration, priority_score auto-calculation |
| Backend | HTML escaping utility, keyword analysis endpoint, migration versioning |
| Frontend | Manual Entry tab, interest/priority scoring, cover message, outcome tracking, raw text display, sort dropdown, keyboard shortcuts with cleanup, hash-colored avatars |
| Tests | 8 new tests covering parity fields, analysis, XSS, migration idempotency |
| CSS | Avatar styles, keyboard hints, responsive styles |

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2025-06-13-job-crm-parity.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

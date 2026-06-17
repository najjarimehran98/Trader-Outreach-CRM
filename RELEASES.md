# Release Notes

## v1.2.0 — Bug Fix Sprint
**Date:** 2025-06-17

### Bug Fixes (Frontend)
- Fixed keyboard Enter shortcut dropping trader ID — now opens detail correctly
- Fixed scoring sliders completely broken — `calculatePreview` moved to global scope, DOM targeting fixed with unique IDs
- Fixed raw text expand/collapse — replaced CSS class toggle with direct style manipulation
- Added error handling to `refreshData` — connection recovery now works
- Added error handling to `updateTraderField` — shows error toast on failure
- Fixed `togglePlatform` splice(-1) bug — now checks index before removing
- Escaped `research_notes` in textarea (was unescaped unlike `cover_message`)
- Changed `window.onload` to `addEventListener` to avoid overwriting

### Bug Fixes (Backend)
- Enabled `PRAGMA foreign_keys = ON` — orphaned outreach logs now deleted with traders
- Added `?confirm=yes` guard to `DELETE /api/traders` — prevents accidental data wipe
- Fixed `_seed_sample_data` crash on restart — each insert wrapped in try/except
- Fixed `import_data` crash when settings key missing — now checks type before iterating
- Fixed `import_traders` bypassing fit score calculation — now uses `create_trader` for proper scoring

### Files Changed
- `index.html` — 8 frontend fixes
- `main.py` — 3 backend fixes
- `database.py` — 2 backend fixes

---

## v1.1.2 — Fix: Trader Detail Page Blank
**Date:** 2025-06-17

### Bug Fixes
- Removed premature `calculatePreview()` call in `renderTraderDetail()` that accessed DOM elements before they were created, causing a TypeError and blank page

### Files Changed
- `index.html` — removed redundant function call

---

## v1.1.1 — Fix: Quick Parse Button Disabled
**Date:** 2025-06-17

### Bug Fixes
- Parse button on Discovery page was permanently disabled — added `oninput` handler to textarea to enable/disable the button based on text content

### Files Changed
- `index.html` — textarea oninput handler

---

## v1.1.0 — Fix: New Trader Entries Not Saving
**Date:** 2025-06-17

### Bug Fixes
- Added missing `Content-Type: application/json` header to all API POST/PUT methods — FastAPI was not parsing request bodies correctly in some browsers
- Added `await refreshData()` before navigating to traders list after creating a new entry — the list was showing stale data

### Files Changed
- `index.html` — API methods and save functions

---

## v1.0.0 — Apple macOS Redesign + Job CRM Parity
**Date:** 2025-06-15

### Features
- Apple macOS-inspired UI redesign (sidebar blur, toolbar headers, grouped lists)
- Pure custom CSS (`design-system.css`) — removed Tailwind CDN and Font Awesome
- Inline SVG icons replacing icon fonts
- Job CRM feature parity: interest score, priority score, cover messages, raw text analysis
- Keyboard shortcuts (j/k/n/d/Esc)
- Hash-colored platform avatars
- Sort by 6 options (date, fit score, priority, last contact)
- Trader profile text analysis (keywords + summary)

### Bug Fixes
- Fixed `importData()` syntax error
- Fixed `renderTraderDetail()` async issue
- Fixed `clearAllData()` missing endpoint
- Fixed `GET /api/traders/stats` route ordering bug
- Fixed `updateNavActive()` class selector

### Testing
- 23 tests passing (test_traders, test_parity, test_frontend)
- Frontend integrity tests for CSS/design verification

### Deployment
- Dockerfile updated with PORT env var for Render.com
- render.yaml added for Render.com deployment
- README.md with setup and deploy instructions
- Dead files cleaned (parser.py, sample_data, stale docs)

### Security
- Removed `.Claude/Settings.json` with API key from git history
- Added `.Claude/` and `.DS_Store` to .gitignore

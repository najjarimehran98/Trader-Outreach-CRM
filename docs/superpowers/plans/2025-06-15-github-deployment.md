# GitHub Deployment — Render.com Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Trader CRM app ready to deploy on Render.com via GitHub, so colleagues can access a live demo URL.

**Architecture:** Minimal changes — the app already reads `PORT` from env var and uses relative API URLs. We just need to fix the Dockerfile, add a Render config, write a README, and clean up the gitignore. No application code changes required.

**Tech Stack:** FastAPI, SQLite, Docker, Render.com

---

## Current State Analysis

The app is already 90% deployment-ready:
- `main.py:94` reads `PORT` from env var ✓
- `main.py:496-498` runs uvicorn on that PORT ✓
- Frontend uses relative URLs (`/api/...`) — no hardcoded host ✓
- `.gitignore` excludes `traders.db` ✓
- `requirements.txt` has all dependencies ✓

### What actually needs fixing:

| File | Issue | Fix |
|------|-------|-----|
| `Dockerfile:6` | Hardcodes `--port 8000` | Use `$PORT` env var |
| `.gitignore` | Missing `*.db` pattern (only has `traders.db`) | Add `*.db` |
| `README.md` | Doesn't exist | Create with project description + deploy instructions |
| `render.yaml` | Doesn't exist | Create for declarative Render config |

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `Dockerfile` | Modify | Use `$PORT` env var instead of hardcoded 8000 |
| `.gitignore` | Modify | Broaden DB exclusion pattern |
| `README.md` | Create | Project description + local dev + Render deploy instructions |
| `render.yaml` | Create | Render.com service definition (auto-detects Python) |

---

### Task 1: Fix Dockerfile for Render PORT env var

**Files:**
- Modify: `Dockerfile:6`

- [ ] **Step 1: Update Dockerfile CMD**

Current `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Replace with:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

This uses shell expansion so Render can inject its `PORT` env var, while defaulting to 8000 for local Docker runs.

- [ ] **Step 2: Verify Docker build works**

Run:
```bash
docker build -t trader-crm-test . && docker run -p 8000:8000 trader-crm-test
```

Expected: App starts on port 8000, accessible at `http://localhost:8000`

- [ ] **Step 3: Verify PORT override works**

Run:
```bash
docker run -e PORT=9000 -p 9000:9000 trader-crm-test
```

Expected: App starts on port 9000, accessible at `http://localhost:9000`

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "fix: use PORT env var in Dockerfile for Render deployment"
```

---

### Task 2: Clean up .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Update .gitignore**

Current `.gitignore`:
```
.env
traders.db
__pycache__/
*.pyc
.DS_Store
.Claude/
```

Replace with:
```
.env
*.db
__pycache__/
*.pyc
.DS_Store
.Claude/
```

Changed `traders.db` → `*.db` to catch any SQLite database files.

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: broaden .gitignore db pattern"
```

---

### Task 3: Create README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

```markdown
# Trader Outreach CRM

A CRM for managing trader outreach — tracking traders across platforms (eToro, MQL5, TradingView, etc.), scoring their fit, managing outreach pipelines, and analyzing profile data.

## Features

- **Traders List** — Sort by fit score, priority, date added, last contact
- **Trader Detail** — Edit scores, cover messages, raw profile text, outreach logs
- **Discovery** — Paste trader profiles for auto-analysis (keywords, summary)
- **Dashboard** — Pipeline stats, reply rates, platform breakdown
- **Settings** — Scoring weights, platform toggles
- **Keyboard Shortcuts** — j/k navigate, Enter opens, n new, d delete, Esc back

## Local Development

```bash
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open [http://localhost:8000](http://localhost:8000)

## Run Tests

```bash
pytest tests/ -v
```

## Deploy to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects Python — settings are pre-configured via `render.yaml`
5. Click "Deploy"

Your app will be live at `https://your-app-name.onrender.com`

**Note:** Free tier sleeps after 15 min of inactivity. First request takes ~30s to wake up. SQLite data resets on redeploy — this is a demo environment.

## Tech Stack

- **Backend:** FastAPI + aiosqlite
- **Frontend:** Vanilla JS (single HTML file)
- **Design:** Custom Apple-inspired CSS (`design-system.css`)
- **Database:** SQLite (file-based, zero config)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with local dev and Render deploy instructions"
```

---

### Task 4: Create render.yaml

**Files:**
- Create: `render.yaml`

- [ ] **Step 1: Write render.yaml**

```yaml
services:
  - type: web
    name: trader-crm
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
```

This tells Render:
- Use Python 3.11
- Install deps from requirements.txt
- Start with uvicorn on the PORT Render assigns
- Free plan

- [ ] **Step 2: Commit**

```bash
git add render.yaml
git commit -m "chore: add render.yaml for Render.com deployment"
```

---

### Task 5: Final verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run:
```bash
pytest tests/ -v
```

Expected: 23/23 tests pass

- [ ] **Step 2: Verify git log is clean**

Run:
```bash
git log --oneline -6
```

Expected: 4 new commits (Dockerfile, .gitignore, README, render.yaml)

- [ ] **Step 3: Push to GitHub**

```bash
git push origin main
```

After push, the repo is ready for Render deployment.

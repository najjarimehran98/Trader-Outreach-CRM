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

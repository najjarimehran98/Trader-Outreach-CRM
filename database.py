import aiosqlite
import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "traders.db"

# Load migration SQL
MIGRATION_SQL = (Path(__file__).parent / "migrations" / "001_create_traders.sql").read_text()

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
"""

VALID_SORT = {
    "date_added DESC", "date_added ASC",
    "fit_score DESC", "fit_score ASC",
    "priority_score DESC", "priority_score ASC",
    "last_contact_date DESC",
}

def generate_id():
    return f"{int(time.time()):x}{random.randbytes(3).hex()}"

def calculate_fit_score(trader, weights):
    """Calculate weighted fit score (0-100) from 6 component scores (1-10 each)."""
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

async def get_traders(conn, status='all', platform='all', min_fit=0, search='', sort='date_added DESC'):
    """List traders with optional filters."""
    conditions = []
    params = []

    if status != 'all':
        conditions.append("status = ?")
        params.append(status)
    if platform != 'all':
        conditions.append("platform = ?")
        params.append(platform)
    if min_fit > 0:
        conditions.append("fit_score >= ?")
        params.append(min_fit)
    if search:
        conditions.append("(trader_name LIKE ? OR profile_url LIKE ? OR research_notes LIKE ? OR tags LIKE ?)")
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term, search_term])

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    if sort not in VALID_SORT:
        sort = "date_added DESC"
    sql = f"SELECT * FROM traders {where_clause} ORDER BY {sort}"
    cursor = await conn.execute(sql, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]

async def get_trader(conn, trader_id: str):
    cursor = await conn.execute("SELECT * FROM traders WHERE id = ?", (trader_id,))
    row = await cursor.fetchone()
    trader = dict(row) if row else None
    if trader:
        # Fetch outreach logs
        outreach_logs = await get_outreach_logs(conn, trader_id)
        trader['outreach_logs'] = outreach_logs
    return trader

async def create_trader(conn, trader_data: dict) -> str:
    """Insert new trader. Returns trader_id."""
    trader_id = generate_id()
    now = datetime.utcnow().isoformat()
    trader_data.setdefault('id', trader_id)
    trader_data.setdefault('date_added', now)
    trader_data.setdefault('date_updated', now)

    # Calculate fit_score if scoring fields present
    scoring_fields = ['audience_strength', 'trading_consistency', 'communication_quality',
                     'crypto_knowledge', 'likelihood_to_join', 'brand_value']
    if any(f in trader_data for f in scoring_fields):
        cursor = await conn.execute(
            "SELECT key, value FROM settings WHERE key LIKE 'scoring_weights.%'"
        )
        rows = await cursor.fetchall()
        weights = {}
        for row in rows:
            key = row[0].split('.')[-1]
            weights[key] = float(row[1])
        for f in scoring_fields:
            weights.setdefault(f, 1.0)
        trader_data['fit_score'] = calculate_fit_score(trader_data, weights)

    # Calculate priority_score: (fit_score * interest_score) / 5
    interest = trader_data.get('interest_score', 0)
    trader_data['priority_score'] = int(round(trader_data.get('fit_score', 0) * interest / 5))

    fields = list(trader_data.keys())
    values = []
    for f in fields:
        v = trader_data[f]
        if isinstance(v, (dict, list)):
            v = json.dumps(v)
        values.append(v)

    placeholders = ", ".join(["?"] * len(fields))
    sql = f"INSERT INTO traders ({','.join(fields)}) VALUES ({placeholders})"
    await conn.execute(sql, values)
    await conn.commit()
    return trader_id

async def update_trader(conn, trader_id: str, updates: dict) -> dict:
    """Update trader and recalculate fit_score if scoring fields changed."""
    current = await get_trader(conn, trader_id)
    if not current:
        return None

    scoring_fields = ['audience_strength', 'trading_consistency', 'communication_quality',
                     'crypto_knowledge', 'likelihood_to_join', 'brand_value']
    needs_recalc = any(field in updates for field in scoring_fields)

    merged = {**current, **updates}

    if needs_recalc:
        # Get weights from settings (all scoring_weights keys)
        cursor = await conn.execute(
            "SELECT key, value FROM settings WHERE key LIKE 'scoring_weights.%'"
        )
        rows = await cursor.fetchall()
        weights = {}
        for row in rows:
            key = row[0].split('.')[-1]  # extract field name after dot
            weights[key] = float(row[1])
        # Default missing weights to 1.0
        for field in scoring_fields:
            weights.setdefault(field, 1.0)

        updates['fit_score'] = calculate_fit_score(merged, weights)
        merged['fit_score'] = updates['fit_score']

    if needs_recalc or 'interest_score' in updates:
        fit = merged.get('fit_score', 0)
        interest = merged.get('interest_score', 0)
        updates['priority_score'] = int(round(fit * interest / 5))

    updates['date_updated'] = datetime.utcnow().isoformat()

    if not updates:
        return current

    set_clause = ','.join([f"{k} = ?" for k in updates.keys()])
    params = list(updates.values()) + [trader_id]
    await conn.execute(f"UPDATE traders SET {set_clause} WHERE id = ?", params)
    await conn.commit()

    return await get_trader(conn, trader_id)

async def delete_trader(conn, trader_id: str) -> bool:
    cursor = await conn.execute("DELETE FROM traders WHERE id = ?", (trader_id,))
    await conn.commit()
    return cursor.rowcount > 0

async def get_traders_stats(conn):
    """Return dashboard statistics."""
    cursor = await conn.execute("SELECT COUNT(*) FROM traders")
    row = await cursor.fetchone()
    total = row[0] if row else 0

    cursor = await conn.execute("SELECT status, COUNT(*) FROM traders GROUP BY status")
    status_rows = await cursor.fetchall()
    by_status = {row[0]: row[1] for row in status_rows}

    cursor = await conn.execute("SELECT platform, COUNT(*) FROM traders GROUP BY platform")
    platform_rows = await cursor.fetchall()
    by_platform = {row[0]: row[1] for row in platform_rows}

    active_pipeline = sum(by_status.get(s, 0) for s in
                         ['Trader Found', 'Researching', 'Contacted', 'Replied', 'Interested',
                          'Meeting Scheduled', 'Negotiation', 'Onboarding'])

    replied = by_status.get('Replied', 0)
    contacted = by_status.get('Contacted', 0) + replied
    reply_rate = (replied / contacted * 100) if contacted > 0 else 0

    cursor = await conn.execute("SELECT SUM(outreach_attempts) FROM traders")
    total_outreach_row = await cursor.fetchone()
    total_outreach = total_outreach_row[0] or 0

    return {
        'total': total,
        'active_pipeline': active_pipeline,
        'total_outreach': total_outreach,
        'reply_rate': round(reply_rate, 1),
        'by_status': by_status,
        'by_platform': by_platform,
        'conversion_rate': round((active_pipeline / total * 100) if total > 0 else 0, 1)
    }

async def log_outreach(conn, trader_id: str, method: str, notes: str = '') -> str:
    """Log an outreach attempt."""
    outreach_id = f"out_{generate_id()}"
    now = datetime.utcnow().isoformat()
    await conn.execute(
        "INSERT INTO outreach_logs (id, trader_id, date_sent, method, notes) VALUES (?, ?, ?, ?, ?)",
        (outreach_id, trader_id, now, method, notes)
    )
    await conn.commit()
    # Increment outreach_attempts and update last_contact_date
    await conn.execute(
        "UPDATE traders SET outreach_attempts = outreach_attempts + 1, last_contact_date = ? WHERE id = ?",
        (now, trader_id)
    )
    await conn.commit()
    return outreach_id

async def get_outreach_logs(conn, trader_id: str):
    cursor = await conn.execute(
        "SELECT * FROM outreach_logs WHERE trader_id = ? ORDER BY date_sent DESC",
        (trader_id,)
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]

async def get_setting(conn, key: str) -> str:
    cursor = await conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = await cursor.fetchone()
    return row[0] if row else ""

async def set_setting(conn, key: str, value: str):
    await conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    await conn.commit()

async def get_all_settings(conn) -> dict:
    cursor = await conn.execute("SELECT key, value FROM settings")
    rows = await cursor.fetchall()
    return {row[0]: row[1] for row in rows}

async def import_traders(conn, traders_data: list):
    """Bulk import traders."""
    for trader in traders_data:
        try:
            fields = [k for k in trader.keys()]
            placeholders = ", ".join(["?"] * len(fields))
            columns = ",".join(fields)
            values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in [trader[f] for f in fields]]
            await conn.execute(f"INSERT OR REPLACE INTO traders ({columns}) VALUES ({placeholders})", values)
        except Exception:
            continue
    await conn.commit()

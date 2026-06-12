-- Create traders table
CREATE TABLE IF NOT EXISTS traders (
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
    fit_score INTEGER DEFAULT 0,
    creator_score INTEGER DEFAULT 0,
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_traders_platform ON traders(platform);
CREATE INDEX IF NOT EXISTS idx_traders_status ON traders(status);
CREATE INDEX IF NOT EXISTS idx_traders_fit_score ON traders(fit_score DESC);
CREATE INDEX IF NOT EXISTS idx_traders_date_added ON traders(date_added DESC);

-- Create outreach_logs table
CREATE TABLE IF NOT EXISTS outreach_logs (
    id TEXT PRIMARY KEY,
    trader_id TEXT NOT NULL,
    date_sent TEXT NOT NULL,
    method TEXT NOT NULL,
    notes TEXT DEFAULT '',
    FOREIGN KEY (trader_id) REFERENCES traders(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_outreach_logs_trader_id ON outreach_logs(trader_id);
CREATE INDEX IF NOT EXISTS idx_outreach_logs_date_sent ON outreach_logs(date_sent DESC);

-- Add fields for feature parity with Job CRM
ALTER TABLE traders ADD COLUMN raw_text TEXT DEFAULT '';
ALTER TABLE traders ADD COLUMN interest_score INTEGER DEFAULT 0;
ALTER TABLE traders ADD COLUMN priority_score INTEGER DEFAULT 0;
ALTER TABLE traders ADD COLUMN cover_message TEXT DEFAULT '';
ALTER TABLE traders ADD COLUMN response_received TEXT DEFAULT 'No';
ALTER TABLE traders ADD COLUMN stage_reached TEXT DEFAULT '';

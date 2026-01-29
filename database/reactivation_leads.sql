-- ===========================================
-- Reactivation Leads Table
-- Stores lead context for AI responder
-- ===========================================

-- Table to store lead context from CSV uploads
CREATE TABLE IF NOT EXISTS reactivation_leads (
    id BIGSERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    notes TEXT,
    company VARCHAR(255),
    campaign_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'contacted',
    conversation_history JSONB DEFAULT '[]'::jsonb,
    last_contact TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast phone lookups
CREATE INDEX IF NOT EXISTS idx_reactivation_leads_phone ON reactivation_leads(phone);

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_reactivation_leads_status ON reactivation_leads(status);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_reactivation_leads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_reactivation_leads_updated_at ON reactivation_leads;
CREATE TRIGGER trigger_reactivation_leads_updated_at
    BEFORE UPDATE ON reactivation_leads
    FOR EACH ROW
    EXECUTE FUNCTION update_reactivation_leads_updated_at();

-- ===========================================
-- Also ensure reactivation_log exists (for campaign tracking)
-- ===========================================

CREATE TABLE IF NOT EXISTS reactivation_log (
    id BIGSERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    company VARCHAR(255),
    campaign_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'sent',
    error TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for campaign progress queries
CREATE INDEX IF NOT EXISTS idx_reactivation_log_campaign ON reactivation_log(campaign_id);
CREATE INDEX IF NOT EXISTS idx_reactivation_log_phone ON reactivation_log(phone);

-- ===========================================
-- Grant permissions (adjust if needed)
-- ===========================================
-- GRANT ALL ON reactivation_leads TO authenticated;
-- GRANT ALL ON reactivation_log TO authenticated;

COMMENT ON TABLE reactivation_leads IS 'Stores lead context from CSV uploads for AI responder';
COMMENT ON TABLE reactivation_log IS 'Logs each message sent in reactivation campaigns';

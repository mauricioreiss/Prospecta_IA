-- =====================================================
-- MIGRATION: Tabela reactivation_log
-- Para rastrear mensagens de reativacao e evitar duplicatas
-- Execute no Supabase SQL Editor
-- =====================================================

-- Tabela para log de mensagens de reativacao enviadas
CREATE TABLE IF NOT EXISTS reactivation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Dados do lead
    phone TEXT NOT NULL,                          -- Telefone normalizado (55...)
    name TEXT,                                    -- Nome do lead
    company TEXT,                                 -- Empresa

    -- Campanha
    campaign_id TEXT NOT NULL,                    -- ID da campanha de reativacao
    message_preview TEXT,                         -- Preview da mensagem enviada

    -- Status
    status TEXT DEFAULT 'queued',                 -- 'queued', 'sent', 'failed', 'delivered'
    error TEXT,                                   -- Erro se falhou

    -- Timestamps
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,

    -- Evitar duplicatas do mesmo telefone na mesma campanha
    UNIQUE(phone, campaign_id)
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_reactivation_phone ON reactivation_log(phone);
CREATE INDEX IF NOT EXISTS idx_reactivation_campaign ON reactivation_log(campaign_id);
CREATE INDEX IF NOT EXISTS idx_reactivation_sent_at ON reactivation_log(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_reactivation_status ON reactivation_log(status);

-- RLS
ALTER TABLE reactivation_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all on reactivation_log" ON reactivation_log FOR ALL USING (true);

-- =====================================================
-- FIM DA MIGRATION
-- =====================================================

-- =====================================================
-- PROSPECTA IA v3.0 - Schema PostgreSQL
-- Estrutura: Senior Daora
-- Execute no Supabase SQL Editor
-- =====================================================

-- =====================================================
-- 1. TABELA: leads (O Core Unificado)
-- Centraliza prospeccao fria e leads do formulario
-- =====================================================

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Origem do lead
    origem TEXT NOT NULL DEFAULT 'outbound',  -- 'inbound' (Site) ou 'outbound' (Maps)

    -- Dados do contato
    nome_contato TEXT,                        -- Nome do lead captado
    nome_empresa TEXT NOT NULL,               -- Razao social ou nome fantasia
    telefone TEXT,                            -- WhatsApp/Telefone formatado
    email TEXT,                               -- E-mail do contato

    -- Dados da empresa
    site_url TEXT,                            -- Link do site para analise da IA
    endereco TEXT,
    cidade TEXT,

    -- Qualificacao
    segmento_declarado TEXT,                  -- Opcao escolhida no formulario
    faturamento_faixa TEXT,                   -- Faixa de faturamento para Score

    -- Pipeline
    status TEXT DEFAULT 'Novo',               -- 'Novo', 'Qualificado', 'Reuniao Agendada', 'Curioso'

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 2. TABELA: lead_intelligence (O Cerebro)
-- Onde a IA salva o que "pensou" - substitui nota Google
-- =====================================================

CREATE TABLE IF NOT EXISTS lead_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamento
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Score calculado pela IA
    ai_score FLOAT DEFAULT 0,                 -- Pontuacao 0-100 (Segmento x Faturamento)

    -- Diagnostico
    diagnostico_ferida TEXT,                  -- Resumo 3 linhas sobre estoque parado
    maquinas_detectadas JSONB DEFAULT '[]',   -- Lista de equipamentos achados no site

    -- Output de venda
    script_20_linhas TEXT,                    -- Pitch pronto para o SDR

    -- Sintese (substitui HTML bruto)
    sintese_site TEXT,                        -- Breve resumo do texto do site (~500 chars)

    -- Metadados
    segmento_detectado TEXT,                  -- Segmento identificado pela IA
    pontos_falhos JSONB DEFAULT '[]',         -- Oportunidades detectadas

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraint: 1 intelligence por lead
    UNIQUE(lead_id)
);

-- =====================================================
-- 3. TABELA: interactions (Historico de Acao)
-- Para IA saber se ja ligou ou mandou WhatsApp
-- =====================================================

CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamento
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Tipo de interacao
    tipo TEXT NOT NULL,                       -- 'WhatsApp', 'Ligacao AI', 'Ligacao Humana', 'Email', 'Reuniao'

    -- Conteudo
    resumo_conversa TEXT,                     -- Transcricao ou resumo do que foi falado
    sentimento TEXT,                          -- 'Positivo', 'Negativo', 'Neutro' (Filtro de curiosos)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 4. TABELA: clientes_existentes (Blacklist)
-- Empresas que ja sao clientes - nao prospectar
-- =====================================================

CREATE TABLE IF NOT EXISTS clientes_existentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_empresa TEXT NOT NULL,
    nome_normalizado TEXT UNIQUE NOT NULL,
    origem TEXT DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 5. TABELA: webhook_logs (Debug/Auditoria)
-- Log de webhooks recebidos do Baserow
-- =====================================================

CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,                     -- 'baserow', 'site', etc
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- INDICES PARA PERFORMANCE
-- =====================================================

-- Leads
CREATE INDEX IF NOT EXISTS idx_leads_origem ON leads(origem);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_segmento ON leads(segmento_declarado);
CREATE INDEX IF NOT EXISTS idx_leads_faturamento ON leads(faturamento_faixa);
CREATE INDEX IF NOT EXISTS idx_leads_cidade ON leads(cidade);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);

-- Intelligence
CREATE INDEX IF NOT EXISTS idx_intelligence_lead ON lead_intelligence(lead_id);
CREATE INDEX IF NOT EXISTS idx_intelligence_score ON lead_intelligence(ai_score DESC);
CREATE INDEX IF NOT EXISTS idx_intelligence_segmento ON lead_intelligence(segmento_detectado);

-- Interactions
CREATE INDEX IF NOT EXISTS idx_interactions_lead ON interactions(lead_id);
CREATE INDEX IF NOT EXISTS idx_interactions_tipo ON interactions(tipo);
CREATE INDEX IF NOT EXISTS idx_interactions_sentimento ON interactions(sentimento);

-- Clientes
CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes_existentes(nome_normalizado);

-- =====================================================
-- TRIGGERS PARA UPDATED_AT
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS leads_updated_at ON leads;
CREATE TRIGGER leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS intelligence_updated_at ON lead_intelligence;
CREATE TRIGGER intelligence_updated_at
    BEFORE UPDATE ON lead_intelligence
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =====================================================
-- RLS (Row Level Security) - Ajuste conforme necessidade
-- =====================================================

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_intelligence ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes_existentes ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_logs ENABLE ROW LEVEL SECURITY;

-- Politicas permissivas (ajuste para producao)
CREATE POLICY "Allow all on leads" ON leads FOR ALL USING (true);
CREATE POLICY "Allow all on lead_intelligence" ON lead_intelligence FOR ALL USING (true);
CREATE POLICY "Allow all on interactions" ON interactions FOR ALL USING (true);
CREATE POLICY "Allow all on clientes_existentes" ON clientes_existentes FOR ALL USING (true);
CREATE POLICY "Allow all on webhook_logs" ON webhook_logs FOR ALL USING (true);

-- =====================================================
-- FIM DO SCHEMA v3.0
-- =====================================================

/**
 * Backend API Client
 * All communication with backend goes through here
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      return { error: error.detail || `HTTP ${response.status}` };
    }

    const data = await response.json();
    return { data };
  } catch (err) {
    return { error: err instanceof Error ? err.message : 'Network error' };
  }
}

// Lead types
export interface Lead {
  id: number;
  nome_empresa: string;
  telefone?: string;
  site?: string;
  endereco?: string;
  cidade: string;
  nota_google?: number;
  nicho: string;
  status: string;
  score: number;
  temperatura?: {
    nivel: string;
    label: string;
    cor: string;
  };
  interacoes?: Array<{
    data: string;
    tipo: string;
    descricao: string;
  }>;
}

export interface LeadCounts {
  novos: number;
  contatado: number;
  interesse: number;
  agendado: number;
  total: number;
}

export interface CampaignProgress {
  job_id: number;
  status: string;
  progresso: number;
  leads_encontrados: number;
  leads_qualificados: number;
  mensagem?: string;
}

// API functions
export const api = {
  // Leads
  getLeads: (filters?: Record<string, any>) => {
    const params = filters ? new URLSearchParams(filters).toString() : '';
    return apiCall<{ total: number; leads: Lead[] }>(`/api/leads${params ? `?${params}` : ''}`);
  },

  getLeadCounts: () => {
    return apiCall<LeadCounts>('/api/leads/counts');
  },

  getLead: (id: number) => {
    return apiCall<Lead>(`/api/leads/${id}`);
  },

  updateLeadStatus: (id: number, status: string) => {
    return apiCall(`/api/leads/${id}/status?status=${status}`, { method: 'POST' });
  },

  addInteraction: (id: number, tipo: string, descricao: string) => {
    return apiCall(`/api/leads/${id}/interaction?tipo=${tipo}&descricao=${encodeURIComponent(descricao)}`, {
      method: 'POST'
    });
  },

  getIcebreaker: (id: number) => {
    return apiCall<{ icebreaker: string }>(`/api/leads/${id}/icebreaker`);
  },

  deleteLeadsByStatus: (status: string) => {
    return apiCall<{ deleted: number; message: string }>(`/api/leads/bulk?status=${status}`, {
      method: 'DELETE',
    });
  },

  sendWhatsApp: (id: number, message: string) => {
    return apiCall<{ status: string; phone: string }>(`/api/leads/${id}/whatsapp?message=${encodeURIComponent(message)}`, {
      method: 'POST',
    });
  },

  sendBulkWhatsApp: (messageTemplate: string, statusFilter: string = 'novo', limit: number = 10) => {
    const params = new URLSearchParams({
      message_template: messageTemplate,
      status_filter: statusFilter,
      limit: String(limit),
    });
    return apiCall<{ status: string; count: number; leads: string[] }>(`/api/leads/whatsapp/bulk?${params}`, {
      method: 'POST',
    });
  },

  // Campaigns
  startCampaign: (nicho: string, cidade: string, limite: number = 20) => {
    return apiCall<{ job_id: number; status: string }>('/api/campaigns/start', {
      method: 'POST',
      body: JSON.stringify({ nicho, cidade, limite }),
    });
  },

  getCampaignStatus: (jobId: number) => {
    return apiCall<CampaignProgress>(`/api/campaigns/${jobId}`);
  },

  // Health
  healthCheck: () => {
    return apiCall<{ status: string; database: string }>('/health');
  },

  // Reactivation
  previewCSV: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${BACKEND_URL}/api/reactivation/preview-csv`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        return { error: error.detail || `HTTP ${response.status}` };
      }

      const data = await response.json();
      return { data };
    } catch (err) {
      return { error: err instanceof Error ? err.message : 'Network error' };
    }
  },

  sendReactivation: async (leads: any[], messageTemplate: string, delaySeconds: number = 45) => {
    const formData = new FormData();
    // Only send minimal data (phone + name) to avoid request size limits
    const minimalLeads = leads.map(l => ({ phone: l.phone, name: l.name }));
    formData.append('leads', JSON.stringify(minimalLeads));
    formData.append('msg1_template', messageTemplate);
    formData.append('delay_seconds', String(delaySeconds));

    try {
      const response = await fetch(`${BACKEND_URL}/api/reactivation/send-bulk`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Send failed' }));
        return { error: error.detail || `HTTP ${response.status}` };
      }

      const data = await response.json();
      return { data };
    } catch (err) {
      return { error: err instanceof Error ? err.message : 'Network error' };
    }
  },

  getReactivationTemplate: () => {
    return apiCall<{ template: string; placeholders: string[]; example: string }>('/api/reactivation/template');
  },

  // Cold Prospecting (SPIN Selling)
  previewColdProspecting: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${BACKEND_URL}/api/cold-prospecting/preview`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        return { error: error.detail || `HTTP ${response.status}` };
      }

      const data = await response.json();
      return { data };
    } catch (err) {
      return { error: err instanceof Error ? err.message : 'Network error' };
    }
  },

  sendColdProspecting: async (leads: any[], delaySeconds: number = 45) => {
    const formData = new FormData();
    const minimalLeads = leads.map(l => ({ phone: l.phone, name: l.name, company: l.company || '' }));
    formData.append('leads', JSON.stringify(minimalLeads));
    formData.append('delay_seconds', String(delaySeconds));

    try {
      const response = await fetch(`${BACKEND_URL}/api/cold-prospecting/send`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Send failed' }));
        return { error: error.detail || `HTTP ${response.status}` };
      }

      const data = await response.json();
      return { data };
    } catch (err) {
      return { error: err instanceof Error ? err.message : 'Network error' };
    }
  },

  getColdCampaignProgress: (campaignId: string) => {
    return apiCall<any>(`/api/cold-prospecting/campaign/${campaignId}`);
  },

  // Kanban / AI Responder
  getKanbanData: () => {
    return apiCall<KanbanResponse>('/api/ai-responder/kanban');
  },

  moveLeadStatus: (phone: string, newStatus: string) => {
    return apiCall<{ status: string; phone: string; new_status: string }>(
      `/api/ai-responder/kanban/move?phone=${encodeURIComponent(phone)}&new_status=${newStatus}`,
      { method: 'POST' }
    );
  },
};

// Kanban types
export interface KanbanLead {
  phone: string;
  name: string;
  company: string;
  campaign_id: string;
  status: string;
  phase: string;
  qualification_progress: number;
  qualification_data: {
    equipamento?: string;
    urgencia?: string;
    cnpj?: string;
    faturamento?: string;
  };
  salesperson_insights: string;
  total_exchanges: number;
  last_message: string;
  last_message_time: string;
  last_contact: string;
  created_at: string;
  updated_at: string;
}

export interface KanbanResponse {
  leads: KanbanLead[];
  columns: {
    novo: KanbanLead[];
    em_conversa: KanbanLead[];
    qualificado: KanbanLead[];
    reuniao_agendada: KanbanLead[];
    curioso: KanbanLead[];
    perdido: KanbanLead[];
  };
  summary: {
    novo: number;
    em_conversa: number;
    qualificado: number;
    reuniao_agendada: number;
    curioso: number;
    perdido: number;
    total: number;
  };
}

export default api;

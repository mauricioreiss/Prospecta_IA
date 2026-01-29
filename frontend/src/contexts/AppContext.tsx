'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api, { Lead, LeadCounts, CampaignProgress } from '@/lib/api';

interface ActiveCall {
  isActive: boolean;
  callId?: string | null;
  leadId?: string | number | null;
  leadName?: string;
  phoneNumber?: string;
  duration?: number;
  status?: string;
  transcript?: Array<{ role: string; text: string }>;
}

interface Niche {
  value: string;
  label: string;
}

interface AppContextType {
  // State
  isLoading: boolean;
  error: string | null;
  leads: Lead[];
  leadCounts: LeadCounts | null;
  activeCall: ActiveCall | null;
  isProspecting: boolean;
  currentCampaign: CampaignProgress | null;

  // Niches
  nichos: Niche[];

  // Actions
  refreshLeads: () => Promise<void>;
  startCampaign: (nicho: string, cidade: string, limite?: number) => Promise<void>;
  updateLeadStatus: (leadId: number, status: string) => Promise<void>;
  deleteLeadsByStatus: (status: string) => Promise<void>;
  setActiveCall: (call: ActiveCall | null) => void;
}

const AppContext = createContext<AppContextType | null>(null);

// Available niches
const NICHOS: Niche[] = [
  { value: 'locadora', label: 'Locadora de Equipamentos' },
  { value: 'autopecas', label: 'Auto Pecas' },
  { value: 'oficina', label: 'Oficina Mecanica' },
  { value: 'clinica', label: 'Clinica/Consultorio' },
  { value: 'restaurante', label: 'Restaurante' },
  { value: 'generico', label: 'Outro Segmento' },
];

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [leadCounts, setLeadCounts] = useState<LeadCounts | null>(null);
  const [activeCall, setActiveCall] = useState<ActiveCall | null>(null);
  const [isProspecting, setIsProspecting] = useState(false);
  const [currentCampaign, setCurrentCampaign] = useState<CampaignProgress | null>(null);

  // Initial load
  useEffect(() => {
    async function init() {
      setIsLoading(true);

      const healthResult = await api.healthCheck();
      if (healthResult.error) {
        setError(`Erro de conexao: ${healthResult.error}`);
        setIsLoading(false);
        return;
      }

      await refreshLeads();
      setIsLoading(false);
    }

    init();
  }, []);

  // Refresh leads and counts
  const refreshLeads = useCallback(async () => {
    const [leadsResult, countsResult] = await Promise.all([
      api.getLeads({ limit: 100 }),
      api.getLeadCounts(),
    ]);

    if (leadsResult.data) {
      setLeads(leadsResult.data.leads);
    }
    if (countsResult.data) {
      setLeadCounts(countsResult.data);
    }
  }, []);

  // Start prospecting campaign
  const startCampaign = useCallback(async (nicho: string, cidade: string, limite: number = 20) => {
    setIsProspecting(true);
    setCurrentCampaign({
      job_id: 0,
      status: 'running',
      progresso: 0,
      leads_encontrados: 0,
      leads_qualificados: 0,
      mensagem: 'Iniciando...',
    });

    const result = await api.startCampaign(nicho, cidade, limite);

    if (result.error) {
      setError(result.error);
      setIsProspecting(false);
      setCurrentCampaign(null);
      return;
    }

    const jobId = result.data!.job_id;

    // Poll for progress
    const poll = async () => {
      const statusResult = await api.getCampaignStatus(jobId);

      if (statusResult.data) {
        setCurrentCampaign(statusResult.data);

        if (statusResult.data.status === 'completed') {
          setIsProspecting(false);
          await refreshLeads();
        } else if (statusResult.data.status === 'failed') {
          setIsProspecting(false);
          setError(statusResult.data.mensagem || 'Erro na prospeccao');
        } else {
          setTimeout(poll, 1000);
        }
      }
    };

    poll();
  }, [refreshLeads]);

  // Update lead status
  const updateLeadStatus = useCallback(async (leadId: number, status: string) => {
    const result = await api.updateLeadStatus(leadId, status);
    if (!result.error) {
      await refreshLeads();
    }
  }, [refreshLeads]);

  // Delete leads by status
  const deleteLeadsByStatus = useCallback(async (status: string) => {
    const result = await api.deleteLeadsByStatus(status);
    if (!result.error) {
      await refreshLeads();
    }
  }, [refreshLeads]);

  return (
    <AppContext.Provider
      value={{
        isLoading,
        error,
        leads,
        leadCounts,
        activeCall,
        isProspecting,
        currentCampaign,
        nichos: NICHOS,
        refreshLeads,
        startCampaign,
        updateLeadStatus,
        deleteLeadsByStatus,
        setActiveCall,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}

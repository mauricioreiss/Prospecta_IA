'use client';

import { useEffect, useState, useCallback } from 'react';
import { ArrowLeft, RefreshCw, Loader2, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useApp } from '@/contexts/AppContext';
import { StatusCardsRow } from '@/components/StatusCard';
import LeadCard from '@/components/LeadCard';
import LiveCallCard from '@/components/LiveCallCard';
import api, { Lead } from '@/lib/api';

type UIStatus = 'novos' | 'contatado' | 'interesse' | 'agendado';

// Map UI status to backend status filters
const STATUS_MAP: Record<UIStatus, string[]> = {
  novos: ['novo', 'contato_site'],
  contatado: ['contatado', 'follow_up'],
  interesse: ['interesse', 'proposta'],
  agendado: ['agendado', 'fechado'],
};

export default function PipelinePage() {
  const { leadCounts, activeCall, refreshLeads, updateLeadStatus, deleteLeadsByStatus } = useApp();

  const [selectedStatus, setSelectedStatus] = useState<UIStatus>('novos');
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showDeleteMenu, setShowDeleteMenu] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load leads when status changes
  const loadLeads = useCallback(async () => {
    setIsLoading(true);
    const statuses = STATUS_MAP[selectedStatus];
    const result = await api.getLeads({
      status: statuses[0],
      limit: 50,
      order_by: 'score',
      order_desc: 'true',
    });
    if (result.data) {
      setLeads(result.data.leads);
    }
    setIsLoading(false);
  }, [selectedStatus]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  const handleWhatsApp = (lead: Lead) => {
    if (lead.telefone) {
      let phone = lead.telefone.replace(/\D/g, '');
      if (!phone.startsWith('55')) {
        phone = '55' + phone;
      }
      window.open(`https://wa.me/${phone}`, '_blank');
    }
  };

  const handleCall = (lead: Lead) => {
    if (lead.telefone) {
      window.location.href = `tel:${lead.telefone}`;
    }
  };

  const handleStatusChange = async (lead: Lead, newStatus: string) => {
    await updateLeadStatus(lead.id, newStatus);
    setLeads(prev => prev.filter(l => l.id !== lead.id));
  };

  const handleRefresh = async () => {
    await refreshLeads();
    await loadLeads();
  };

  const handleDelete = async (status: string) => {
    if (!confirm(`Tem certeza que deseja deletar todos os leads com status "${status}"?`)) {
      return;
    }
    setIsDeleting(true);
    await deleteLeadsByStatus(status);
    await loadLeads();
    setIsDeleting(false);
    setShowDeleteMenu(false);
  };

  const handleDeleteAll = async () => {
    if (!confirm('Tem certeza que deseja deletar TODOS os leads? Esta acao nao pode ser desfeita!')) {
      return;
    }
    setIsDeleting(true);
    await deleteLeadsByStatus('all');
    await loadLeads();
    setIsDeleting(false);
    setShowDeleteMenu(false);
  };

  const counts: Record<UIStatus, number> = {
    novos: leadCounts?.novos || 0,
    contatado: leadCounts?.contatado || 0,
    interesse: leadCounts?.interesse || 0,
    agendado: leadCounts?.agendado || 0,
  };

  // Show Live Call Card when call is active
  if (activeCall?.isActive) {
    return (
      <div className="min-h-screen py-8 px-4">
        <LiveCallCard />
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8 px-4">
      {/* Header */}
      <header className="max-w-6xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-lg text-text-muted hover:text-text transition-colors"
          >
            <ArrowLeft className="w-6 h-6" />
            Voltar
          </Link>
          <h1 className="text-2xl font-bold text-primary">Meu Pipeline</h1>
          <div className="flex items-center gap-2">
            <div className="relative">
              <button
                onClick={() => setShowDeleteMenu(!showDeleteMenu)}
                className="p-3 text-red-500 hover:text-red-700 transition-colors rounded-lg hover:bg-red-50"
                title="Deletar leads"
                disabled={isDeleting}
              >
                {isDeleting ? <Loader2 className="w-6 h-6 animate-spin" /> : <Trash2 className="w-6 h-6" />}
              </button>
              {showDeleteMenu && (
                <div className="absolute right-0 top-full mt-2 bg-white rounded-lg shadow-lg border p-2 min-w-[200px] z-50">
                  <p className="text-sm text-text-muted px-3 py-2 border-b mb-2">Deletar leads por status:</p>
                  <button
                    onClick={() => handleDelete('agendado')}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 rounded"
                  >
                    Agendados
                  </button>
                  <button
                    onClick={() => handleDelete('fechado')}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 rounded"
                  >
                    Fechados
                  </button>
                  <button
                    onClick={() => handleDelete('perdido')}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 rounded"
                  >
                    Perdidos (Sem Interesse)
                  </button>
                  <hr className="my-2" />
                  <button
                    onClick={handleDeleteAll}
                    className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded font-medium"
                  >
                    Deletar TODOS
                  </button>
                </div>
              )}
            </div>
            <button
              onClick={handleRefresh}
              className="p-3 text-text-muted hover:text-text transition-colors rounded-lg hover:bg-gray-100"
              title="Atualizar"
            >
              <RefreshCw className="w-6 h-6" />
            </button>
          </div>
        </div>
      </header>

      {/* Status Cards */}
      <div className="max-w-5xl mx-auto mb-10">
        <StatusCardsRow
          counts={counts}
          selectedStatus={selectedStatus}
          onSelect={setSelectedStatus}
        />
      </div>

      {/* Leads List */}
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-medium text-text">
            {selectedStatus.toUpperCase()} ({leads.length} leads)
          </h2>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-10 h-10 animate-spin text-accent" />
          </div>
        ) : leads.length === 0 ? (
          <div className="card text-center py-16">
            <p className="text-xl text-text-muted mb-6">
              Nenhum lead neste status.
            </p>
            <Link href="/" className="btn btn-primary inline-flex items-center gap-2 text-lg">
              Buscar Novos Leads
            </Link>
          </div>
        ) : (
          <div className="space-y-5">
            {leads.map((lead) => (
              <LeadCard
                key={lead.id}
                lead={lead}
                onCall={() => handleCall(lead)}
                onWhatsApp={() => handleWhatsApp(lead)}
                onStatusChange={(status) => handleStatusChange(lead, status)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

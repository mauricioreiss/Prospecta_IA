'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { ArrowLeft, RefreshCw, Phone, Building2, MessageSquare, Calendar, Star, AlertTriangle, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import api, { KanbanLead, KanbanResponse } from '@/lib/api';

const COLUMNS = [
  { key: 'novo', label: 'Novo', color: 'border-blue-500', bg: 'bg-blue-500/10', badge: 'bg-blue-500' },
  { key: 'em_conversa', label: 'Em Conversa', color: 'border-yellow-500', bg: 'bg-yellow-500/10', badge: 'bg-yellow-500' },
  { key: 'qualificado', label: 'Qualificado (Ouro)', color: 'border-green-500', bg: 'bg-green-500/10', badge: 'bg-green-500' },
  { key: 'reuniao_agendada', label: 'Reuniao Agendada', color: 'border-purple-500', bg: 'bg-purple-500/10', badge: 'bg-purple-500' },
  { key: 'curioso', label: 'Curioso', color: 'border-gray-500', bg: 'bg-gray-500/10', badge: 'bg-gray-500' },
  { key: 'perdido', label: 'Perdido', color: 'border-red-500', bg: 'bg-red-500/10', badge: 'bg-red-500' },
] as const;

type ColumnKey = typeof COLUMNS[number]['key'];

function ProgressBar({ progress }: { progress: number }) {
  const dots = [1, 2, 3, 4];
  return (
    <div className="flex gap-1 items-center">
      {dots.map((d) => (
        <div
          key={d}
          className={`w-2.5 h-2.5 rounded-full ${
            d <= progress ? 'bg-green-500' : 'bg-gray-600'
          }`}
        />
      ))}
      <span className="text-xs text-gray-400 ml-1">{progress}/4</span>
    </div>
  );
}

function LeadCard({ lead, onMove }: { lead: KanbanLead; onMove: (phone: string, status: string) => void }) {
  const [expanded, setExpanded] = useState(false);

  const timeAgo = (dateStr: string) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}min`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h`;
    return `${Math.floor(hours / 24)}d`;
  };

  const qualData = lead.qualification_data || {};

  return (
    <div className="bg-gray-800 rounded-lg p-3 border border-gray-700 hover:border-gray-600 transition-colors">
      {/* Header */}
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="font-semibold text-white text-sm">{lead.name || 'Lead'}</h4>
          {lead.company && (
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <Building2 className="w-3 h-3" />
              {lead.company}
            </div>
          )}
        </div>
        <ProgressBar progress={lead.qualification_progress} />
      </div>

      {/* Phone */}
      <div className="flex items-center gap-1 text-xs text-gray-400 mb-2">
        <Phone className="w-3 h-3" />
        {lead.phone}
      </div>

      {/* Qualification badges */}
      <div className="flex flex-wrap gap-1 mb-2">
        {qualData.equipamento && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/50 text-blue-300">
            {qualData.equipamento}
          </span>
        )}
        {qualData.urgencia && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-orange-900/50 text-orange-300">
            <Clock className="w-3 h-3 inline mr-0.5" />
            {qualData.urgencia}
          </span>
        )}
        {qualData.cnpj && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/50 text-green-300">
            CNPJ
          </span>
        )}
        {qualData.faturamento && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-purple-900/50 text-purple-300">
            {qualData.faturamento}
          </span>
        )}
      </div>

      {/* Last message */}
      {lead.last_message && (
        <div className="text-xs text-gray-500 mb-2 truncate">
          <MessageSquare className="w-3 h-3 inline mr-1" />
          &quot;{lead.last_message}&quot;
        </div>
      )}

      {/* Meta info */}
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>{lead.total_exchanges} trocas</span>
        {lead.updated_at && <span>{timeAgo(lead.updated_at)}</span>}
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full mt-2 text-xs text-gray-500 hover:text-gray-300 flex items-center justify-center gap-1"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {expanded ? 'Menos' : 'Mais detalhes'}
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-gray-700 space-y-3">
          {/* Insights */}
          {lead.salesperson_insights && (
            <div>
              <h5 className="text-xs font-semibold text-yellow-400 mb-1 flex items-center gap-1">
                <Star className="w-3 h-3" />
                Insights para Vendedor
              </h5>
              <pre className="text-xs text-gray-300 whitespace-pre-wrap font-sans">
                {lead.salesperson_insights}
              </pre>
            </div>
          )}

          {/* CNPJ */}
          {qualData.cnpj && (
            <div className="text-xs">
              <span className="text-gray-400">CNPJ:</span>{' '}
              <span className="text-white font-mono">{qualData.cnpj}</span>
            </div>
          )}

          {/* Move actions */}
          <div className="flex flex-wrap gap-1">
            {lead.status !== 'reuniao_agendada' && (
              <button
                onClick={() => onMove(lead.phone, 'reuniao_agendada')}
                className="text-xs px-2 py-1 rounded bg-purple-600 hover:bg-purple-500 text-white flex items-center gap-1"
              >
                <Calendar className="w-3 h-3" />
                Marcar Reuniao
              </button>
            )}
            {lead.status !== 'perdido' && lead.status !== 'curioso' && (
              <button
                onClick={() => onMove(lead.phone, 'perdido')}
                className="text-xs px-2 py-1 rounded bg-red-600/50 hover:bg-red-500 text-white"
              >
                Perdido
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function KanbanPage() {
  const [data, setData] = useState<KanbanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    const result = await api.getKanbanData();
    if (result.data) {
      setData(result.data);
      setError(null);
    } else {
      setError(result.error || 'Erro ao carregar dados');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleMove = async (phone: string, newStatus: string) => {
    await api.moveLeadStatus(phone, newStatus);
    fetchData();
  };

  if (loading && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-400 mb-4">{error}</p>
          <button onClick={fetchData} className="btn btn-primary">
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const columns = data?.columns || {};
  const summary = data?.summary || { total: 0 };

  return (
    <div className="min-h-screen py-6 px-4">
      {/* Header */}
      <header className="max-w-[1600px] mx-auto mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-6 h-6" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white">Pipeline de Leads</h1>
              <p className="text-sm text-gray-400">
                {summary.total || 0} leads no pipeline
              </p>
            </div>
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </div>

        {/* Summary bar */}
        <div className="flex gap-3 mt-4 overflow-x-auto pb-2">
          {COLUMNS.map((col) => {
            const count = (summary as Record<string, number>)[col.key] || 0;
            return (
              <div
                key={col.key}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${col.bg} border ${col.color} text-sm whitespace-nowrap`}
              >
                <div className={`w-2 h-2 rounded-full ${col.badge}`} />
                <span className="text-gray-300">{col.label}</span>
                <span className="font-bold text-white">{count}</span>
              </div>
            );
          })}
        </div>
      </header>

      {/* Kanban Board */}
      <div className="max-w-[1600px] mx-auto overflow-x-auto">
        <div className="flex gap-4 min-w-[1200px] pb-8">
          {COLUMNS.map((col) => {
            const leads = (columns as Record<string, KanbanLead[]>)[col.key] || [];
            return (
              <div key={col.key} className="flex-1 min-w-[250px]">
                {/* Column header */}
                <div className={`border-t-2 ${col.color} bg-gray-900 rounded-t-lg px-3 py-2 mb-2`}>
                  <div className="flex justify-between items-center">
                    <h3 className="font-semibold text-white text-sm">{col.label}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${col.badge} text-white`}>
                      {leads.length}
                    </span>
                  </div>
                </div>

                {/* Cards */}
                <div className="space-y-2">
                  {leads.length === 0 ? (
                    <div className="text-center py-8 text-gray-600 text-sm">
                      Nenhum lead
                    </div>
                  ) : (
                    leads.map((lead) => (
                      <LeadCard
                        key={lead.phone}
                        lead={lead}
                        onMove={handleMove}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

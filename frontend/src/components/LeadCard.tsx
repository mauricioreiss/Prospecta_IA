'use client';

import { useState } from 'react';
import { Phone, MessageCircle, ChevronRight, ChevronDown, MapPin, Star, Globe, Lightbulb, Loader2, X, Send } from 'lucide-react';
import { Lead } from '@/lib/api';
import api from '@/lib/api';

interface LeadCardProps {
  lead: Lead;
  onCall?: () => void;
  onWhatsApp?: () => void;
  onStatusChange?: (status: string) => void;
}

const DEFAULT_MESSAGE_TEMPLATE = `Ola! Notei que a {nome_empresa} tem boas avaliacoes no Google.

Estou entrando em contato porque trabalho ajudando empresas como a sua a aumentar a presenca digital e atrair mais clientes.

Posso te mostrar como outras empresas do segmento estao conseguindo mais visibilidade online?`;

function getScoreColor(score: number | undefined): string {
  if (!score) return 'bg-gray-100 text-gray-600';
  if (score >= 80) return 'score-ouro';
  if (score >= 60) return 'score-prata';
  return 'score-bronze';
}

function getTemperaturaLabel(temp: Lead['temperatura']): string {
  if (!temp) return '';
  return temp.label;
}

function formatPhone(phone: string | undefined): string {
  if (!phone) return '';
  const clean = phone.replace(/\D/g, '').slice(-11);
  if (clean.length === 11) {
    return `(${clean.slice(0, 2)}) ${clean.slice(2, 7)}-${clean.slice(7)}`;
  }
  return phone;
}

const STATUS_OPTIONS = [
  { value: 'novo', label: 'Novo' },
  { value: 'contatado', label: 'Contatado' },
  { value: 'interesse', label: 'Interesse' },
  { value: 'agendado', label: 'Agendado' },
  { value: 'sem_interesse', label: 'Sem Interesse' },
  { value: 'arquivado', label: 'Arquivado' },
];

export default function LeadCard({ lead, onCall, onWhatsApp, onStatusChange }: LeadCardProps) {
  const [icebreaker, setIcebreaker] = useState<string | null>(null);
  const [loadingIcebreaker, setLoadingIcebreaker] = useState(false);
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const [showWhatsAppModal, setShowWhatsAppModal] = useState(false);
  const [whatsAppMessage, setWhatsAppMessage] = useState('');
  const [sendingWhatsApp, setSendingWhatsApp] = useState(false);
  const [whatsAppSent, setWhatsAppSent] = useState(false);

  const hasPhone = !!lead.telefone;
  const hasWebsite = !!lead.site;

  const openWhatsAppModal = () => {
    const message = DEFAULT_MESSAGE_TEMPLATE.replace('{nome_empresa}', lead.nome_empresa);
    setWhatsAppMessage(message);
    setShowWhatsAppModal(true);
  };

  const handleSendWhatsApp = async () => {
    if (!whatsAppMessage.trim() || sendingWhatsApp) return;
    setSendingWhatsApp(true);

    const result = await api.sendWhatsApp(lead.id, whatsAppMessage);

    if (result.data) {
      setWhatsAppSent(true);
      setTimeout(() => {
        setShowWhatsAppModal(false);
        setWhatsAppSent(false);
        onStatusChange?.('contatado');
      }, 1500);
    } else {
      alert(result.error || 'Erro ao enviar WhatsApp');
    }

    setSendingWhatsApp(false);
  };

  const fetchIcebreaker = async () => {
    if (icebreaker || loadingIcebreaker) return;
    setLoadingIcebreaker(true);
    const result = await api.getIcebreaker(lead.id);
    if (result.data?.icebreaker) {
      setIcebreaker(result.data.icebreaker);
    }
    setLoadingIcebreaker(false);
  };

  const handleStatusSelect = (status: string) => {
    setShowStatusMenu(false);
    onStatusChange?.(status);
  };

  return (
    <div className="card hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-bold text-primary">
            {lead.nome_empresa}
          </h3>
          <div className="flex items-center gap-2 text-text-muted mt-1">
            <MapPin className="w-5 h-5" />
            <span className="text-lg">{lead.endereco || lead.cidade}</span>
          </div>
        </div>
        <div className="text-right">
          <div className={`px-4 py-2 rounded-full text-xl font-bold ${getScoreColor(lead.score)}`}>
            {lead.score || '--'}
          </div>
          {lead.temperatura && (
            <span className="text-sm text-text-muted mt-1 block">
              {getTemperaturaLabel(lead.temperatura)}
            </span>
          )}
        </div>
      </div>

      {/* Rating */}
      {lead.nota_google && (
        <div className="flex items-center gap-2 text-text-muted mb-4">
          <Star className="w-6 h-6 fill-yellow-400 text-yellow-400" />
          <span className="text-lg font-medium">{lead.nota_google.toFixed(1)}</span>
          <span className="text-base">no Google</span>
        </div>
      )}

      {/* Contact Info */}
      <div className="flex flex-wrap items-center gap-4 text-text mb-4">
        {hasPhone && (
          <div className="flex items-center gap-2">
            <Phone className="w-5 h-5 text-accent" />
            <span className="text-lg font-medium">{formatPhone(lead.telefone)}</span>
          </div>
        )}
        {hasWebsite && (
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-accent" />
            <a
              href={lead.site?.startsWith('http') ? lead.site : `https://${lead.site}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline truncate max-w-[200px]"
            >
              {lead.site?.replace(/^https?:\/\//, '')}
            </a>
          </div>
        )}
      </div>

      {/* Icebreaker */}
      {icebreaker ? (
        <div className="flex items-start gap-3 bg-yellow-50 text-yellow-900 p-4 rounded-xl mb-5">
          <Lightbulb className="w-6 h-6 flex-shrink-0 mt-0.5" />
          <span className="text-base leading-relaxed">{icebreaker}</span>
        </div>
      ) : (
        <button
          onClick={fetchIcebreaker}
          disabled={loadingIcebreaker}
          className="flex items-center gap-2 text-accent hover:underline mb-5 text-lg"
        >
          {loadingIcebreaker ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Buscando insight...
            </>
          ) : (
            <>
              <Lightbulb className="w-5 h-5" />
              Ver insight para abordagem
            </>
          )}
        </button>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        {hasPhone && (
          <>
            <button
              onClick={onCall}
              className="btn btn-primary flex items-center gap-2"
            >
              <Phone className="w-6 h-6" />
              Ligar
            </button>
            <button
              onClick={openWhatsAppModal}
              className="btn btn-secondary flex items-center gap-2"
            >
              <MessageCircle className="w-6 h-6" />
              WhatsApp
            </button>
          </>
        )}

        {/* Status Change Dropdown */}
        <div className="relative ml-auto">
          <button
            onClick={() => setShowStatusMenu(!showStatusMenu)}
            className="btn btn-outline flex items-center gap-2"
          >
            Mover para...
            <ChevronDown className={`w-5 h-5 transition-transform ${showStatusMenu ? 'rotate-180' : ''}`} />
          </button>

          {showStatusMenu && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-xl border z-10">
              {STATUS_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleStatusSelect(option.value)}
                  disabled={option.value === lead.status}
                  className={`
                    w-full text-left px-4 py-3 text-lg hover:bg-gray-50 first:rounded-t-xl last:rounded-b-xl
                    ${option.value === lead.status ? 'text-gray-400 cursor-not-allowed' : 'text-text'}
                  `}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* WhatsApp Modal */}
      {showWhatsAppModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b bg-green-500 text-white">
              <div className="flex items-center gap-3">
                <MessageCircle className="w-6 h-6" />
                <div>
                  <h3 className="font-bold">Enviar WhatsApp</h3>
                  <p className="text-sm opacity-90">{lead.nome_empresa}</p>
                </div>
              </div>
              <button
                onClick={() => setShowWhatsAppModal(false)}
                className="p-1 hover:bg-white/20 rounded"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-4">
              {whatsAppSent ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Send className="w-8 h-8 text-green-600" />
                  </div>
                  <p className="text-xl font-bold text-green-600">Mensagem enviada!</p>
                </div>
              ) : (
                <>
                  <label className="block text-sm font-medium text-gray-600 mb-2">
                    Mensagem para {formatPhone(lead.telefone)}:
                  </label>
                  <textarea
                    value={whatsAppMessage}
                    onChange={(e) => setWhatsAppMessage(e.target.value)}
                    className="w-full h-48 p-3 border rounded-xl resize-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                    placeholder="Digite sua mensagem..."
                  />
                  <p className="text-sm text-gray-500 mt-2">
                    A mensagem sera enviada via n8n para o Uazap.
                  </p>
                </>
              )}
            </div>

            {/* Modal Footer */}
            {!whatsAppSent && (
              <div className="flex gap-3 p-4 border-t bg-gray-50">
                <button
                  onClick={() => setShowWhatsAppModal(false)}
                  className="btn btn-outline flex-1"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSendWhatsApp}
                  disabled={sendingWhatsApp || !whatsAppMessage.trim()}
                  className="btn bg-green-500 hover:bg-green-600 text-white flex-1 flex items-center justify-center gap-2"
                >
                  {sendingWhatsApp ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      Enviar
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

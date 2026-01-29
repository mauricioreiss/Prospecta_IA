'use client';

import { useState, useCallback } from 'react';
import {
  Upload,
  FileSpreadsheet,
  Users,
  MessageSquare,
  Send,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X,
  Edit3,
  Eye,
  Clock,
  Zap,
  ShieldCheck,
  ShieldAlert,
  Ban,
  UserX,
  Copy
} from 'lucide-react';
import api from '@/lib/api';

interface ReactivationLead {
  name: string;
  phone: string;
  notes: string;
  company?: string;
  preview_message?: string;
  original_status?: string;
}

interface SkippedLead {
  name: string;
  phone: string;
  company?: string;
  status?: string;
  reason?: string;
}

interface SafetyReport {
  skipped_fechado: number;
  skipped_fechado_list: SkippedLead[];
  already_contacted: number;
  already_contacted_list: SkippedLead[];
  duplicates_removed: number;
  no_phone: number;
  total_original: number;
}

interface PreviewData {
  total_leads: number;
  preview: ReactivationLead[];
  all_leads: ReactivationLead[];
  default_template: string;
  safety_report?: SafetyReport;
}

type Step = 'upload' | 'preview' | 'edit' | 'sending' | 'success' | 'error';

export default function ReactivationCampaign() {
  const [step, setStep] = useState<Step>('upload');
  const [isDragging, setIsDragging] = useState(false);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [messageTemplate, setMessageTemplate] = useState('');
  const [delaySeconds, setDelaySeconds] = useState(45);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [selectedPreviewLead, setSelectedPreviewLead] = useState<ReactivationLead | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleFileUpload = async (file: File) => {
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const hasValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!hasValidExtension) {
      setError('Por favor, selecione um arquivo CSV ou Excel (.xlsx)');
      return;
    }

    setLoading(true);
    setError(null);

    const result = await api.previewCSV(file);

    if (result.data) {
      setPreviewData(result.data);
      setMessageTemplate(result.data.default_template);
      setStep('preview');
    } else {
      setError(result.error || 'Erro ao processar arquivo');
    }

    setLoading(false);
  };

  const formatMessage = (template: string, lead: ReactivationLead) => {
    return template
      .replace('[NAME]', lead.name)
      .replace('[NOTES]', lead.notes)
      .replace('[COMPANY]', lead.company || '')
      .replace('{name}', lead.name)
      .replace('{notes}', lead.notes)
      .replace('{company}', lead.company || '');
  };

  const handleSendCampaign = async () => {
    if (!previewData) return;

    setStep('sending');
    setError(null);

    const result = await api.sendReactivation(
      previewData.all_leads,
      messageTemplate,
      delaySeconds
    );

    if (result.data) {
      setResult(result.data);
      setStep('success');
    } else {
      setError(result.error || 'Erro ao enviar campanha');
      setStep('error');
    }
  };

  const resetCampaign = () => {
    setStep('upload');
    setPreviewData(null);
    setMessageTemplate('');
    setError(null);
    setResult(null);
    setSelectedPreviewLead(null);
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-3 bg-gradient-to-r from-orange-500 to-red-500 text-white px-6 py-3 rounded-full mb-4">
          <Zap className="w-6 h-6" />
          <span className="text-xl font-bold">Campanha de Reativacao</span>
        </div>
        <p className="text-text-muted text-lg">
          Reative leads antigos com mensagens personalizadas via WhatsApp
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex justify-center gap-2 mb-8">
        {['upload', 'preview', 'edit', 'sending'].map((s, i) => (
          <div
            key={s}
            className={`w-3 h-3 rounded-full transition-all ${
              step === s ? 'bg-primary w-8' :
              ['upload', 'preview', 'edit', 'sending'].indexOf(step) > i
                ? 'bg-green-500' : 'bg-gray-300'
            }`}
          />
        ))}
      </div>

      {/* Step: Upload */}
      {step === 'upload' && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-3 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer
            ${isDragging
              ? 'border-primary bg-primary/5 scale-[1.02]'
              : 'border-gray-300 hover:border-primary hover:bg-gray-50'
            }
          `}
        >
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileSelect}
            className="hidden"
            id="csv-upload"
          />
          <label htmlFor="csv-upload" className="cursor-pointer">
            {loading ? (
              <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-16 h-16 text-primary animate-spin" />
                <p className="text-xl text-text-muted">Processando arquivo...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
                  <FileSpreadsheet className="w-10 h-10 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-text mb-2">
                    Arraste seu arquivo aqui
                  </p>
                  <p className="text-text-muted text-lg">
                    CSV ou Excel (.xlsx)
                  </p>
                </div>
                <div className="mt-4 px-6 py-2 bg-gray-100 rounded-full text-sm text-text-muted">
                  Colunas: Dono(s), Empresa, Telefone, Resultado, Resumo
                </div>
              </div>
            )}
          </label>
        </div>
      )}

      {/* Step: Preview */}
      {step === 'preview' && previewData && (
        <div className="space-y-6">
          {/* Safety Report - IMPORTANTE */}
          {previewData.safety_report && (
            <div className="card bg-gradient-to-r from-emerald-50 to-green-50 border-2 border-emerald-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center">
                  <ShieldCheck className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-emerald-800">Verificacao de Seguranca</h3>
                  <p className="text-sm text-emerald-600">
                    {previewData.safety_report.total_original} leads no CSV →{' '}
                    <strong>{previewData.total_leads}</strong> serao contatados
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {/* Leads OK */}
                <div className="bg-green-100 rounded-xl p-3 text-center">
                  <CheckCircle2 className="w-6 h-6 text-green-600 mx-auto mb-1" />
                  <p className="text-2xl font-bold text-green-700">{previewData.total_leads}</p>
                  <p className="text-xs text-green-600">Leads OK</p>
                </div>

                {/* Bloqueados FECHADO */}
                <div className={`rounded-xl p-3 text-center ${
                  previewData.safety_report.skipped_fechado > 0
                    ? 'bg-red-100'
                    : 'bg-gray-100'
                }`}>
                  <Ban className={`w-6 h-6 mx-auto mb-1 ${
                    previewData.safety_report.skipped_fechado > 0
                      ? 'text-red-600'
                      : 'text-gray-400'
                  }`} />
                  <p className={`text-2xl font-bold ${
                    previewData.safety_report.skipped_fechado > 0
                      ? 'text-red-700'
                      : 'text-gray-500'
                  }`}>
                    {previewData.safety_report.skipped_fechado}
                  </p>
                  <p className={`text-xs ${
                    previewData.safety_report.skipped_fechado > 0
                      ? 'text-red-600'
                      : 'text-gray-500'
                  }`}>
                    FECHADO (bloqueado)
                  </p>
                </div>

                {/* Ja contatados */}
                <div className={`rounded-xl p-3 text-center ${
                  previewData.safety_report.already_contacted > 0
                    ? 'bg-yellow-100'
                    : 'bg-gray-100'
                }`}>
                  <UserX className={`w-6 h-6 mx-auto mb-1 ${
                    previewData.safety_report.already_contacted > 0
                      ? 'text-yellow-600'
                      : 'text-gray-400'
                  }`} />
                  <p className={`text-2xl font-bold ${
                    previewData.safety_report.already_contacted > 0
                      ? 'text-yellow-700'
                      : 'text-gray-500'
                  }`}>
                    {previewData.safety_report.already_contacted}
                  </p>
                  <p className={`text-xs ${
                    previewData.safety_report.already_contacted > 0
                      ? 'text-yellow-600'
                      : 'text-gray-500'
                  }`}>
                    Ja contatados
                  </p>
                </div>

                {/* Duplicados */}
                <div className={`rounded-xl p-3 text-center ${
                  previewData.safety_report.duplicates_removed > 0
                    ? 'bg-blue-100'
                    : 'bg-gray-100'
                }`}>
                  <Copy className={`w-6 h-6 mx-auto mb-1 ${
                    previewData.safety_report.duplicates_removed > 0
                      ? 'text-blue-600'
                      : 'text-gray-400'
                  }`} />
                  <p className={`text-2xl font-bold ${
                    previewData.safety_report.duplicates_removed > 0
                      ? 'text-blue-700'
                      : 'text-gray-500'
                  }`}>
                    {previewData.safety_report.duplicates_removed}
                  </p>
                  <p className={`text-xs ${
                    previewData.safety_report.duplicates_removed > 0
                      ? 'text-blue-600'
                      : 'text-gray-500'
                  }`}>
                    Duplicados
                  </p>
                </div>
              </div>

              {/* Detalhes dos bloqueados */}
              {previewData.safety_report.skipped_fechado > 0 && (
                <details className="mt-4">
                  <summary className="text-sm text-red-600 cursor-pointer hover:text-red-800 font-medium">
                    Ver {previewData.safety_report.skipped_fechado} leads FECHADO bloqueados
                  </summary>
                  <div className="mt-2 bg-red-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                    {previewData.safety_report.skipped_fechado_list.map((lead, i) => (
                      <div key={i} className="text-xs text-red-700 py-1 border-b border-red-100 last:border-0">
                        <strong>{lead.name}</strong> - {lead.company} ({lead.status})
                      </div>
                    ))}
                  </div>
                </details>
              )}

              {previewData.safety_report.already_contacted > 0 && (
                <details className="mt-2">
                  <summary className="text-sm text-yellow-600 cursor-pointer hover:text-yellow-800 font-medium">
                    Ver {previewData.safety_report.already_contacted} leads ja contatados recentemente
                  </summary>
                  <div className="mt-2 bg-yellow-50 rounded-lg p-3 max-h-32 overflow-y-auto">
                    {previewData.safety_report.already_contacted_list.map((lead, i) => (
                      <div key={i} className="text-xs text-yellow-700 py-1 border-b border-yellow-100 last:border-0">
                        <strong>{lead.name}</strong> - {lead.phone}
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          )}

          {/* Stats Cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <div className="flex items-center gap-3">
                <Users className="w-8 h-8 opacity-80" />
                <div>
                  <p className="text-3xl font-bold">{previewData.total_leads}</p>
                  <p className="text-blue-100">Leads a enviar</p>
                </div>
              </div>
            </div>
            <div className="card bg-gradient-to-br from-green-500 to-green-600 text-white">
              <div className="flex items-center gap-3">
                <MessageSquare className="w-8 h-8 opacity-80" />
                <div>
                  <p className="text-3xl font-bold">{previewData.total_leads}</p>
                  <p className="text-green-100">Mensagens</p>
                </div>
              </div>
            </div>
            <div className="card bg-gradient-to-br from-orange-500 to-orange-600 text-white">
              <div className="flex items-center gap-3">
                <Clock className="w-8 h-8 opacity-80" />
                <div>
                  <p className="text-3xl font-bold">
                    ~{Math.ceil((previewData.total_leads * delaySeconds) / 60)}min
                  </p>
                  <p className="text-orange-100">Tempo estimado</p>
                </div>
              </div>
            </div>
          </div>

          {/* Preview Table */}
          <div className="card">
            <h3 className="text-xl font-bold text-text mb-4 flex items-center gap-2">
              <Eye className="w-6 h-6 text-primary" />
              Preview dos Leads
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold text-text-muted">Nome</th>
                    <th className="text-left py-3 px-4 font-semibold text-text-muted">Telefone</th>
                    <th className="text-left py-3 px-4 font-semibold text-text-muted">Dificuldade/Notas</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">Preview</th>
                  </tr>
                </thead>
                <tbody>
                  {previewData.preview.map((lead, i) => (
                    <tr key={i} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{lead.name}</td>
                      <td className="py-3 px-4 text-text-muted">{lead.phone}</td>
                      <td className="py-3 px-4 text-text-muted truncate max-w-[200px]">
                        {lead.notes}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => setSelectedPreviewLead(lead)}
                          className="text-primary hover:underline flex items-center gap-1 mx-auto"
                        >
                          <Eye className="w-4 h-4" />
                          Ver
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {previewData.total_leads > 5 && (
              <p className="text-center text-text-muted mt-4">
                ... e mais {previewData.total_leads - 5} leads
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button onClick={resetCampaign} className="btn btn-outline flex-1">
              <X className="w-5 h-5 mr-2" />
              Cancelar
            </button>
            <button onClick={() => setStep('edit')} className="btn btn-primary flex-1">
              <Edit3 className="w-5 h-5 mr-2" />
              Editar Mensagem
            </button>
          </div>
        </div>
      )}

      {/* Step: Edit Message */}
      {step === 'edit' && previewData && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-xl font-bold text-text mb-4 flex items-center gap-2">
              <Edit3 className="w-6 h-6 text-primary" />
              Personalize sua Mensagem
            </h3>

            <div className="mb-4">
              <label className="block text-sm font-medium text-text-muted mb-2">
                Use os marcadores: <code className="bg-gray-100 px-2 py-1 rounded">[NAME]</code>{' '}
                <code className="bg-gray-100 px-2 py-1 rounded">[NOTES]</code>{' '}
                <code className="bg-gray-100 px-2 py-1 rounded">[COMPANY]</code>
              </label>
              <textarea
                value={messageTemplate}
                onChange={(e) => setMessageTemplate(e.target.value)}
                className="w-full h-64 p-4 border rounded-xl resize-none focus:ring-2 focus:ring-primary focus:border-primary font-mono text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-muted mb-2">
                  Intervalo entre mensagens (segundos)
                </label>
                <input
                  type="number"
                  min={30}
                  max={120}
                  value={delaySeconds}
                  onChange={(e) => setDelaySeconds(Math.max(30, Math.min(120, parseInt(e.target.value) || 45)))}
                  className="input"
                />
                <p className="text-xs text-text-muted mt-1">
                  Minimo 30s para evitar bloqueio
                </p>
              </div>
              <div className="flex items-end">
                <div className="bg-orange-50 text-orange-800 px-4 py-3 rounded-xl w-full">
                  <p className="font-semibold">Tempo total estimado:</p>
                  <p className="text-2xl font-bold">
                    {Math.ceil((previewData.total_leads * delaySeconds) / 60)} minutos
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Live Preview */}
          <div className="card bg-green-50 border-green-200">
            <h4 className="text-lg font-bold text-green-800 mb-3 flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Preview da Mensagem
            </h4>
            <div className="bg-white rounded-xl p-4 shadow-inner whitespace-pre-wrap text-sm">
              {formatMessage(messageTemplate, previewData.preview[0] || {
                name: 'Carlos',
                notes: 'conseguir mais clientes',
                company: 'Empresa XYZ'
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button onClick={() => setStep('preview')} className="btn btn-outline flex-1">
              Voltar
            </button>
            <button
              onClick={handleSendCampaign}
              className="btn bg-green-500 hover:bg-green-600 text-white flex-1 flex items-center justify-center gap-2"
            >
              <Send className="w-5 h-5" />
              Enviar para {previewData.total_leads} Leads
            </button>
          </div>
        </div>
      )}

      {/* Step: Sending */}
      {step === 'sending' && (
        <div className="card text-center py-12">
          <div className="w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <Loader2 className="w-12 h-12 text-primary animate-spin" />
          </div>
          <h3 className="text-2xl font-bold text-text mb-2">Enviando Campanha...</h3>
          <p className="text-text-muted text-lg">
            Aguarde enquanto as mensagens sao enfileiradas
          </p>
        </div>
      )}

      {/* Step: Success */}
      {step === 'success' && result && (
        <div className="card text-center py-12">
          <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-12 h-12 text-green-600" />
          </div>
          <h3 className="text-2xl font-bold text-green-600 mb-2">Campanha Enviada!</h3>
          <p className="text-text-muted text-lg mb-6">
            {result.total} mensagens foram enfileiradas para envio
          </p>
          <div className="bg-green-50 rounded-xl p-4 max-w-md mx-auto mb-6">
            <p className="text-green-800">
              <strong>Tempo estimado:</strong> {result.estimated_time_minutes} minutos
            </p>
            <p className="text-green-700 text-sm mt-1">
              As mensagens serao enviadas via n8n/Uazap com intervalo de {delaySeconds}s
            </p>
          </div>
          <button onClick={resetCampaign} className="btn btn-primary">
            Nova Campanha
          </button>
        </div>
      )}

      {/* Step: Error */}
      {step === 'error' && (
        <div className="card text-center py-12">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-12 h-12 text-red-600" />
          </div>
          <h3 className="text-2xl font-bold text-red-600 mb-2">Erro ao Enviar</h3>
          <p className="text-text-muted text-lg mb-6">{error}</p>
          <div className="flex gap-4 justify-center">
            <button onClick={resetCampaign} className="btn btn-outline">
              Tentar Novamente
            </button>
            <button onClick={() => setStep('edit')} className="btn btn-primary">
              Voltar e Editar
            </button>
          </div>
        </div>
      )}

      {/* Error Toast */}
      {error && step === 'upload' && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white px-6 py-4 rounded-xl shadow-lg flex items-center gap-3">
          <AlertCircle className="w-6 h-6" />
          <span>{error}</span>
          <button onClick={() => setError(null)}>
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Message Preview Modal */}
      {selectedPreviewLead && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full">
            <div className="flex items-center justify-between p-4 border-b bg-green-500 text-white rounded-t-2xl">
              <div>
                <h3 className="font-bold">Preview: {selectedPreviewLead.name}</h3>
                <p className="text-sm opacity-90">{selectedPreviewLead.phone}</p>
              </div>
              <button onClick={() => setSelectedPreviewLead(null)}>
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-4">
              <div className="bg-green-50 rounded-xl p-4 whitespace-pre-wrap text-sm">
                {formatMessage(messageTemplate || previewData?.default_template || '', selectedPreviewLead)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

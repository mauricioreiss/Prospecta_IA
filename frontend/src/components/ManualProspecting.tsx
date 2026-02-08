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
  Target,
  Copy,
  ArrowLeft
} from 'lucide-react';
import api from '@/lib/api';

// =====================================================
// Types
// =====================================================

interface Lead {
  name: string;
  phone: string;
  company?: string;
  notes?: string;
  preview_msg1?: string;
  preview_msg2?: string;
  original_status?: string;
}

interface SafetyReport {
  sendable?: number;
  already_contacted?: number;
  already_contacted_list?: any[];
  duplicates_removed?: number;
  duplicates_list?: any[];
  no_phone?: number;
  total_in_file?: number;
  total_original?: number;
  skipped_fechado?: number;
  skipped_fechado_list?: any[];
  sheets_processed?: any[];
  sheets_skipped?: any[];
}

interface PreviewData {
  total_leads: number;
  preview: Lead[];
  all_leads: Lead[];
  default_template?: string;
  safety_report?: SafetyReport;
}

type Mode = 'spin' | 'custom';
type Step = 'mode' | 'upload' | 'preview' | 'edit' | 'sending' | 'success' | 'error';

// =====================================================
// Component
// =====================================================

export default function ManualProspecting() {
  const [mode, setMode] = useState<Mode | null>(null);
  const [step, setStep] = useState<Step>('mode');
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [messageTemplate, setMessageTemplate] = useState('');
  const [msg2Template, setMsg2Template] = useState('');
  const [delaySeconds, setDelaySeconds] = useState(45);
  const [result, setResult] = useState<any>(null);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  // =====================================================
  // File handling
  // =====================================================

  const handleFile = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);

    try {
      let response;
      if (mode === 'spin') {
        response = await api.previewColdProspecting(file);
      } else {
        response = await api.previewCSV(file);
      }

      if (response.error) {
        setError(response.error);
        return;
      }

      setPreviewData(response.data);

      if (mode === 'custom' && response.data?.default_template) {
        setMessageTemplate(response.data.default_template);
      }

      setStep('preview');
    } catch (e: any) {
      setError(e.message || 'Erro ao processar arquivo');
    } finally {
      setLoading(false);
    }
  }, [mode]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  // =====================================================
  // Send
  // =====================================================

  const handleSend = async () => {
    if (!previewData) return;
    setStep('sending');

    try {
      let response;
      if (mode === 'spin') {
        response = await api.sendColdProspecting(previewData.all_leads, delaySeconds);
      } else {
        response = await api.sendReactivation(
          previewData.all_leads,
          messageTemplate,
          delaySeconds
        );
      }

      if (response.error) {
        setError(response.error);
        setStep('error');
        return;
      }

      setResult(response.data);
      setStep('success');
    } catch (e: any) {
      setError(e.message || 'Erro ao enviar');
      setStep('error');
    }
  };

  // =====================================================
  // Reset
  // =====================================================

  const reset = () => {
    setMode(null);
    setStep('mode');
    setPreviewData(null);
    setMessageTemplate('');
    setMsg2Template('');
    setError(null);
    setResult(null);
    setSelectedLead(null);
  };

  const formatMessage = (template: string, lead: Lead) => {
    return template
      .replace(/\[NAME\]/g, lead.name || 'Amigo')
      .replace(/\[NOTES\]/g, lead.notes || 'crescer o negocio')
      .replace(/\[COMPANY\]/g, lead.company || '')
      .replace(/\{name\}/g, lead.name || 'Amigo')
      .replace(/\{notes\}/g, lead.notes || 'crescer o negocio')
      .replace(/\{company\}/g, lead.company || '');
  };

  // =====================================================
  // Step indicators
  // =====================================================

  const steps = mode === 'custom'
    ? ['Modo', 'Upload', 'Preview', 'Editar', 'Enviar']
    : ['Modo', 'Upload', 'Preview', 'Enviar'];

  const stepIndex = {
    mode: 0,
    upload: 1,
    preview: 2,
    edit: 3,
    sending: mode === 'custom' ? 4 : 3,
    success: mode === 'custom' ? 4 : 3,
    error: mode === 'custom' ? 4 : 3,
  };

  // =====================================================
  // RENDER: Mode Selection
  // =====================================================

  if (step === 'mode') {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text mb-2">Prospecção Manual</h1>
          <p className="text-text-muted">Escolha o modo de envio para seus leads</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* SPIN Selling Card */}
          <button
            onClick={() => { setMode('spin'); setStep('upload'); }}
            className="card p-8 text-left hover:shadow-xl hover:scale-[1.02] transition-all border-2 border-transparent hover:border-orange-500 group"
          >
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center mb-4">
              <Target className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-xl font-bold text-text mb-2">SPIN Selling</h2>
            <p className="text-text-muted text-sm mb-4">
              Mensagens automáticas de isca + IA conversa com o lead para fechar reunião.
            </p>
            <div className="space-y-2 text-xs text-text-muted">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>MSG 1: &quot;Oi [nome], tudo bem? João aqui.&quot;</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>MSG 2: &quot;Vi a [empresa] no Google...&quot;</span>
              </div>
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-orange-500" />
                <span>IA responde automaticamente usando SPIN</span>
              </div>
            </div>
          </button>

          {/* Custom Message Card */}
          <button
            onClick={() => { setMode('custom'); setStep('upload'); }}
            className="card p-8 text-left hover:shadow-xl hover:scale-[1.02] transition-all border-2 border-transparent hover:border-blue-500 group"
          >
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center mb-4">
              <Edit3 className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-xl font-bold text-text mb-2">Mensagem Específica</h2>
            <p className="text-text-muted text-sm mb-4">
              Você escreve a mensagem personalizada para enviar aos leads.
            </p>
            <div className="space-y-2 text-xs text-text-muted">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>Você define o texto da mensagem</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>Placeholders: [NAME], [COMPANY], [NOTES]</span>
              </div>
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-blue-500" />
                <span>Ideal para campanhas específicas</span>
              </div>
            </div>
          </button>
        </div>
      </div>
    );
  }

  // =====================================================
  // RENDER: Upload
  // =====================================================

  if (step === 'upload') {
    return (
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <button onClick={reset} className="text-text-muted hover:text-primary transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-text">
              {mode === 'spin' ? 'SPIN Selling' : 'Mensagem Específica'}
            </h1>
            <p className="text-text-muted text-sm">Faça upload do arquivo com os leads</p>
          </div>
          <div className={`ml-auto px-3 py-1 rounded-full text-xs font-medium ${
            mode === 'spin'
              ? 'bg-orange-500/10 text-orange-500'
              : 'bg-blue-500/10 text-blue-500'
          }`}>
            {mode === 'spin' ? 'SPIN' : 'Custom'}
          </div>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-2 mb-8">
          {steps.map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                i < stepIndex[step] ? 'bg-green-500 text-white' :
                i === stepIndex[step] ? (mode === 'spin' ? 'bg-orange-500' : 'bg-blue-500') + ' text-white' :
                'bg-surface text-text-muted'
              }`}>
                {i < stepIndex[step] ? '✓' : i + 1}
              </div>
              <span className="text-xs text-text-muted hidden sm:inline">{s}</span>
              {i < steps.length - 1 && <div className="w-8 h-0.5 bg-surface" />}
            </div>
          ))}
        </div>

        {/* Drop Zone */}
        <div
          className={`card p-12 text-center border-3 border-dashed transition-all cursor-pointer ${
            isDragging
              ? 'border-primary bg-primary/5 scale-[1.02]'
              : 'border-text-muted/30 hover:border-primary/50'
          }`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          onClick={() => document.getElementById('file-upload')?.click()}
        >
          <input
            id="file-upload"
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={onFileSelect}
          />

          {loading ? (
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-12 h-12 text-primary animate-spin" />
              <p className="text-text-muted">Processando arquivo...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-surface flex items-center justify-center">
                <Upload className="w-8 h-8 text-text-muted" />
              </div>
              <div>
                <p className="text-text font-medium">Arraste o arquivo aqui ou clique para selecionar</p>
                <p className="text-text-muted text-sm mt-1">CSV ou Excel (.xlsx) com colunas: Nome, Telefone, Empresa</p>
              </div>
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <FileSpreadsheet className="w-4 h-4" />
                <span>CSV, XLSX, XLS</span>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
            <AlertCircle className="w-4 h-4 inline mr-2" />
            {error}
          </div>
        )}
      </div>
    );
  }

  // =====================================================
  // RENDER: Preview
  // =====================================================

  if (step === 'preview' && previewData) {
    const report = previewData.safety_report;
    const totalOriginal = report?.total_original || report?.total_in_file || previewData.total_leads;

    return (
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <button onClick={() => setStep('upload')} className="text-text-muted hover:text-primary transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-text">Preview dos Leads</h1>
            <p className="text-text-muted text-sm">{previewData.total_leads} leads prontos para envio</p>
          </div>
        </div>

        {/* Safety Report */}
        {report && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <div className="card p-3 text-center border-l-4 border-green-500">
              <p className="text-2xl font-bold text-green-500">{previewData.total_leads}</p>
              <p className="text-xs text-text-muted">Leads OK</p>
            </div>
            <div className="card p-3 text-center border-l-4 border-yellow-500">
              <p className="text-2xl font-bold text-yellow-500">{report.already_contacted || 0}</p>
              <p className="text-xs text-text-muted">Já contatados</p>
            </div>
            <div className="card p-3 text-center border-l-4 border-blue-500">
              <p className="text-2xl font-bold text-blue-500">{report.duplicates_removed || 0}</p>
              <p className="text-xs text-text-muted">Duplicatas</p>
            </div>
            <div className="card p-3 text-center border-l-4 border-gray-500">
              <p className="text-2xl font-bold text-gray-400">{report.no_phone || 0}</p>
              <p className="text-xs text-text-muted">Sem telefone</p>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className={`card p-4 text-center bg-gradient-to-br ${
            mode === 'spin' ? 'from-orange-500/10 to-red-500/10' : 'from-blue-500/10 to-indigo-500/10'
          }`}>
            <Users className="w-6 h-6 mx-auto mb-1 text-text-muted" />
            <p className="text-2xl font-bold text-text">{previewData.total_leads}</p>
            <p className="text-xs text-text-muted">Leads</p>
          </div>
          <div className={`card p-4 text-center bg-gradient-to-br ${
            mode === 'spin' ? 'from-orange-500/10 to-red-500/10' : 'from-blue-500/10 to-indigo-500/10'
          }`}>
            <MessageSquare className="w-6 h-6 mx-auto mb-1 text-text-muted" />
            <p className="text-2xl font-bold text-text">{previewData.total_leads * 2}</p>
            <p className="text-xs text-text-muted">Mensagens</p>
          </div>
          <div className={`card p-4 text-center bg-gradient-to-br ${
            mode === 'spin' ? 'from-orange-500/10 to-red-500/10' : 'from-blue-500/10 to-indigo-500/10'
          }`}>
            <Clock className="w-6 h-6 mx-auto mb-1 text-text-muted" />
            <p className="text-2xl font-bold text-text">{Math.ceil((previewData.total_leads * delaySeconds) / 60)}</p>
            <p className="text-xs text-text-muted">Minutos</p>
          </div>
        </div>

        {/* Preview Table */}
        <div className="card p-4 mb-6">
          <h3 className="font-medium text-text mb-3 flex items-center gap-2">
            <Eye className="w-4 h-4" />
            Amostra ({previewData.preview.length} leads)
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface">
                  <th className="text-left p-2 text-text-muted">Nome</th>
                  <th className="text-left p-2 text-text-muted">Telefone</th>
                  <th className="text-left p-2 text-text-muted">Empresa</th>
                  <th className="text-center p-2 text-text-muted">Preview</th>
                </tr>
              </thead>
              <tbody>
                {previewData.preview.map((lead, i) => (
                  <tr key={i} className="border-b border-surface/50">
                    <td className="p-2 text-text">{lead.name}</td>
                    <td className="p-2 text-text-muted">{lead.phone}</td>
                    <td className="p-2 text-text-muted">{lead.company || '-'}</td>
                    <td className="p-2 text-center">
                      <button
                        onClick={() => setSelectedLead(lead)}
                        className="text-primary hover:underline text-xs"
                      >
                        Ver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Lead Preview Modal */}
        {selectedLead && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedLead(null)}>
            <div className="card p-6 max-w-md w-full" onClick={e => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-text">Mensagens para {selectedLead.name}</h3>
                <button onClick={() => setSelectedLead(null)}>
                  <X className="w-5 h-5 text-text-muted" />
                </button>
              </div>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-text-muted mb-1 font-medium">MSG 1:</p>
                  <div className="p-3 bg-surface rounded-lg text-sm text-text whitespace-pre-wrap">
                    {mode === 'spin'
                      ? (selectedLead.preview_msg1 || `Oi ${selectedLead.name}, tudo bem? João aqui.`)
                      : formatMessage(messageTemplate || previewData.default_template || '', selectedLead)
                    }
                  </div>
                </div>
                <div>
                  <p className="text-xs text-text-muted mb-1 font-medium">MSG 2:</p>
                  <div className="p-3 bg-surface rounded-lg text-sm text-text whitespace-pre-wrap">
                    {mode === 'spin'
                      ? (selectedLead.preview_msg2 || `Vi a ${selectedLead.company || 'sua empresa'} no Google e fiquei com uma dúvida sobre a frota de vocês.`)
                      : (msg2Template ? formatMessage(msg2Template, selectedLead) : '(Usando template padrão MSG 2)')
                    }
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Delay config */}
        <div className="card p-4 mb-6">
          <label className="block text-sm font-medium text-text mb-2">
            <Clock className="w-4 h-4 inline mr-1" />
            Delay entre leads (segundos)
          </label>
          <input
            type="number"
            min={30}
            max={120}
            value={delaySeconds}
            onChange={e => setDelaySeconds(Number(e.target.value))}
            className="input w-32"
          />
          <p className="text-xs text-text-muted mt-1">
            Tempo estimado: {Math.ceil((previewData.total_leads * delaySeconds) / 60)} minutos
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-between">
          <button
            onClick={() => setStep('upload')}
            className="btn btn-outline"
          >
            Cancelar
          </button>
          <div className="flex gap-3">
            {mode === 'custom' && (
              <button
                onClick={() => setStep('edit')}
                className="btn btn-outline flex items-center gap-2"
              >
                <Edit3 className="w-4 h-4" />
                Editar Mensagem
              </button>
            )}
            <button
              onClick={handleSend}
              className={`btn flex items-center gap-2 text-white ${
                mode === 'spin'
                  ? 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600'
                  : 'bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600'
              }`}
            >
              <Send className="w-4 h-4" />
              Enviar {previewData.total_leads} Leads
            </button>
          </div>
        </div>
      </div>
    );
  }

  // =====================================================
  // RENDER: Edit (Custom mode only)
  // =====================================================

  if (step === 'edit' && previewData) {
    const exampleLead = previewData.preview[0] || { name: 'Carlos', notes: 'crescer o negocio', company: 'Empresa X' };

    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <button onClick={() => setStep('preview')} className="text-text-muted hover:text-primary">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold text-text">Editar Mensagem</h1>
        </div>

        {/* Message 1 Editor */}
        <div className="card p-4 mb-4">
          <label className="block text-sm font-medium text-text mb-2">
            <MessageSquare className="w-4 h-4 inline mr-1" />
            Mensagem 1 (Abertura)
          </label>
          <textarea
            value={messageTemplate}
            onChange={e => setMessageTemplate(e.target.value)}
            rows={5}
            className="input w-full"
            placeholder="Fala, [NAME]! Tudo bem? ..."
          />
          <div className="flex flex-wrap gap-2 mt-2">
            {['[NAME]', '[NOTES]', '[COMPANY]'].map(p => (
              <span key={p} className="px-2 py-1 bg-surface rounded text-xs text-text-muted">{p}</span>
            ))}
          </div>
        </div>

        {/* Live Preview */}
        <div className="card p-4 mb-4 border-l-4 border-blue-500">
          <p className="text-xs text-text-muted mb-2 font-medium">Preview MSG 1:</p>
          <p className="text-sm text-text whitespace-pre-wrap">
            {formatMessage(messageTemplate, exampleLead)}
          </p>
        </div>

        {/* Delay */}
        <div className="card p-4 mb-6">
          <label className="block text-sm font-medium text-text mb-2">
            Delay entre leads: {delaySeconds}s
          </label>
          <input
            type="number"
            min={30}
            max={120}
            value={delaySeconds}
            onChange={e => setDelaySeconds(Number(e.target.value))}
            className="input w-32"
          />
          <p className="text-xs text-text-muted mt-1">
            Tempo estimado: {Math.ceil((previewData.total_leads * delaySeconds) / 60)} minutos
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-between">
          <button onClick={() => setStep('preview')} className="btn btn-outline">
            Voltar
          </button>
          <button
            onClick={handleSend}
            className="btn bg-gradient-to-r from-blue-500 to-indigo-500 text-white flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Enviar {previewData.total_leads} Leads
          </button>
        </div>
      </div>
    );
  }

  // =====================================================
  // RENDER: Sending
  // =====================================================

  if (step === 'sending') {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card p-12 text-center">
          <Loader2 className={`w-16 h-16 mx-auto animate-spin ${
            mode === 'spin' ? 'text-orange-500' : 'text-blue-500'
          }`} />
          <h2 className="text-xl font-bold text-text mt-4">Enviando Campanha...</h2>
          <p className="text-text-muted mt-2">
            {mode === 'spin' ? 'SPIN Selling' : 'Mensagem Personalizada'} - Aguarde...
          </p>
        </div>
      </div>
    );
  }

  // =====================================================
  // RENDER: Success
  // =====================================================

  if (step === 'success' && result) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card p-12 text-center">
          <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto" />
          <h2 className="text-xl font-bold text-text mt-4">Campanha Iniciada!</h2>
          <p className="text-text-muted mt-2">
            {result.total} leads serão contactados com {result.messages_per_lead || 2} mensagens cada.
          </p>
          <div className="mt-4 p-3 bg-surface rounded-lg inline-block">
            <p className="text-xs text-text-muted">Campaign ID</p>
            <p className="text-sm font-mono text-text">{result.campaign_id}</p>
          </div>
          <p className="text-text-muted text-sm mt-4">
            Tempo estimado: ~{result.estimated_time_minutes} minutos
          </p>
          <button
            onClick={reset}
            className={`btn mt-6 text-white ${
              mode === 'spin'
                ? 'bg-gradient-to-r from-orange-500 to-red-500'
                : 'bg-gradient-to-r from-blue-500 to-indigo-500'
            }`}
          >
            Nova Campanha
          </button>
        </div>
      </div>
    );
  }

  // =====================================================
  // RENDER: Error
  // =====================================================

  if (step === 'error') {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card p-12 text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto" />
          <h2 className="text-xl font-bold text-text mt-4">Erro no Envio</h2>
          <p className="text-red-400 mt-2">{error}</p>
          <div className="flex justify-center gap-3 mt-6">
            <button onClick={handleSend} className="btn btn-primary">
              Tentar Novamente
            </button>
            <button onClick={() => setStep('preview')} className="btn btn-outline">
              Voltar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

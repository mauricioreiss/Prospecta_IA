'use client';

import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { useApp } from '@/contexts/AppContext';

export default function CampaignStarter() {
  const { startCampaign, isProspecting, currentCampaign } = useApp();
  const [nicho, setNicho] = useState('');
  const [cidade, setCidade] = useState('');
  const [limite, setLimite] = useState(20);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nicho || !cidade) return;
    await startCampaign(nicho, cidade, limite);
  };

  return (
    <div className="card max-w-xl mx-auto">
      <h2 className="text-2xl font-bold text-primary text-center mb-6">
        Iniciar Nova Prospeccao
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Niche Input */}
        <div>
          <label htmlFor="nicho" className="block text-lg font-medium text-text mb-2">
            Qual nicho voce quer prospectar?
          </label>
          <input
            id="nicho"
            type="text"
            value={nicho}
            onChange={(e) => setNicho(e.target.value)}
            placeholder="Ex: Clinicas odontologicas, Academias, Restaurantes..."
            className="input"
            disabled={isProspecting}
          />
        </div>

        {/* City Input */}
        <div>
          <label htmlFor="cidade" className="block text-lg font-medium text-text mb-2">
            Onde? (Cidade/Estado)
          </label>
          <input
            id="cidade"
            type="text"
            value={cidade}
            onChange={(e) => setCidade(e.target.value)}
            placeholder="Ex: Sumare, SP"
            className="input"
            disabled={isProspecting}
          />
        </div>

        {/* Limit Input */}
        <div>
          <label htmlFor="limite" className="block text-lg font-medium text-text mb-2">
            Quantos leads buscar?
          </label>
          <input
            id="limite"
            type="number"
            min={5}
            max={100}
            value={limite}
            onChange={(e) => setLimite(Math.min(100, Math.max(5, parseInt(e.target.value) || 20)))}
            className="input"
            disabled={isProspecting}
          />
          <p className="text-sm text-text-muted mt-1">Minimo 5, maximo 100 leads</p>
        </div>

        {/* Progress */}
        {isProspecting && currentCampaign && (
          <div className="bg-surface rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-text-muted">Buscando leads...</span>
              <span className="font-medium">{currentCampaign.progresso}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-accent h-3 rounded-full transition-all duration-300"
                style={{ width: `${currentCampaign.progresso}%` }}
              />
            </div>
            {currentCampaign.leads_encontrados > 0 && (
              <p className="text-sm text-text-muted mt-2">
                {currentCampaign.leads_qualificados} leads qualificados de {currentCampaign.leads_encontrados} encontrados
              </p>
            )}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!nicho || !cidade || isProspecting}
          className="btn btn-primary w-full text-xl flex items-center justify-center gap-3"
        >
          {isProspecting ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              Buscando...
            </>
          ) : (
            <>
              <Search className="w-6 h-6" />
              BUSCAR LEADS
            </>
          )}
        </button>
      </form>
    </div>
  );
}

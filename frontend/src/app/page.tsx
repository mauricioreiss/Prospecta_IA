'use client';

import { useApp } from '@/contexts/AppContext';
import CampaignStarter from '@/components/CampaignStarter';
import LiveCallCard from '@/components/LiveCallCard';
import Link from 'next/link';
import { BarChart3, Loader2, Target, Kanban } from 'lucide-react';

export default function Home() {
  const { isLoading, error, activeCall, leadCounts } = useApp();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-accent mx-auto mb-4" />
          <p className="text-text-muted">Carregando...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="card max-w-md text-center">
          <h2 className="text-xl font-bold text-red-600 mb-2">Erro de Conexao</h2>
          <p className="text-text-muted mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="btn btn-primary"
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  const totalLeads = leadCounts?.total || 0;

  return (
    <div className="min-h-screen py-12 px-4">
      {/* Header */}
      <header className="text-center mb-12">
        <h1 className="text-3xl font-bold text-primary mb-2">
          PROSPECTA IA
        </h1>
        <p className="text-text-muted">
          Sistema inteligente de prospeccao B2B
        </p>
      </header>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto">
        {/* Show Live Call Card when call is active */}
        {activeCall?.isActive ? (
          <LiveCallCard />
        ) : (
          <>
            {/* Campaign Starter */}
            <CampaignStarter />

            {/* Action Links */}
            <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
              {totalLeads > 0 && (
                <Link
                  href="/pipeline"
                  className="btn btn-secondary inline-flex items-center gap-3 text-lg"
                >
                  <BarChart3 className="w-6 h-6" />
                  Ver Meu Pipeline ({totalLeads} leads)
                </Link>
              )}
              <Link
                href="/prospeccao-manual"
                className="btn bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white inline-flex items-center gap-3 text-lg"
              >
                <Target className="w-6 h-6" />
                Prospecção Manual
              </Link>
              <Link
                href="/kanban"
                className="btn bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white inline-flex items-center gap-3 text-lg"
              >
                <Kanban className="w-6 h-6" />
                Pipeline Kanban
              </Link>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <footer className="text-center mt-16 text-text-muted text-sm">
        <p>Prospecta IA v2.0</p>
      </footer>
    </div>
  );
}

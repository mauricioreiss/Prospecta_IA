'use client';

import ReactivationCampaign from '@/components/ReactivationCampaign';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function ReativacaoPage() {
  return (
    <main className="min-h-screen bg-background p-6">
      {/* Navigation */}
      <div className="max-w-4xl mx-auto mb-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-text-muted hover:text-primary transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Voltar para Home
        </Link>
      </div>

      <ReactivationCampaign />
    </main>
  );
}

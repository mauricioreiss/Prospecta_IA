'use client';

import { Phone, PhoneOff, FileText, Clock } from 'lucide-react';
import { useApp } from '@/contexts/AppContext';

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function LiveCallCard() {
  const { activeCall, setActiveCall } = useApp();

  if (!activeCall?.isActive) {
    return null;
  }

  const handleEndCall = () => {
    // TODO: Send end call command via WebSocket
    setActiveCall(null);
  };

  return (
    <div className="card max-w-2xl mx-auto border-2 border-green-500">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative">
          <div className="w-4 h-4 bg-green-500 rounded-full pulse-dot" />
        </div>
        <span className="text-xl font-bold text-green-600">
          LIGACAO EM ANDAMENTO
        </span>
      </div>

      {/* Lead Info */}
      <div className="bg-surface rounded-lg p-6 mb-6 text-center">
        <p className="text-text-muted mb-2">Alex esta conversando com:</p>
        <h2 className="text-2xl font-bold text-primary mb-2">
          {activeCall.leadName}
        </h2>
        <p className="text-lg text-text-muted mb-4">
          {activeCall.phoneNumber}
        </p>
        <div className="flex items-center justify-center gap-2 text-2xl text-text">
          <Clock className="w-6 h-6" />
          <span className="font-mono font-bold">
            {formatDuration(activeCall.duration)}
          </span>
        </div>
      </div>

      {/* Current Status */}
      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <p className="text-blue-800 font-medium flex items-center gap-2">
          <span className="text-xl">✓</span>
          {activeCall.status}
        </p>
      </div>

      {/* Transcript */}
      {activeCall.transcript.length > 0 && (
        <div className="mb-6">
          <h3 className="font-bold text-text mb-3">Transcricao:</h3>
          <div className="bg-gray-50 rounded-lg p-4 max-h-[200px] overflow-y-auto space-y-2">
            {activeCall.transcript.map((line, index) => (
              <p key={index} className="text-sm">
                <span className={`font-bold ${line.role === 'assistant' ? 'text-accent' : 'text-text'}`}>
                  {line.role === 'assistant' ? 'Alex:' : 'Lead:'}
                </span>{' '}
                {line.text}
              </p>
            ))}
            {/* Cursor indicator */}
            <span className="inline-block w-2 h-5 bg-accent animate-pulse" />
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4">
        <button
          onClick={handleEndCall}
          className="btn flex-1 bg-red-500 text-white hover:bg-red-600 flex items-center justify-center gap-2"
        >
          <PhoneOff className="w-5 h-5" />
          Encerrar Ligacao
        </button>
        <button className="btn btn-secondary flex items-center justify-center gap-2">
          <FileText className="w-5 h-5" />
          Adicionar Nota
        </button>
      </div>
    </div>
  );
}

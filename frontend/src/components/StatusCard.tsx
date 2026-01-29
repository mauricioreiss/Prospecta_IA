'use client';

import { Inbox, Phone, Star, Calendar } from 'lucide-react';

type UIStatus = 'novos' | 'contatado' | 'interesse' | 'agendado';

interface StatusCardProps {
  status: UIStatus;
  count: number;
  isSelected: boolean;
  onClick: () => void;
}

const STATUS_CONFIG: Record<UIStatus, {
  label: string;
  icon: typeof Inbox;
  bgColor: string;
  textColor: string;
  borderColor: string;
}> = {
  novos: {
    label: 'NOVOS',
    icon: Inbox,
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-800',
    borderColor: 'border-blue-400',
  },
  contatado: {
    label: 'CONTATADO',
    icon: Phone,
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-800',
    borderColor: 'border-yellow-400',
  },
  interesse: {
    label: 'INTERESSE',
    icon: Star,
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
    borderColor: 'border-green-400',
  },
  agendado: {
    label: 'AGENDADO',
    icon: Calendar,
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-800',
    borderColor: 'border-purple-400',
  },
};

export default function StatusCard({ status, count, isSelected, onClick }: StatusCardProps) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <button
      onClick={onClick}
      className={`
        flex-1 min-w-[160px] p-5 rounded-xl border-3 transition-all cursor-pointer
        ${config.bgColor} ${config.textColor} ${config.borderColor}
        ${isSelected ? 'ring-4 ring-offset-2 ring-accent shadow-xl scale-105' : 'hover:shadow-lg hover:scale-102'}
        focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-accent
      `}
      aria-label={`${config.label}: ${count} leads`}
    >
      <div className="flex flex-col items-center gap-3">
        <Icon className="w-10 h-10" strokeWidth={2.5} />
        <span className="text-base font-bold tracking-wide">{config.label}</span>
        <span className="text-4xl font-bold">{count}</span>
      </div>
    </button>
  );
}

// Container for horizontal row
export function StatusCardsRow({
  counts,
  selectedStatus,
  onSelect,
}: {
  counts: Record<UIStatus, number>;
  selectedStatus: UIStatus;
  onSelect: (status: UIStatus) => void;
}) {
  const statuses: UIStatus[] = ['novos', 'contatado', 'interesse', 'agendado'];

  return (
    <div className="flex flex-wrap gap-4 justify-center">
      {statuses.map((status) => (
        <StatusCard
          key={status}
          status={status}
          count={counts[status] || 0}
          isSelected={selectedStatus === status}
          onClick={() => onSelect(status)}
        />
      ))}
    </div>
  );
}

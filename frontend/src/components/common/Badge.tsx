import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'nobre' | 'urgent' | 'success' | 'warning' | 'info' | 'neutral' | 'collect';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
  icon,
}) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs font-semibold',
    lg: 'px-3 py-1.5 text-sm font-semibold',
  }[size];

  const variantClasses = {
    nobre: 'bg-nobre-500 text-slate-900 border border-nobre-600 shadow-sm font-bold',
    urgent: 'bg-red-500 text-white border border-red-600 font-bold animate-pulse',
    success: 'bg-emerald-50 text-emerald-700 border border-emerald-300 font-semibold',
    warning: 'bg-amber-50 text-amber-800 border border-amber-300 font-semibold',
    info: 'bg-sky-50 text-sky-700 border border-sky-300 font-semibold',
    neutral: 'bg-slate-100 text-slate-700 border border-slate-300',
    collect: 'bg-red-50 text-red-700 border border-red-300 font-bold',
  }[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${sizeClasses} ${variantClasses} ${className}`}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

export const SituacaoBadge: React.FC<{ situacao: string }> = ({ situacao }) => {
  const sitUpper = situacao.toUpperCase();

  switch (sitUpper) {
    case 'URGENTE':
      return <Badge variant="urgent">URGENTE</Badge>;
    case 'NORMAL':
      return <Badge variant="success">NORMAL</Badge>;
    case 'CARRO HORARIO':
      return <Badge variant="info">CARRO HORÁRIO</Badge>;
    case 'PROGRAMADO':
      return <Badge variant="warning">PROGRAMADO</Badge>;
    case 'TOPIQUE':
      return <Badge variant="nobre">TOPIQUE</Badge>;
    case 'RETIRADA':
      return <Badge variant="neutral">RETIRADA BALCÃO</Badge>;
    case 'CANCELADO':
      return <Badge variant="collect">CANCELADO</Badge>;
    default:
      return <Badge variant="neutral">{situacao}</Badge>;
  }
};

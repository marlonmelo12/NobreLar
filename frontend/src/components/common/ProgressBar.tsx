import React from 'react';

interface ProgressBarProps {
  value: number; // Porcentagem (0 a 100)
  label: string;
  detail: string;
  isLimiting?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  detail,
  isLimiting = false,
}) => {
  const clampedValue = Math.min(Math.max(value, 0), 100);

  // Cor da barra de progresso baseada na ocupação e recurso limitante
  let barColor = 'bg-nobre-500';
  if (clampedValue > 95) {
    barColor = 'bg-red-500';
  } else if (clampedValue > 80) {
    barColor = 'bg-amber-500';
  } else if (isLimiting) {
    barColor = 'bg-nobre-500';
  } else {
    barColor = 'bg-slate-400';
  }

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-slate-700 flex items-center gap-1.5">
          {label}
          {isLimiting && (
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-nobre-100 text-nobre-900 border border-nobre-400 font-bold uppercase tracking-wider">
              Limitante
            </span>
          )}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-slate-500 font-mono text-[11px]">{detail}</span>
          <span className="font-bold text-slate-900 font-mono">{value.toFixed(1)}%</span>
        </div>
      </div>

      <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200">
        <div
          className={`h-full transition-all duration-500 ease-out rounded-full ${barColor}`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
};

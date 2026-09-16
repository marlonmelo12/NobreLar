import React, { useEffect, useState } from 'react';
import { DecoupledDispatchResponse } from '../../types/dispatch';
import { Loader2, Trash2 } from 'lucide-react';
import { api } from '../../services/api';

interface DashboardViewProps {
  dispatchResult: DecoupledDispatchResponse | null;
  totalOrdersCount: number;
  lastExecutionTime: string | null;
  isProcessing: boolean;
  onExecute: () => void;
  onClear?: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  dispatchResult,
  totalOrdersCount,
  lastExecutionTime,
  isProcessing,
  onExecute,
  onClear,
}) => {
  const [axesCount, setAxesCount] = useState(6);
  const [vehiclesCount, setVehiclesCount] = useState(4);

  useEffect(() => {
    api.fetchAxisProfiles().then((data) => {
      if (data && data.length > 0) setAxesCount(data.length);
    }).catch(() => {});

    api.fetchVehicles().then((data) => {
      if (data && data.length > 0) setVehiclesCount(data.length);
    }).catch(() => {});
  }, []);

  const resumo = dispatchResult?.resumo;
  const pedidosTotais = resumo ? resumo.total_records_read : totalOrdersCount;
  const pedidosValidos = resumo ? resumo.total_valid_deliveries : 0;
  const pedidosDescartados = resumo ? resumo.total_discarded_cleaning : 0;

  return (
    <div className="max-w-5xl mx-auto py-8 px-6 space-y-8 animate-fadeIn">
      {/* Título Centralizado conforme Figma */}
      <div className="text-center">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          Dashboard
        </h1>
      </div>

      {/* Card Principal: Realizar controle dos limites */}
      <div className="border border-amber-400 bg-white rounded-2xl shadow-sm overflow-hidden transition-all duration-150">
        <div className="p-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-1 text-center md:text-left">
            <h2 className="text-xl font-bold text-slate-800">
              Realizar controle dos limites
            </h2>
            <p className="text-sm text-slate-500">
              Dispara a otimização CP-SAT multi-viagens e roteirização TSP sobre os pedidos faturados.
            </p>
          </div>

          <button
            onClick={onExecute}
            disabled={isProcessing}
            className="w-full md:w-auto bg-amber-400 hover:bg-amber-500 active:bg-amber-600 disabled:opacity-50 text-slate-950 font-bold px-10 py-3 rounded-xl shadow-sm transition-all duration-150 flex items-center justify-center gap-2 text-base cursor-pointer"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Processando...</span>
              </>
            ) : (
              <span>Executar</span>
            )}
          </button>
        </div>

        {/* Faixa inferior amarela suave */}
        <div className="bg-[#FEF3C7] border-t border-amber-200/80 px-8 py-3 flex items-center justify-between text-xs text-slate-700 font-semibold">
          <div className="flex items-center gap-3">
            <span>Última execução:</span>
            <span className="font-mono text-slate-900">
              {lastExecutionTime || 'Nenhuma execução realizada'}
            </span>
          </div>

          {dispatchResult && onClear && (
            <button
              onClick={onClear}
              className="text-xs text-rose-700 hover:text-rose-900 font-bold flex items-center gap-1 bg-white/80 hover:bg-white px-2.5 py-1 rounded-lg border border-amber-300 transition cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Limpar Resultados</span>
            </button>
          )}
        </div>
      </div>

      {/* Linha de 3 Cards de Métricas de Pedidos */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="border border-amber-400 bg-white rounded-2xl p-6 text-center shadow-sm hover:shadow transition-shadow">
          <h3 className="text-base font-semibold text-slate-700 mb-2">
            Pedidos Totais
          </h3>
          <div className="text-4xl font-extrabold text-slate-900 font-mono">
            {pedidosTotais}
          </div>
          <span className="text-xs text-slate-400 mt-2 block">
            Registros brutos faturados
          </span>
        </div>

        <div className="border border-amber-400 bg-white rounded-2xl p-6 text-center shadow-sm hover:shadow transition-shadow">
          <h3 className="text-base font-semibold text-slate-700 mb-2">
            Pedidos Válidos
          </h3>
          <div className="text-4xl font-extrabold text-slate-900 font-mono">
            {pedidosValidos}
          </div>
          <span className="text-xs text-emerald-600 font-semibold mt-2 block">
            Elegíveis para expedição rodoviária
          </span>
        </div>

        <div className="border border-amber-400 bg-white rounded-2xl p-6 text-center shadow-sm hover:shadow transition-shadow">
          <h3 className="text-base font-semibold text-slate-700 mb-2">
            Pedidos Descartados
          </h3>
          <div className="text-4xl font-extrabold text-slate-900 font-mono">
            {pedidosDescartados}
          </div>
          <span className="text-xs text-rose-600 font-semibold mt-2 block">
            Retiradas balcão ou cancelados
          </span>
        </div>
      </div>

      {/* Linha de 2 Cards de Métricas Operacionais */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="border border-amber-400 bg-white rounded-2xl p-8 text-center shadow-sm hover:shadow transition-shadow">
          <h3 className="text-base font-semibold text-slate-700 mb-2">
            Eixos
          </h3>
          <div className="text-5xl font-black text-slate-900 font-mono">
            {axesCount}
          </div>
          <span className="text-xs text-slate-400 mt-2 block">
            Macrorregião de Crateús (Eixos 0 a 5)
          </span>
        </div>

        <div className="border border-amber-400 bg-white rounded-2xl p-8 text-center shadow-sm hover:shadow transition-shadow">
          <h3 className="text-base font-semibold text-slate-700 mb-2">
            Veículos
          </h3>
          <div className="text-5xl font-black text-slate-900 font-mono">
            {vehiclesCount}
          </div>
          <span className="text-xs text-slate-400 mt-2 block">
            2 Accelo 815 • 1 Kia Bongo • 1 Hyundai HR
          </span>
        </div>
      </div>
    </div>
  );
};

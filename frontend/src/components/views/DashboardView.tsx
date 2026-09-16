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
  onSimulateApiLoad: () => void;
  onClear?: () => void;
  onNavigateToLoads?: () => void;
  onNavigateToRoutes?: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  dispatchResult,
  totalOrdersCount,
  lastExecutionTime,
  isProcessing,
  onExecute,
  onSimulateApiLoad,
  onClear,
  onNavigateToLoads,
  onNavigateToRoutes,
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
  const hasTrips = (dispatchResult?.cargas_caminhao?.length || 0) > 0;
  const hasPendingOrders = pedidosValidos > 0 && !hasTrips;

  return (
    <div className="max-w-5xl mx-auto py-8 px-6 space-y-8 animate-fadeIn">
      {/* Título Centralizado conforme Figma */}
      <div className="text-center space-y-1">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          Dashboard
        </h1>
        <p className="text-xs text-slate-500">
          Painel operacional de expedição, limites de capacidade e controle de viagens da Nobre Lar.
        </p>
      </div>

      {/* Banner de Estado dos Pedidos */}
      {hasPendingOrders && (
        <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-400 text-slate-950 font-bold flex items-center justify-center shrink-0">
              ⚡
            </div>
            <div>
              <h4 className="text-sm font-extrabold text-amber-950">
                {pedidosValidos} pedidos carregados via JSON da API aguardando alocação
              </h4>
              <p className="text-xs text-amber-800">
                Os pedidos estão disponíveis no sistema em estado desalocado. Clique no botão <strong>Executar</strong> abaixo para realizar o controle de limites e roteirização.
              </p>
            </div>
          </div>
          <button
            onClick={onExecute}
            disabled={isProcessing}
            className="shrink-0 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-xs transition"
          >
            Executar Agora
          </button>
        </div>
      )}

      {/* Banner de Viagens Concluídas */}
      {hasTrips && (
        <div className="bg-emerald-50 border border-emerald-300 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500 text-white font-bold flex items-center justify-center shrink-0">
              ✓
            </div>
            <div>
              <h4 className="text-sm font-extrabold text-emerald-950">
                {dispatchResult?.cargas_caminhao.length} viagens alocadas e roteirizadas com sucesso!
              </h4>
              <p className="text-xs text-emerald-800">
                Total de {resumo?.total_allocated_orders} pedidos expedidos com definição física de estivagem e ordem de entregas TSP.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {onNavigateToLoads && (
              <button
                onClick={onNavigateToLoads}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl transition"
              >
                Ver Cargas
              </button>
            )}
            {onNavigateToRoutes && (
              <button
                onClick={onNavigateToRoutes}
                className="bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs px-3.5 py-2 rounded-xl transition"
              >
                Ver Ordem de Entregas
              </button>
            )}
          </div>
        </div>
      )}

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

          <div className="flex items-center gap-3 flex-wrap justify-center md:justify-end w-full md:w-auto">
            {/* Botão Simular Carga da API */}
            <button
              onClick={onSimulateApiLoad}
              disabled={isProcessing}
              title="Carrega 5 pedidos simulados da API em formato JSON (ficam inicialmente desalocados)"
              className="bg-slate-100 hover:bg-slate-200 active:bg-slate-300 disabled:opacity-50 text-slate-800 font-bold px-5 py-3 rounded-xl border border-slate-300 transition-all duration-150 flex items-center justify-center gap-2 text-sm cursor-pointer shrink-0"
            >
              <span>Simular Carga da API</span>
            </button>

            {/* Botão Executar Controle de Limites */}
            <button
              onClick={onExecute}
              disabled={isProcessing}
              className="bg-amber-400 hover:bg-amber-500 active:bg-amber-600 disabled:opacity-50 text-slate-950 font-bold px-10 py-3 rounded-xl shadow-sm transition-all duration-150 flex items-center justify-center gap-2 text-base cursor-pointer shrink-0"
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

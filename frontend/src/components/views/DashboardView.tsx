import React, { useEffect, useState } from 'react';
import { DecoupledDispatchResponse } from '../../types/dispatch';
import {
  Package,
  CheckCircle,
  XCircle,
  Compass,
  Truck,
  TrendingUp,
  Layers,
  ArrowRight,
  Boxes,
  Weight,
} from 'lucide-react';
import { api } from '../../services/api';

interface DashboardViewProps {
  dispatchResult: DecoupledDispatchResponse | null;
  totalOrdersCount: number;
  lastExecutionTime?: string | null;
  isProcessing?: boolean;
  onExecute?: () => void;
  onSimulateApiLoad?: () => void;
  onClear?: () => void;
  onNavigateToLoads?: () => void;
  onNavigateToRoutes?: () => void;
  onNavigateToPrepare?: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  dispatchResult,
  totalOrdersCount,
  onNavigateToLoads,
  onNavigateToRoutes,
  onNavigateToPrepare,
}) => {
  const [axesCount, setAxesCount] = useState(6);
  const [vehiclesCount, setVehiclesCount] = useState(4);

  useEffect(() => {
    api
      .fetchAxisProfiles()
      .then((data) => {
        if (data && data.length > 0) setAxesCount(data.length);
      })
      .catch(() => {});

    api
      .fetchVehicles()
      .then((data) => {
        if (data && data.length > 0) setVehiclesCount(data.length);
      })
      .catch(() => {});
  }, []);

  const resumo = dispatchResult?.resumo;
  const pedidosTotais = resumo ? resumo.total_records_read : totalOrdersCount;
  const pedidosValidos = resumo
    ? resumo.total_allocated_orders > 0
      ? resumo.total_allocated_orders
      : resumo.total_valid_deliveries
    : 0;
  const pedidosDescartados = resumo ? resumo.total_discarded_cleaning : 0;
  const viagensCount = dispatchResult?.cargas_caminhao?.length || 0;
  const faturamentoTotal = resumo?.total_invoiced_value || 0;
  const pesoTotal = resumo?.total_allocated_weight_kg || 0;
  const volumeTotal = resumo?.total_allocated_volume_m3 || 0;

  const fmtMoney = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  return (
    <div className="max-w-6xl mx-auto py-8 px-6 space-y-8 animate-fadeIn">
      {/* Cabeçalho Executivo */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
          Painel de Indicadores (KPIs)
        </h1>
        <p className="text-xs md:text-sm text-slate-500 max-w-xl mx-auto">
          Visão consolidada do faturamento diário, capacidade operacional da frota e eficiência das viagens.
        </p>
      </div>

      {/* SEÇÃO 1: KPIs Principais de Pedidos */}
      <div>
        <div className="flex items-center gap-2 mb-3 text-xs font-bold uppercase tracking-wider text-slate-400">
          <Package className="w-3.5 h-3.5" />
          <span>Fluxo de Pedidos do Faturamento</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {/* KPI 1: Pedidos Totais */}
          <div className="border border-slate-200 bg-white rounded-2xl p-6 shadow-xs hover:border-slate-300 transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Pedidos Totais
              </span>
              <span className="p-2 rounded-xl bg-slate-100 text-slate-700">
                <Package className="w-4 h-4" />
              </span>
            </div>
            <div className="text-4xl font-extrabold text-slate-900 font-mono mt-3">
              {pedidosTotais}
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block">
              Registros brutos faturados no lote
            </span>
          </div>

          {/* KPI 2: Pedidos Elegíveis / Alocados */}
          <div className="border border-emerald-200 bg-emerald-50/40 rounded-2xl p-6 shadow-xs hover:border-emerald-300 transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">
                Pedidos Elegíveis / Alocados
              </span>
              <span className="p-2 rounded-xl bg-emerald-100 text-emerald-700">
                <CheckCircle className="w-4 h-4" />
              </span>
            </div>
            <div className="text-4xl font-extrabold text-emerald-900 font-mono mt-3">
              {pedidosValidos}
            </div>
            <span className="text-[11px] text-emerald-700 font-medium mt-2 block">
              Elegíveis para expedição rodoviária
            </span>
          </div>

          {/* KPI 3: Pedidos Descartados */}
          <div className="border border-slate-200 bg-white rounded-2xl p-6 shadow-xs hover:border-slate-300 transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Pedidos Descartados
              </span>
              <span className="p-2 rounded-xl bg-slate-100 text-slate-500">
                <XCircle className="w-4 h-4" />
              </span>
            </div>
            <div className="text-4xl font-extrabold text-slate-600 font-mono mt-3">
              {pedidosDescartados}
            </div>
            <span className="text-[11px] text-slate-400 mt-2 block">
              Retirada no balcão ou cancelados
            </span>
          </div>
        </div>
      </div>

      {/* SEÇÃO 2: KPIs de Recursos Operacionais */}
      <div>
        <div className="flex items-center gap-2 mb-3 text-xs font-bold uppercase tracking-wider text-slate-400">
          <Truck className="w-3.5 h-3.5" />
          <span>Infraestrutura e Frota Disponível</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* KPI 4: Eixos Rodoviários */}
          <div className="border border-slate-200 bg-white rounded-2xl p-6 shadow-xs hover:border-slate-300 transition">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                  Eixos Rodoviários
                </span>
                <span className="text-xs text-slate-400">Macrorregião CD Crateús</span>
              </div>
              <span className="p-2.5 rounded-xl bg-amber-50 text-amber-700 border border-amber-200">
                <Compass className="w-5 h-5" />
              </span>
            </div>
            <div className="text-4xl font-extrabold text-slate-900 font-mono mt-3">
              {axesCount} Eixos
            </div>
            <p className="text-[11px] text-slate-500 mt-2">
              Urbano, Piauí, Sertão Central, Sul, Norte e Sertões dos Inhamuns
            </p>
          </div>

          {/* KPI 5: Frota de Veículos */}
          <div className="border border-slate-200 bg-white rounded-2xl p-6 shadow-xs hover:border-slate-300 transition">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                  Veículos da Frota
                </span>
                <span className="text-xs text-slate-400">Capacidade Operacional</span>
              </div>
              <span className="p-2.5 rounded-xl bg-slate-100 text-slate-800 border border-slate-200">
                <Truck className="w-5 h-5" />
              </span>
            </div>
            <div className="text-4xl font-extrabold text-slate-900 font-mono mt-3">
              {vehiclesCount} Caminhões
            </div>
            <p className="text-[11px] text-slate-500 mt-2">
              2 Mercedes-Benz Accelo 815 (4.800 kg) • 1 Kia Bongo • 1 Hyundai HR
            </p>
          </div>
        </div>
      </div>

      {/* SEÇÃO 3: KPIs de Resultados da Expedição (Exibidos quando há viagens) */}
      {viagensCount > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Resultados Consolidados da Expedição</span>
            </div>
            <div className="flex items-center gap-2">
              {onNavigateToLoads && (
                <button
                  onClick={onNavigateToLoads}
                  className="text-xs font-bold text-slate-700 hover:text-slate-950 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition flex items-center gap-1 cursor-pointer"
                >
                  <Layers className="w-3.5 h-3.5 text-amber-500" />
                  <span>Ver Cargas</span>
                </button>
              )}
              {onNavigateToRoutes && (
                <button
                  onClick={onNavigateToRoutes}
                  className="text-xs font-bold text-slate-700 hover:text-slate-950 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition flex items-center gap-1 cursor-pointer"
                >
                  <Compass className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Ver Roteiros</span>
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
            <div className="border border-slate-200 bg-white rounded-2xl p-5 shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Viagens Geradas
              </span>
              <div className="text-3xl font-extrabold text-slate-900 font-mono mt-1">
                {viagensCount}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Alocação multi-viagens
              </span>
            </div>

            <div className="border border-slate-200 bg-white rounded-2xl p-5 shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Faturamento Expedido
              </span>
              <div className="text-2xl lg:text-3xl font-extrabold text-emerald-700 font-mono mt-1">
                {fmtMoney(faturamentoTotal)}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Valor das notas fiscais
              </span>
            </div>

            <div className="border border-slate-200 bg-white rounded-2xl p-5 shadow-xs">
              <div className="flex items-center gap-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <Weight className="w-3 h-3" />
                <span>Peso Total Carga</span>
              </div>
              <div className="text-2xl lg:text-3xl font-extrabold text-slate-900 font-mono mt-1">
                {pesoTotal.toFixed(1)} <span className="text-base font-normal text-slate-400">kg</span>
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Massa expedida nos caminhões
              </span>
            </div>

            <div className="border border-slate-200 bg-white rounded-2xl p-5 shadow-xs">
              <div className="flex items-center gap-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <Boxes className="w-3 h-3" />
                <span>Volume Total</span>
              </div>
              <div className="text-2xl lg:text-3xl font-extrabold text-slate-900 font-mono mt-1">
                {volumeTotal.toFixed(2)} <span className="text-base font-normal text-slate-400">m³</span>
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Cubagem física das cargas
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Card Informativo para Importação (quando ainda não há resultado) */}
      {viagensCount === 0 && onNavigateToPrepare && (
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="space-y-1 text-center sm:text-left">
            <h4 className="text-sm font-bold text-slate-900">
              Pronto para planejar uma nova expedição?
            </h4>
            <p className="text-xs text-slate-500">
              Acesse a aba <strong>Preparar</strong> para importar o arquivo CSV de faturamento diário e calcular as viagens otimizadas.
            </p>
          </div>
          <button
            onClick={onNavigateToPrepare}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold text-xs rounded-xl shadow-xs transition cursor-pointer shrink-0"
          >
            <span>Ir para Preparar Cargas</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};

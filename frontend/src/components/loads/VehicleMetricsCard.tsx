import React from 'react';
import { CargaCaminhaoViagem } from '../../types/dispatch';
import { ProgressBar } from '../common/ProgressBar';
import { FileDown, Truck, Weight, Box, DollarSign, Layers } from 'lucide-react';
import { api } from '../../services/api';

interface VehicleMetricsCardProps {
  trip: CargaCaminhaoViagem;
}

export const VehicleMetricsCard: React.FC<VehicleMetricsCardProps> = ({ trip }) => {
  const pdfUrl = api.getLoadingSheetPdfUrl(trip.viagem_id);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
      
      {/* Header do Card: Veículo e Botão PDF */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-nobre-500 text-slate-950 flex items-center justify-center font-bold shadow-sm shrink-0">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-lg font-extrabold text-slate-900">{trip.veiculo.nome}</h2>
              <span className="px-2.5 py-0.5 rounded-md bg-slate-900 text-white font-mono text-xs font-bold tracking-wider">
                {trip.veiculo.placa}
              </span>
              <span className="px-2 py-0.5 rounded-md bg-nobre-100 text-nobre-900 border border-nobre-300 text-xs font-semibold">
                {trip.veiculo.tipo_carroceria}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Viagem #{trip.viagem_numero} — Eixo {trip.eixo_nome} ({trip.total_pedidos} pedidos estivados)
            </p>
          </div>
        </div>

        {/* Botão Baixar PDF do Romaneio */}
        <a
          href={pdfUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-xs font-bold text-slate-900 bg-nobre-500 hover:bg-nobre-400 active:bg-nobre-600 rounded-xl shadow-xs border border-nobre-600 transition"
        >
          <FileDown className="w-4 h-4" />
          <span>Mapa de Carregamento (PDF)</span>
        </a>
      </div>

      {/* Indicadores Numéricos */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        
        <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
          <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
            <Weight className="w-4 h-4 text-slate-600" />
            <span>Peso Alocado</span>
          </div>
          <div className="text-base font-extrabold text-slate-900 font-mono">
            {trip.peso_total_kg.toLocaleString('pt-BR', { minimumFractionDigits: 1 })} kg
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            de {trip.veiculo.capacidade_kg.toLocaleString('pt-BR')} kg máx
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
          <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
            <Box className="w-4 h-4 text-slate-600" />
            <span>Volume Alocado</span>
          </div>
          <div className="text-base font-extrabold text-slate-900 font-mono">
            {trip.volume_total_m3.toFixed(3)} m³
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            de {trip.veiculo.volume_util_m3.toFixed(1)} m³ útil
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
          <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
            <Layers className="w-4 h-4 text-slate-600" />
            <span>Recurso Limitante</span>
          </div>
          <div className="text-base font-extrabold text-nobre-700 font-mono">
            {trip.recurso_limitante}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Gargalo físico de capacidade
          </div>
        </div>

        <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
          <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
            <DollarSign className="w-4 h-4 text-slate-600" />
            <span>Faturamento Carga</span>
          </div>
          <div className="text-base font-extrabold text-emerald-700 font-mono">
            R$ {trip.faturamento_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            {trip.total_pedidos} notas fiscais
          </div>
        </div>

      </div>

      {/* Barras de Ocupação */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        <ProgressBar
          value={trip.ocupacao_peso_pct}
          label="Ocupação em Peso (Capacidade de Carga)"
          detail={`${trip.peso_total_kg.toFixed(0)} kg / ${trip.veiculo.capacidade_kg} kg`}
          isLimiting={trip.recurso_limitante === 'PESO'}
        />

        <ProgressBar
          value={trip.ocupacao_volume_pct}
          label="Ocupação em Volume (Cubagem Útil)"
          detail={`${trip.volume_total_m3.toFixed(2)} m³ / ${trip.veiculo.volume_util_m3} m³`}
          isLimiting={trip.recurso_limitante === 'VOLUME'}
        />
      </div>

      {/* Alerta Operacional Oficial */}
      {trip.alerta_carroceria && (
        <div className="p-3.5 rounded-xl bg-slate-900 text-white text-xs border border-slate-800 flex items-center justify-between">
          <span className="font-semibold text-slate-200">
            {trip.alerta_carroceria}
          </span>
          <span className="text-[10px] px-2 py-0.5 bg-nobre-500 text-slate-950 font-bold rounded">
            Protocolo de Galpão
          </span>
        </div>
      )}

    </div>
  );
};

import React, { useState } from 'react';
import { RoteiroEntregaViagem } from '../../types/dispatch';
import { DeliveryStopCard } from './DeliveryStopCard';
import { MapPin, Navigation, DollarSign, CreditCard, FileDown, Route } from 'lucide-react';
import { api } from '../../services/api';

interface DeliveryRouteViewProps {
  roteiros: RoteiroEntregaViagem[];
}

export const DeliveryRouteView: React.FC<DeliveryRouteViewProps> = ({ roteiros }) => {
  const [selectedRouteIndex, setSelectedRouteIndex] = useState(0);

  if (!roteiros || roteiros.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mb-4">
          <Route className="w-7 h-7" />
        </div>
        <h3 className="text-base font-bold text-slate-800">Nenhum Roteiro Disponível</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
          Execute o processamento de pedidos no cabeçalho para gerar as sequências de entrega via algoritmo TSP.
        </p>
      </div>
    );
  }

  const currentRoute = roteiros[selectedRouteIndex] || roteiros[0];
  const pdfUrl = api.getDeliveryRoutePdfUrl(currentRoute.viagem_id);

  return (
    <div className="space-y-6">
      
      {/* Seletor de Roteiros */}
      <div className="bg-white rounded-2xl border border-slate-200 p-3 shadow-xs">
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {roteiros.map((r, idx) => {
            const isSelected = idx === selectedRouteIndex;
            return (
              <button
                key={r.viagem_id}
                type="button"
                onClick={() => setSelectedRouteIndex(idx)}
                className={`px-4 py-2.5 rounded-xl text-left transition shrink-0 border ${
                  isSelected
                    ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black uppercase">
                    {r.titulo}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                      isSelected ? 'bg-nobre-500 text-slate-950' : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {r.total_paradas} paradas
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {r.eixo_nome} ({r.distancia_estimada_km.toFixed(0)} km)
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Card de Métricas da Rota */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-slate-900 text-nobre-400 flex items-center justify-center font-bold shadow-sm shrink-0 border border-slate-800">
              <Navigation className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-lg font-extrabold text-slate-900">
                  Roteiro de Entregas TSP — {currentRoute.eixo_nome}
                </h2>
                <span className="px-2.5 py-0.5 rounded-md bg-nobre-100 text-nobre-900 border border-nobre-300 text-xs font-bold font-mono">
                  {currentRoute.viagem_id}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Veículo designado: <strong className="text-slate-800">{currentRoute.veiculo.nome}</strong> (Placa: {currentRoute.veiculo.placa})
              </p>
            </div>
          </div>

          {/* Botão Baixar Roteiro em PDF */}
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-xs font-bold text-slate-900 bg-nobre-500 hover:bg-nobre-400 active:bg-nobre-600 rounded-xl shadow-xs border border-nobre-600 transition"
          >
            <FileDown className="w-4 h-4" />
            <span>Roteiro de Entregas (PDF)</span>
          </a>
        </div>

        {/* Métricas da Rota */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          
          <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
              <Navigation className="w-4 h-4 text-slate-600" />
              <span>Extensão Estimada</span>
            </div>
            <div className="text-base font-extrabold text-slate-900 font-mono">
              {currentRoute.distancia_estimada_km.toFixed(1)} km
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Ida e volta com tortuosidade
            </div>
          </div>

          <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
              <MapPin className="w-4 h-4 text-slate-600" />
              <span>Total de Paradas</span>
            </div>
            <div className="text-base font-extrabold text-slate-900 font-mono">
              {currentRoute.total_paradas} clientes
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Sequência ótima TSP
            </div>
          </div>

          <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
              <DollarSign className="w-4 h-4 text-slate-600" />
              <span>Faturamento Total</span>
            </div>
            <div className="text-base font-extrabold text-slate-900 font-mono">
              R$ {currentRoute.faturamento_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Valor das notas expedidas
            </div>
          </div>

          <div className={`rounded-xl p-3.5 border ${
            currentRoute.total_a_receber_rota > 0
              ? 'bg-red-50 border-red-200 text-red-900'
              : 'bg-emerald-50 border-emerald-200 text-emerald-900'
          }`}>
            <div className="flex items-center gap-2 text-xs mb-1 font-semibold">
              <CreditCard className="w-4 h-4" />
              <span>Total a Receber</span>
            </div>
            <div className="text-base font-extrabold font-mono">
              R$ {currentRoute.total_a_receber_rota.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
            </div>
            <div className="text-[11px] mt-0.5 opacity-80">
              {currentRoute.total_a_receber_rota > 0
                ? 'Cobrança mandante na rota'
                : '100% dos pedidos quitados'}
            </div>
          </div>

        </div>
      </div>

      {/* Linha do Tempo de Paradas */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
            <span>Sequência Geográfica de Paradas</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-300">
              Partida: CD Crateús
            </span>
          </h3>
          <span className="text-xs text-slate-500">
            Menor percurso com retorno ao Centro de Distribuição
          </span>
        </div>

        <div className="pt-2">
          {currentRoute.paradas.map((parada, idx) => (
            <DeliveryStopCard
              key={parada.pedido}
              parada={parada}
              isLastStop={idx === currentRoute.paradas.length - 1}
            />
          ))}
        </div>
      </div>

    </div>
  );
};

import React, { useState } from 'react';
import { RoteiroEntregaViagem } from '../../types/dispatch';
import { DeliveryStopCard } from './DeliveryStopCard';
import { MapPin, Navigation, DollarSign, FileDown, Route, CheckCircle2, ExternalLink } from 'lucide-react';
import { api } from '../../services/api';

interface DeliveryRouteViewProps {
  roteiros: RoteiroEntregaViagem[];
}

export const DeliveryRouteView: React.FC<DeliveryRouteViewProps> = ({ roteiros }) => {
  const [selectedRouteIndex, setSelectedRouteIndex] = useState(0);

  if (!roteiros || roteiros.length === 0) {
    return (
      <div className="max-w-6xl mx-auto py-8 px-6 space-y-6 animate-fadeIn">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Route className="w-8 h-8 text-amber-500" />
            <span>Ordem de Entregas</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Sequência otimizada de paradas calculada pelo algoritmo TSP, endereços e alertas de cobrança por viagem.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mb-4">
            <Route className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-slate-800">Nenhum Roteiro Disponível</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            Envie um lote de pedidos pelo Swagger ou pela aba <strong>Preparar</strong> para calcular as rotas de entrega e a ordem das paradas.
          </p>
        </div>
      </div>
    );
  }

  const currentRoute = roteiros[selectedRouteIndex] || roteiros[0];
  const pdfUrl = api.getDeliveryRoutePdfUrl(currentRoute.viagem_id);

  return (
    <div className="max-w-6xl mx-auto py-8 px-6 space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <Route className="w-8 h-8 text-amber-500" />
          <span>Ordem de Entregas</span>
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Sequência otimizada de paradas calculada pelo algoritmo TSP, endereços de entrega e valores a receber por viagem.
        </p>
      </div>
      
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
                    {r.titulo || `Viagem ${idx + 1}`}
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

          <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Otimização TSP</span>
            </div>
            <div className="text-base font-extrabold text-slate-900 font-mono">
              Sequência Ótima
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Menor trajeto rodoviário
            </div>
          </div>

        </div>
      </div>

      {/* Itinerário Resumido dos Pontos */}
      <div className="bg-amber-50 rounded-2xl border border-amber-200/80 p-4 shadow-xs space-y-2">
        <div className="flex items-center justify-between flex-wrap gap-2 text-xs font-bold text-amber-900">
          <div className="flex items-center gap-2">
            <Route className="w-4 h-4 text-amber-600" />
            <span>Itinerário Completo dos Pontos Definidos na Rota:</span>
          </div>
          <span className="text-[11px] font-mono bg-amber-200/60 text-amber-900 px-2.5 py-0.5 rounded-full">
            {currentRoute.paradas.length + 2} pontos geográficos mapeados
          </span>
        </div>
        <div className="text-xs font-mono text-slate-800 bg-white/90 p-3 rounded-xl border border-amber-200 overflow-x-auto">
          {currentRoute.itinerario_resumido || (
            `CD Crateús (Origem) ➔ ${currentRoute.paradas.map(p => `Ponto ${p.ponto_numero || p.parada}: ${p.cliente || 'Cliente'} (${p.cidade})`).join(' ➔ ')} ➔ Retorno CD Crateús`
          )}
        </div>
      </div>

      {/* Linha do Tempo de Paradas */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
            <span>Sequência Geográfica de Pontos da Rota</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 font-mono">
              Origem & Retorno: CD Crateús
            </span>
          </h3>
          <span className="text-xs text-slate-500">
            Ordem ótima calculada com retorno ao depósito
          </span>
        </div>

        <div className="pt-2">
          {/* Ponto 0: Origem / Partida */}
          <div className="relative pl-8 pb-8">
            <div className="absolute left-3.5 top-8 bottom-0 w-0.5 bg-slate-200" />
            <div className="absolute left-0 top-1 w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs border-2 shadow-sm bg-amber-400 text-slate-950 border-amber-500">
              0
            </div>
            <div className="bg-slate-50 rounded-2xl border border-slate-200 p-4 space-y-2">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-amber-400 text-slate-950 font-mono">
                    PONTO #0 • ORIGEM / PARTIDA
                  </span>
                  <h4 className="text-sm font-extrabold text-slate-900">
                    {currentRoute.ponto_origem?.nome || 'CD Nobre Lar Crateús (Matriz)'}
                  </h4>
                </div>
                <span className="text-[11px] font-mono font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                  Partida: 0.0 km
                </span>
              </div>
              <div className="text-xs text-slate-600 flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span>{currentRoute.ponto_origem?.endereco || 'Avenida Doutor Edilberto Frota, 2000, Planalto, Crateús - CE'}</span>
                </div>
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(currentRoute.ponto_origem?.endereco || 'Avenida Doutor Edilberto Frota, 2000, Planalto, Crateús - CE')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline font-medium text-xs ml-auto"
                >
                  <span>Abrir no Mapa</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="pt-1 border-t border-slate-200/60 text-[11px] text-slate-600 font-sans">
                {currentRoute.ponto_origem?.acao || 'Carregamento e conferência na doca de expedição'}
              </div>
            </div>
          </div>

          {/* Pontos 1..N: Entregas */}
          {currentRoute.paradas.map((parada) => (
            <DeliveryStopCard
              key={parada.pedido}
              parada={parada}
              isLastStop={false}
            />
          ))}

          {/* Ponto Final: Retorno ao CD */}
          <div className="relative pl-8">
            <div className="absolute left-0 top-1 w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs border-2 shadow-sm bg-slate-900 text-amber-400 border-slate-800">
              🏁
            </div>
            <div className="bg-slate-50 rounded-2xl border border-slate-200 p-4 space-y-2">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-slate-900 text-white font-mono">
                    PONTO #{currentRoute.paradas.length + 1} • RETORNO AO CD
                  </span>
                  <h4 className="text-sm font-extrabold text-slate-900">
                    {currentRoute.ponto_retorno?.nome || 'CD Nobre Lar Crateús (Matriz)'}
                  </h4>
                </div>
                <span className="text-[11px] font-mono font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
                  Distância Total: {currentRoute.distancia_estimada_km.toFixed(1)} km
                </span>
              </div>
              <div className="text-xs text-slate-600 flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span>{currentRoute.ponto_retorno?.endereco || 'Avenida Doutor Edilberto Frota, 2000, Planalto, Crateús - CE'}</span>
                </div>
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(currentRoute.ponto_retorno?.endereco || 'Avenida Doutor Edilberto Frota, 2000, Planalto, Crateús - CE')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline font-medium text-xs ml-auto"
                >
                  <span>Abrir no Mapa</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="flex items-center gap-3 pt-1 border-t border-slate-200/60 text-[11px] text-slate-600 font-sans flex-wrap">
                {currentRoute.ponto_retorno?.distancia_trecho_km !== undefined && (
                  <span className="text-amber-700 font-bold font-mono">+{currentRoute.ponto_retorno.distancia_trecho_km.toFixed(1)} km do último cliente</span>
                )}
                <span className="text-slate-400">•</span>
                <span>{currentRoute.ponto_retorno?.acao || 'Retorno ao Centro de Distribuição Nobre Lar'}</span>
              </div>
            </div>
          </div>

        </div>
      </div>

    </div>
  );
};

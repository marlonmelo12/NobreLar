import React, { useState } from 'react';
import { CargaCaminhaoViagem } from '../../types/dispatch';
import { VehicleMetricsCard } from './VehicleMetricsCard';
import { OrderDrilldownCard } from './OrderDrilldownCard';
import { Truck, Layers } from 'lucide-react';

interface TruckLoadViewProps {
  cargas: CargaCaminhaoViagem[];
}

export const TruckLoadView: React.FC<TruckLoadViewProps> = ({ cargas }) => {
  const [selectedTripIndex, setSelectedTripIndex] = useState(0);

  if (!cargas || cargas.length === 0) {
    return (
      <div className="max-w-6xl mx-auto py-8 px-6 space-y-6 animate-fadeIn">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Layers className="w-8 h-8 text-amber-500" />
            <span>Cargas no Caminhão</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Ordem de carregamento dos pedidos, conferência de peso, volume e materiais da viagem.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mb-4">
            <Truck className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-slate-800">Nenhuma Viagem Alocada</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            Envie um lote de pedidos pelo Swagger ou importe um JSON na aba <strong>Preparar</strong> para calcular as cargas e o planejamento das viagens.
          </p>
        </div>
      </div>
    );
  }

  const currentTrip = cargas[selectedTripIndex] || cargas[0];

  return (
    <div className="max-w-6xl mx-auto py-8 px-6 space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <Layers className="w-8 h-8 text-amber-500" />
          <span>Cargas no Caminhão</span>
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Ordem de carregamento dos pedidos, conferência de peso, volume e materiais da viagem.
        </p>
      </div>
      
      {/* Seletor de Viagens (Abas Horizontais com Numeração Sequencial) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-3 shadow-xs">
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {cargas.map((trip, idx) => {
            const isSelected = idx === selectedTripIndex;
            const tripTitle = trip.titulo || `Viagem ${idx + 1}`;
            return (
              <button
                key={trip.viagem_id || idx}
                type="button"
                onClick={() => setSelectedTripIndex(idx)}
                className={`px-4 py-2.5 rounded-xl text-left transition shrink-0 border ${
                  isSelected
                    ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black uppercase">
                    {tripTitle}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                      isSelected ? 'bg-nobre-500 text-slate-950' : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {trip.total_pedidos} ped.
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {trip.eixo_nome} ({trip.veiculo.nome.split(' ')[0]})
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Card de Métricas do Veículo */}
      <VehicleMetricsCard trip={currentTrip} />

      {/* Lista de Pedidos a Serem Carregados com Drill-down */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
            <span>Pedidos a Serem Carregados</span>
            <span className="text-xs font-normal text-slate-500">
              ({currentTrip.pedidos_carroceria.length} pedidos)
            </span>
          </h3>
          <span className="text-xs text-slate-500">
            Clique no pedido para inspecionar os materiais
          </span>
        </div>

        <div className="space-y-2.5">
          {currentTrip.pedidos_carroceria.map((ped) => (
            <OrderDrilldownCard key={ped.pedido} pedido={ped} />
          ))}
        </div>
      </div>

    </div>
  );
};

import React, { useState } from 'react';
import { CargaCaminhaoViagem } from '../../types/dispatch';
import { VehicleMetricsCard } from './VehicleMetricsCard';
import { TruckBedDiagram } from './TruckBedDiagram';
import { OrderDrilldownCard } from './OrderDrilldownCard';
import { Truck } from 'lucide-react';

interface TruckLoadViewProps {
  cargas: CargaCaminhaoViagem[];
}

export const TruckLoadView: React.FC<TruckLoadViewProps> = ({ cargas }) => {
  const [selectedTripIndex, setSelectedTripIndex] = useState(0);

  if (!cargas || cargas.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mb-4">
          <Truck className="w-7 h-7" />
        </div>
        <h3 className="text-base font-bold text-slate-800">Nenhuma Viagem Alocada</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
          Carregue o mock de pedidos ou importe um arquivo JSON no cabeçalho e clique em &quot;Processar Lote&quot;.
        </p>
      </div>
    );
  }

  const currentTrip = cargas[selectedTripIndex] || cargas[0];
  const hasLongItems = currentTrip.pedidos_carroceria.some((p) => p.possui_itens_6m);

  return (
    <div className="space-y-6">
      
      {/* Seletor de Viagens (Abas Horizontais) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-3 shadow-xs">
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {cargas.map((trip, idx) => {
            const isSelected = idx === selectedTripIndex;
            return (
              <button
                key={trip.viagem_id}
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
                    {trip.titulo}
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

      {/* Diagrama Esquemático da Carroceria Aberta */}
      <TruckBedDiagram
        pedidos={currentTrip.pedidos_carroceria}
        allowsLongItems={currentTrip.veiculo.permite_barras_6m}
        hasLongItems={hasLongItems}
        vehicleName={currentTrip.veiculo.nome}
      />

      {/* Lista de Pedidos na Carroceria (Ordem LIFO com Drill-Down) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
            <span>Sequência Física de Carregamento no Galpão (LIFO)</span>
            <span className="text-xs font-normal text-slate-500">
              ({currentTrip.pedidos_carroceria.length} pedidos)
            </span>
          </h3>
          <span className="text-xs text-slate-500">
            Clique no pedido para inspecionar os materiais (drill-down)
          </span>
        </div>

        <div className="space-y-3">
          {currentTrip.pedidos_carroceria.map((ped) => (
            <OrderDrilldownCard key={ped.pedido} pedido={ped} />
          ))}
        </div>
      </div>

    </div>
  );
};

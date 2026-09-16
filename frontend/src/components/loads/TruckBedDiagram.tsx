import React from 'react';
import { PedidoCarroceriaItem } from '../../types/dispatch';
import { SituacaoBadge } from '../common/Badge';
import { AlertTriangle, ArrowRight, ShieldCheck } from 'lucide-react';

interface TruckBedDiagramProps {
  pedidos: PedidoCarroceriaItem[];
  allowsLongItems: boolean;
  hasLongItems: boolean;
  vehicleName: string;
}

export const TruckBedDiagram: React.FC<TruckBedDiagramProps> = ({
  pedidos,
  hasLongItems,
  vehicleName,
}) => {
  // Ordena os pedidos pela ordem física de carregamento (LIFO)
  // 1º Carregado fica na Frente (Fundo do Assoalho)
  // Último Carregado fica na Traseira (Acesso Imediato)
  const sortedByLoading = [...pedidos].sort((a, b) => a.ordem_carregamento - b.ordem_carregamento);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
            <span>Mapa Físico de Estivagem na Carroceria Aberta (LIFO)</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-nobre-100 text-nobre-900 border border-nobre-400">
              Grade Baixa
            </span>
          </h3>
          <p className="text-xs text-slate-500">
            Último pedido a entrar no galpão é o primeiro a ser entregue (Traseira $\rightarrow$ Acesso Imediato)
          </p>
        </div>

        {hasLongItems && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-300 rounded-lg text-xs font-bold text-amber-800 animate-pulse">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Tubos/Barras 6m: Cintas & Catracas Laterais</span>
          </div>
        )}
      </div>

      {/* Esquema Visual da Carroceria Aberta */}
      <div className="relative border-2 border-slate-800 rounded-2xl bg-slate-900 p-4 sm:p-6 overflow-hidden text-white shadow-inner">
        {/* Cabine do Caminhão (Lado Esquerdo) */}
        <div className="flex flex-col md:flex-row items-stretch gap-3 relative">
          
          {/* Cabine */}
          <div className="w-full md:w-28 bg-slate-800 border-2 border-slate-700 rounded-xl p-3 flex flex-col items-center justify-center text-center shrink-0 shadow-md">
            <div className="w-10 h-10 rounded-lg bg-nobre-500 text-slate-950 font-black flex items-center justify-center text-sm shadow-sm mb-1.5">
              CAB
            </div>
            <span className="text-[11px] font-bold text-slate-200 uppercase tracking-wider">Cabine</span>
            <span className="text-[9px] text-slate-400 leading-tight mt-0.5">{vehicleName.split(' ')[0]}</span>
          </div>

          {/* Assoalho da Carroceria Aberta */}
          <div className="flex-1 bg-slate-950 border border-slate-800 rounded-xl p-3 relative flex flex-col justify-between min-h-[220px]">
            
            {/* Faixa Lateral Superior para Barras de 6 Metros (se houver) */}
            {hasLongItems && (
              <div className="mb-2.5 px-3 py-1.5 bg-amber-500/15 border border-dashed border-amber-400 rounded-lg flex items-center justify-between text-[11px] text-amber-300">
                <span className="font-bold flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                  Fueiro Lateral: Fixação de Tubos / Barras de 6m com Catracas
                </span>
                <span className="font-mono text-[10px] text-amber-400 font-semibold uppercase">
                  Amarração Obrigatória
                </span>
              </div>
            )}

            {/* Baías de Carga: Frente -> Meio -> Traseira */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {sortedByLoading.map((ped) => {
                const isFirstLoaded = ped.ordem_carregamento === 1; // Fundo/Frente
                const isLastLoaded = ped.ordem_carregamento === sortedByLoading.length; // Traseira
                
                return (
                  <div
                    key={ped.pedido}
                    className={`rounded-xl p-3 border transition flex flex-col justify-between ${
                      isLastLoaded
                        ? 'bg-nobre-500/10 border-nobre-400/80 shadow-sm'
                        : isFirstLoaded
                        ? 'bg-slate-800/80 border-slate-700'
                        : 'bg-slate-900 border-slate-800'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-1 mb-1.5">
                        <span
                          className={`text-[10px] font-black px-2 py-0.5 rounded-md ${
                            isLastLoaded
                              ? 'bg-nobre-500 text-slate-950'
                              : 'bg-slate-700 text-slate-200'
                          }`}
                        >
                          {ped.ordem_carregamento}º CARREGADO
                        </span>
                        <SituacaoBadge situacao={ped.situacao} />
                      </div>

                      <div className="text-xs font-bold text-white truncate" title={ped.cliente || ped.pedido}>
                        {ped.cliente || ped.pedido}
                      </div>
                      <div className="text-[11px] text-nobre-400 font-semibold">
                        {ped.cidade}
                      </div>
                    </div>

                    <div className="mt-3 pt-2 border-t border-slate-800/80 space-y-1 text-[11px]">
                      <div className="flex justify-between text-slate-400">
                        <span>Posição:</span>
                        <span className="font-medium text-slate-200 text-right truncate max-w-[130px]" title={ped.posicao_carroceria}>
                          {isLastLoaded ? 'Traseira' : isFirstLoaded ? 'Frente (Fundo)' : 'Meio'}
                        </span>
                      </div>
                      <div className="flex justify-between text-slate-400 font-mono">
                        <span>Carga:</span>
                        <span className="text-white font-semibold">{ped.peso_total_kg.toFixed(0)} kg</span>
                      </div>
                      <div className="flex justify-between text-slate-400 font-mono">
                        <span>Descarga Prevista:</span>
                        <span className="text-nobre-400 font-bold">{ped.ordem_entrega_prevista}ª Parada</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Régua de Orientação LIFO */}
            <div className="mt-3 pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-medium">
              <span className="flex items-center gap-1 text-slate-300">
                <span className="w-2 h-2 rounded-full bg-slate-500" />
                Frente (Fundo do Assoalho)
              </span>
              <div className="flex items-center gap-1.5 text-nobre-400 font-bold">
                <span>Sequência de Descarga</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
              <span className="flex items-center gap-1 text-nobre-400 font-bold">
                Traseira (Acesso Imediato)
                <span className="w-2 h-2 rounded-full bg-nobre-500 animate-pulse" />
              </span>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { ParadaEntregaItem } from '../../types/dispatch';
import { OrderMaterialsModal } from '../common/OrderMaterialsModal';
import { MapPin, Package, ExternalLink, Navigation, ChevronRight } from 'lucide-react';

interface DeliveryStopCardProps {
  parada: ParadaEntregaItem;
  isLastStop?: boolean;
}

export const DeliveryStopCard: React.FC<DeliveryStopCardProps> = ({ parada, isLastStop = false }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const pontoNum = parada.ponto_numero || parada.parada;

  // O mapa abre exclusivamente com o endereço fornecido (coordenadas ficam no backend para o TSP)
  const fullAddress = parada.endereco_completo || `${parada.cidade}, CE`;
  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(fullAddress)}`;

  return (
    <>
      <div className="relative pl-8 pb-6 last:pb-0">
        {/* Linha Vertical da Linha do Tempo */}
        {!isLastStop && (
          <div className="absolute left-3.5 top-8 bottom-0 w-0.5 bg-slate-200" />
        )}

        {/* Marcador do Ponto de Parada */}
        <div className="absolute left-0 top-1 w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs border-2 shadow-xs bg-slate-900 text-nobre-400 border-slate-800">
          {pontoNum}
        </div>

        {/* Card da Parada */}
        <div
          onClick={() => setIsModalOpen(true)}
          className="bg-white rounded-xl border border-slate-200 transition shadow-xs overflow-hidden cursor-pointer hover:border-slate-300 hover:shadow-xs"
        >
          <div className="p-4 sm:p-5 space-y-3">
            {/* Cabeçalho da Parada Clean */}
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-mono font-bold text-slate-400">
                    Parada #{pontoNum}
                  </span>
                  <span className="text-xs font-mono font-semibold text-slate-500">
                    {parada.pedido}
                  </span>
                  <h4 className="text-sm font-bold text-slate-900">
                    {parada.cliente || 'Consumidor'}
                  </h4>
                  {parada.situacao === 'URGENTE' && (
                    <span className="text-xs font-bold text-rose-600">
                      (Urgente)
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5 text-xs text-slate-700">
                  <MapPin className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span className="font-semibold text-slate-800">{parada.cidade}</span>
                  <span className="text-slate-500">— {parada.endereco_completo}</span>
                </div>
              </div>

              {/* Valor do Pedido */}
              <div className="text-right shrink-0">
                <div className="text-[11px] text-slate-400">Valor</div>
                <div className="text-xs font-extrabold text-emerald-700 font-mono">
                  R$ {parada.valor_pedido.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>

            {/* Informações do Itinerário e Link do Mapa por Endereço */}
            <div className="flex items-center justify-between flex-wrap gap-2 pt-2 border-t border-slate-100 text-xs">
              <div className="flex items-center gap-3 text-slate-500 text-[11px]">
                {parada.distancia_trecho_km !== undefined && (
                  <span className="flex items-center gap-1 text-slate-700 font-medium">
                    <Navigation className="w-3 h-3 text-amber-600" />
                    +{parada.distancia_trecho_km.toFixed(1)} km do ponto anterior
                  </span>
                )}
                <span>•</span>
                <span>{parada.peso_total_kg.toFixed(1)} kg</span>
              </div>

              <div className="flex items-center gap-3 ml-auto">
                <a
                  href={mapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline font-medium text-xs"
                >
                  <span>Abrir no Mapa</span>
                  <ExternalLink className="w-3 h-3" />
                </a>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsModalOpen(true);
                  }}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition"
                >
                  <Package className="w-3 h-3 text-slate-500" />
                  <span>Ver Itens ({parada.itens.length})</span>
                  <ChevronRight className="w-3 h-3" />
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* Modal Limpo de Materiais da Entrega */}
      <OrderMaterialsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        tipoModal="entrega"
        ordemOuPonto={pontoNum}
        pedidoId={parada.pedido}
        cliente={parada.cliente}
        cidade={parada.cidade}
        endereco={parada.endereco_completo}
        situacao={parada.situacao}
        valorTotal={parada.valor_pedido}
        pesoTotalKg={parada.peso_total_kg}
        volumeTotalM3={parada.volume_total_m3}
        itens={parada.itens}
      />
    </>
  );
};

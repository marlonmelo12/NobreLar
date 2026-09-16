import React, { useState } from 'react';
import { ParadaEntregaItem } from '../../types/dispatch';
import { SituacaoBadge } from '../common/Badge';
import { OrderMaterialsModal } from '../common/OrderMaterialsModal';
import { MapPin, AlertCircle, CheckCircle2, Package, CreditCard, ExternalLink, Navigation, ChevronRight } from 'lucide-react';

interface DeliveryStopCardProps {
  parada: ParadaEntregaItem;
  isLastStop?: boolean;
}

export const DeliveryStopCard: React.FC<DeliveryStopCardProps> = ({ parada, isLastStop = false }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const isCollect = parada.status_pagamento === 'A RECEBER';
  const pontoNum = parada.ponto_numero || parada.parada;

  return (
    <>
      <div className="relative pl-8 pb-7 last:pb-0">
        
        {/* Linha Vertical da Linha do Tempo */}
        {!isLastStop && (
          <div className="absolute left-3.5 top-8 bottom-0 w-0.5 bg-slate-200" />
        )}

        {/* Marcador do Ponto de Parada */}
        <div
          className={`absolute left-0 top-1 w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs border-2 shadow-sm ${
            isCollect
              ? 'bg-red-500 text-white border-red-600 ring-4 ring-red-100 animate-pulse'
              : 'bg-slate-900 text-nobre-400 border-slate-800'
          }`}
        >
          {pontoNum}
        </div>

        {/* Card da Parada */}
        <div
          onClick={() => setIsModalOpen(true)}
          className={`bg-white rounded-xl border transition shadow-xs overflow-hidden cursor-pointer hover:border-slate-400 hover:shadow-sm ${
            isCollect ? 'border-red-300 ring-1 ring-red-200' : 'border-slate-200'
          }`}
        >
          {/* Banner de Cobrança Mandatória se for A RECEBER */}
          {isCollect && (
            <div className="bg-red-600 text-white px-4 py-2 flex items-center justify-between text-xs font-bold">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-white shrink-0" />
                <span>COBRANÇA OBRIGATÓRIA NO ATO DA ENTREGA</span>
              </div>
              <span className="font-mono text-xs tracking-wide bg-red-700 px-2 py-0.5 rounded">
                Receber: R$ {parada.valor_a_receber.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </span>
            </div>
          )}

          <div className="p-4 sm:p-5 space-y-3">
            {/* Cabeçalho da Parada */}
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2.5 py-0.5 rounded-md text-xs font-black bg-slate-900 text-white font-mono">
                    PONTO #{pontoNum}
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-500">
                    {parada.pedido}
                  </span>
                  <h4 className="text-sm font-extrabold text-slate-900">
                    {parada.cliente || 'Consumidor'}
                  </h4>
                  <SituacaoBadge situacao={parada.situacao} />
                </div>

                <div className="flex items-center gap-1.5 text-xs text-slate-700 font-semibold mt-1">
                  <MapPin className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span>{parada.cidade}</span>
                  <span className="text-slate-400 font-normal">— {parada.endereco_completo}</span>
                </div>

                {/* Informações Geográficas do Ponto */}
                <div className="flex items-center gap-3 flex-wrap mt-2 pt-2 border-t border-slate-100 text-[11px] text-slate-500 font-mono">
                  {parada.latitude !== undefined && parada.longitude !== undefined && (
                    <span className="flex items-center gap-1 bg-slate-100 px-2 py-0.5 rounded text-slate-700">
                      📍 {parada.latitude.toFixed(4)}, {parada.longitude.toFixed(4)}
                    </span>
                  )}
                  {parada.distancia_trecho_km !== undefined && (
                    <span className="flex items-center gap-1 bg-amber-50 text-amber-900 border border-amber-200 px-2 py-0.5 rounded font-bold">
                      <Navigation className="w-3 h-3 text-amber-600" />
                      +{parada.distancia_trecho_km.toFixed(1)} km do ponto anterior
                    </span>
                  )}
                  {parada.google_maps_url && (
                    <a
                      href={parada.google_maps_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline font-sans font-medium ml-auto"
                    >
                      <span>Abrir no Mapa</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>

              {/* Status de Pagamento e Valor */}
              <div className="text-right shrink-0">
                {isCollect ? (
                  <div className="text-red-700 text-xs font-bold flex items-center gap-1 sm:justify-end">
                    <CreditCard className="w-4 h-4" />
                    <span>A RECEBER</span>
                  </div>
                ) : (
                  <div className="text-emerald-700 text-xs font-bold flex items-center gap-1 sm:justify-end">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>QUITADO</span>
                  </div>
                )}
                <div className="text-xs font-extrabold text-slate-900 font-mono mt-0.5">
                  R$ {parada.valor_pedido.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>

            {/* Alerta de Cobrança PIX / Dinheiro */}
            {parada.alerta_cobranca && (
              <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800 font-bold flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                <span>{parada.alerta_cobranca}</span>
              </div>
            )}

            {/* Barra Inferior com Ação de Ver Itens */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
              <div className="text-slate-500 text-[11px] flex items-center gap-3">
                <span>Peso: <strong className="text-slate-800 font-mono">{parada.peso_total_kg.toFixed(1)} kg</strong></span>
                <span>•</span>
                <span>Volume: <strong className="text-slate-800 font-mono">{parada.volume_total_m3.toFixed(3)} m³</strong></span>
              </div>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsModalOpen(true);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-nobre-500 hover:text-slate-950 text-slate-700 text-xs font-bold transition shadow-xs"
              >
                <Package className="w-3.5 h-3.5" />
                <span>Ver Itens ({parada.itens.length})</span>
                <ChevronRight className="w-3 h-3" />
              </button>
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
        statusPagamento={parada.status_pagamento}
        valorTotal={parada.valor_pedido}
        pesoTotalKg={parada.peso_total_kg}
        volumeTotalM3={parada.volume_total_m3}
        itens={parada.itens}
        alertaCobranca={parada.alerta_cobranca}
      />
    </>
  );
};

import React, { useState } from 'react';
import { ParadaEntregaItem } from '../../types/dispatch';
import { SituacaoBadge } from '../common/Badge';
import { MapPin, AlertCircle, CheckCircle2, ChevronDown, ChevronUp, Package, CreditCard } from 'lucide-react';

interface DeliveryStopCardProps {
  parada: ParadaEntregaItem;
  isLastStop?: boolean;
}

export const DeliveryStopCard: React.FC<DeliveryStopCardProps> = ({ parada, isLastStop = false }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isCollect = parada.status_pagamento === 'A RECEBER';

  return (
    <div className="relative pl-8 pb-8 last:pb-0">
      
      {/* Linha Vertical da Linha do Tempo */}
      {!isLastStop && (
        <div className="absolute left-3.5 top-8 bottom-0 w-0.5 bg-slate-200" />
      )}

      {/* Marcador do Ponto de Parada */}
      <div
        className={`absolute left-0 top-1 w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs border-2 shadow-sm ${
          isCollect
            ? 'bg-red-500 text-white border-red-600 ring-4 ring-red-100 animate-bounce'
            : 'bg-slate-900 text-nobre-400 border-slate-800'
        }`}
      >
        {parada.parada}
      </div>

      {/* Card da Parada */}
      <div
        className={`bg-white rounded-2xl border transition shadow-xs overflow-hidden ${
          isCollect ? 'border-red-300 ring-1 ring-red-200' : 'border-slate-200'
        }`}
      >
        
        {/* Banner de Cobrança Mandatória se for A RECEBER */}
        {isCollect && (
          <div className="bg-red-600 text-white px-5 py-2.5 flex items-center justify-between text-xs font-bold">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-white shrink-0" />
              <span>COBRANÇA OBRIGATÓRIA NO ATO DA ENTREGA</span>
            </div>
            <span className="font-mono text-sm tracking-wide bg-red-700 px-2 py-0.5 rounded">
              Receber: R$ {parada.valor_a_receber.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
            </span>
          </div>
        )}

        <div className="p-5 space-y-4">
          
          {/* Cabeçalho da Parada */}
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-slate-900 text-white font-mono">
                  PARADA #{parada.parada}
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
                <MapPin className="w-3.5 h-3.5 text-nobre-600 shrink-0" />
                <span>{parada.cidade}</span>
                <span className="text-slate-400 font-normal">— {parada.endereco_completo}</span>
              </div>
            </div>

            {/* Status de Pagamento */}
            <div className="text-right shrink-0">
              {isCollect ? (
                <div className="text-red-700 text-xs font-bold flex items-center gap-1 sm:justify-end">
                  <CreditCard className="w-4 h-4" />
                  <span>A RECEBER NA ENTREGA</span>
                </div>
              ) : (
                <div className="text-emerald-700 text-xs font-bold flex items-center gap-1 sm:justify-end">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>PAGAMENTO QUITADO</span>
                </div>
              )}
              <div className="text-xs font-extrabold text-slate-900 font-mono mt-0.5">
                R$ {parada.valor_pedido.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          {/* Alerta Específico de Cobrança PIX / Dinheiro */}
          {parada.alerta_cobranca && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 font-bold flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{parada.alerta_cobranca}</span>
            </div>
          )}

          {/* Posicionamento Físico de Descarga e Itens */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100 text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-700">Retirada na Carroceria:</span>
              <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 font-bold border border-slate-200">
                {parada.posicao_na_carroceria}
              </span>
            </div>

            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 hover:text-slate-900 transition"
            >
              <Package className="w-3.5 h-3.5 text-slate-500" />
              <span>Ver Itens a Descarregar ({parada.itens.length})</span>
              {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Drill-down de Descarga */}
          {isExpanded && (
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 animate-in fade-in space-y-2">
              <div className="text-[11px] font-bold text-slate-600 uppercase">
                Conferência de Descarga pelo Motorista / Ajudante:
              </div>
              <ul className="divide-y divide-slate-200/80 text-xs bg-white rounded-lg border border-slate-200">
                {parada.itens.map((it, idx) => (
                  <li key={`${it.codigo}-${idx}`} className="p-2.5 flex items-center justify-between">
                    <div>
                      <span className="font-mono font-bold text-slate-600 mr-2">{it.codigo}</span>
                      <span className="font-medium text-slate-900">{it.descricao}</span>
                    </div>
                    <div className="text-right font-mono shrink-0 ml-4">
                      <span className="font-bold text-slate-900">
                        {it.quantidade} {it.unidade}
                      </span>
                      <span className="text-slate-500 text-[11px] ml-2">
                        ({it.peso_total_kg.toFixed(0)} kg)
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

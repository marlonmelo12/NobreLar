import React, { useState } from 'react';
import { PedidoCarroceriaItem } from '../../types/dispatch';
import { OrderMaterialsModal } from '../common/OrderMaterialsModal';
import { Package, ChevronRight } from 'lucide-react';

interface OrderDrilldownCardProps {
  pedido: PedidoCarroceriaItem;
}

export const OrderDrilldownCard: React.FC<OrderDrilldownCardProps> = ({ pedido }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <div
        onClick={() => setIsModalOpen(true)}
        className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs hover:border-slate-300 hover:shadow-xs transition cursor-pointer group"
      >
        <div className="p-4 sm:p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            {/* Numeração Simples e Limpa (sem bloco preto) */}
            <span className="text-sm font-mono font-bold text-slate-400 w-7 text-center shrink-0">
              #{pedido.ordem_carregamento}
            </span>

            <div className="space-y-1">
              {/* Nome do Cliente e Pedido Limpos (sem contornos de badges) */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono text-slate-400 font-semibold">
                  {pedido.pedido}
                </span>
                <span className="text-sm font-bold text-slate-900">
                  {pedido.cliente || 'Consumidor Final'}
                </span>
                {pedido.urgente && (
                  <span className="text-xs font-bold text-rose-600">
                    (Urgente)
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-600">
                <span className="font-semibold text-slate-800">{pedido.cidade}</span> — {pedido.endereco}
              </p>

              <div className="text-[11px] text-slate-500 flex items-center gap-2">
                <span>
                  Descarga prevista: <strong className="text-slate-800">{pedido.ordem_entrega_prevista}ª Parada</strong>
                </span>
                <span className="text-slate-300">•</span>
                <span className="text-amber-700 font-medium flex items-center gap-1">
                  <Package className="w-3 h-3" />
                  {pedido.itens.length} materiais a carregar
                </span>
              </div>
            </div>
          </div>

          {/* Métricas e Botão Ação */}
          <div className="flex items-center justify-between lg:justify-end gap-5 pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-100">
            <div className="flex items-center gap-4 text-right">
              <div>
                <div className="text-[11px] text-slate-400">Peso</div>
                <div className="text-xs font-extrabold text-slate-900 font-mono">
                  {pedido.peso_total_kg.toFixed(1)} kg
                </div>
              </div>

              <div>
                <div className="text-[11px] text-slate-400">Volume</div>
                <div className="text-xs font-extrabold text-slate-900 font-mono">
                  {pedido.volume_total_m3.toFixed(3)} m³
                </div>
              </div>

              <div>
                <div className="text-[11px] text-slate-400">Valor</div>
                <div className="text-xs font-extrabold text-emerald-700 font-mono">
                  R$ {pedido.valor_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setIsModalOpen(true);
              }}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition shadow-xs"
            >
              <span>Ver Materiais</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Modal Limpo de Materiais */}
      <OrderMaterialsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        tipoModal="carga"
        ordemOuPonto={pedido.ordem_carregamento}
        pedidoId={pedido.pedido}
        cliente={pedido.cliente}
        cidade={pedido.cidade}
        endereco={pedido.endereco}
        situacao={pedido.situacao}
        valorTotal={pedido.valor_total}
        pesoTotalKg={pedido.peso_total_kg}
        volumeTotalM3={pedido.volume_total_m3}
        itens={pedido.itens}
      />
    </>
  );
};

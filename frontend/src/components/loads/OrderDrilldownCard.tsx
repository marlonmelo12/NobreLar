import React, { useState } from 'react';
import { PedidoCarroceriaItem } from '../../types/dispatch';
import { SituacaoBadge, Badge } from '../common/Badge';
import { ChevronDown, ChevronUp, Package, AlertTriangle, CreditCard } from 'lucide-react';

interface OrderDrilldownCardProps {
  pedido: PedidoCarroceriaItem;
}

export const OrderDrilldownCard: React.FC<OrderDrilldownCardProps> = ({ pedido }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const isCollect = pedido.pagamento_na_entrega === 'A RECEBER';

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs hover:border-slate-300 transition">
      
      {/* Linha Resumo do Pedido */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-4 sm:p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4 cursor-pointer hover:bg-slate-50/80 transition"
      >
        <div className="flex items-start gap-3.5">
          {/* Ordem de Carregamento */}
          <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex flex-col items-center justify-center shrink-0 font-mono shadow-sm">
            <span className="text-[9px] text-slate-400 uppercase leading-none">Carga</span>
            <span className="text-sm font-black text-nobre-400 leading-none mt-0.5">
              #{pedido.ordem_carregamento}
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-bold text-slate-500 font-mono">
                {pedido.pedido}
              </span>
              <h4 className="text-sm font-extrabold text-slate-900">
                {pedido.cliente || 'Consumidor Final'}
              </h4>
              <SituacaoBadge situacao={pedido.situacao} />
              
              {isCollect && (
                <Badge variant="collect" icon={<CreditCard className="w-3 h-3" />}>
                  A RECEBER NA ENTREGA
                </Badge>
              )}

              {pedido.possui_itens_6m && (
                <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300 inline-flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-amber-600" />
                  Peça 6m
                </span>
              )}
            </div>

            <p className="text-xs text-slate-600">
              <span className="font-semibold text-slate-900">{pedido.cidade}</span> — {pedido.endereco}
            </p>

            <div className="text-[11px] text-slate-500 flex items-center gap-2">
              <span className="font-medium text-slate-700">Posição:</span>
              <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-800 font-semibold border border-slate-200">
                {pedido.posicao_carroceria}
              </span>
              <span className="text-slate-400">•</span>
              <span>Descarga prevista: <strong className="text-slate-800">{pedido.ordem_entrega_prevista}ª Parada</strong></span>
            </div>
          </div>
        </div>

        {/* Métricas e Botão de Expansão */}
        <div className="flex items-center justify-between lg:justify-end gap-6 pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-100">
          <div className="flex items-center gap-4 text-right">
            <div>
              <div className="text-xs text-slate-400">Peso Total</div>
              <div className="text-xs font-extrabold text-slate-900 font-mono">
                {pedido.peso_total_kg.toFixed(1)} kg
              </div>
            </div>

            <div>
              <div className="text-xs text-slate-400">Volume</div>
              <div className="text-xs font-extrabold text-slate-900 font-mono">
                {pedido.volume_total_m3.toFixed(3)} m³
              </div>
            </div>

            <div>
              <div className="text-xs text-slate-400">Valor do Pedido</div>
              <div className="text-sm font-extrabold text-emerald-700 font-mono">
                R$ {pedido.valor_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          <button
            type="button"
            className="p-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Drill-down de Itens Expandido */}
      {isExpanded && (
        <div className="bg-slate-50 p-4 sm:p-5 border-t border-slate-200 animate-in fade-in">
          <div className="flex items-center justify-between mb-3">
            <h5 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Package className="w-3.5 h-3.5 text-slate-500" />
              <span>Itens Faturados do Pedido ({pedido.itens.length} SKUs)</span>
            </h5>
            <span className="text-[11px] text-slate-500">
              Cubagem técnica baseada no Ranking Top 85 Nobre Lar
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100/80 text-slate-700 border-b border-slate-200 font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Código</th>
                  <th className="py-2.5 px-3">Descrição do Material</th>
                  <th className="py-2.5 px-3 text-right">Qtd</th>
                  <th className="py-2.5 px-3 text-center">Unid</th>
                  <th className="py-2.5 px-3 text-right">Peso Unit</th>
                  <th className="py-2.5 px-3 text-right">Peso Total</th>
                  <th className="py-2.5 px-3 text-right">Volume</th>
                  <th className="py-2.5 px-3 text-center">Especial</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pedido.itens.map((it, idx) => (
                  <tr key={`${it.codigo}-${idx}`} className="hover:bg-slate-50 transition">
                    <td className="py-2 px-3 font-mono font-bold text-slate-600">{it.codigo}</td>
                    <td className="py-2 px-3 font-medium text-slate-900">{it.descricao}</td>
                    <td className="py-2 px-3 text-right font-mono font-bold text-slate-900">
                      {it.quantidade.toLocaleString('pt-BR')}
                    </td>
                    <td className="py-2 px-3 text-center font-mono text-slate-600">{it.unidade}</td>
                    <td className="py-2 px-3 text-right font-mono text-slate-600">
                      {it.peso_unitario_kg.toFixed(2)} kg
                    </td>
                    <td className="py-2 px-3 text-right font-mono font-bold text-slate-900">
                      {it.peso_total_kg.toFixed(1)} kg
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-slate-600">
                      {it.volume_total_m3.toFixed(4)} m³
                    </td>
                    <td className="py-2 px-3 text-center">
                      {it.e_item_6m ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                          6 METROS
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[10px]">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
};

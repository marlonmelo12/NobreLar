import React, { useEffect } from 'react';
import { ItemDrillDown } from '../../types/dispatch';
import { X, Package, Weight, Box, DollarSign } from 'lucide-react';

export interface OrderMaterialsModalProps {
  isOpen: boolean;
  onClose: () => void;
  tipoModal?: 'carga' | 'entrega';
  ordemOuPonto?: number;
  pedidoId: string;
  cliente?: string | null;
  cidade?: string;
  endereco?: string;
  situacao?: string;
  valorTotal?: number;
  pesoTotalKg?: number;
  volumeTotalM3?: number;
  itens: ItemDrillDown[];
}

export const OrderMaterialsModal: React.FC<OrderMaterialsModalProps> = ({
  isOpen,
  onClose,
  tipoModal = 'carga',
  ordemOuPonto,
  pedidoId,
  cliente,
  cidade,
  endereco,
  valorTotal = 0,
  pesoTotalKg = 0,
  volumeTotalM3 = 0,
  itens,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabeçalho Limpo do Modal */}
        <div className="p-5 border-b border-slate-200 bg-slate-50/80 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono font-bold text-slate-400">
                {tipoModal === 'carga' ? `Carga #${ordemOuPonto || 1}` : `Parada #${ordemOuPonto || 1}`}
              </span>
              <span className="text-xs font-mono font-semibold text-slate-500">
                {pedidoId}
              </span>
              <h3 className="text-base font-bold text-slate-900">
                {cliente || 'Consumidor Final'}
              </h3>
            </div>

            {(cidade || endereco) && (
              <p className="text-xs text-slate-600">
                {cidade && <strong className="text-slate-800">{cidade}</strong>}
                {cidade && endereco ? ' — ' : ''}
                {endereco}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition shrink-0"
            title="Fechar (ESC)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Resumo compacto de métricas do pedido */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-4 bg-slate-50/40 border-b border-slate-100 text-xs">
          <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200">
            <Package className="w-4 h-4 text-slate-500 shrink-0" />
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Itens</div>
              <div className="font-mono font-bold text-slate-800">{itens.length} SKUs</div>
            </div>
          </div>

          <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200">
            <Weight className="w-4 h-4 text-slate-500 shrink-0" />
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Peso</div>
              <div className="font-mono font-bold text-slate-800">{pesoTotalKg.toFixed(1)} kg</div>
            </div>
          </div>

          <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200">
            <Box className="w-4 h-4 text-slate-500 shrink-0" />
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Volume</div>
              <div className="font-mono font-bold text-slate-800">{volumeTotalM3.toFixed(3)} m³</div>
            </div>
          </div>

          <div className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200">
            <DollarSign className="w-4 h-4 text-emerald-600 shrink-0" />
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Valor</div>
              <div className="font-mono font-bold text-emerald-700">
                R$ {valorTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        </div>

        {/* Tabela de Materiais (Scrollável) */}
        <div className="p-4 overflow-y-auto flex-1">
          <div className="rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Código</th>
                  <th className="py-2.5 px-3">Descrição do Material</th>
                  <th className="py-2.5 px-3 text-right">Qtd</th>
                  <th className="py-2.5 px-3 text-center">Unid</th>
                  <th className="py-2.5 px-3 text-right">Peso Unit</th>
                  <th className="py-2.5 px-3 text-right">Peso Total</th>
                  <th className="py-2.5 px-3 text-right">Volume</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {itens.map((it, idx) => (
                  <tr key={`${it.codigo}-${idx}`} className="hover:bg-slate-50 transition">
                    <td className="py-2 px-3 font-mono font-bold text-slate-600">{it.codigo}</td>
                    <td className="py-2 px-3 font-medium text-slate-900">{it.descricao}</td>
                    <td className="py-2 px-3 text-right font-mono font-extrabold text-slate-900">
                      {it.quantidade.toLocaleString('pt-BR')}
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className={`px-1.5 py-0.5 rounded text-[11px] font-mono font-bold ${
                        it.unidade === 'CX'
                          ? 'bg-amber-100 text-amber-900 border border-amber-300'
                          : 'bg-slate-100 text-slate-700'
                      }`}>
                        {it.unidade}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-slate-600">
                      {it.peso_unitario_kg.toFixed(2)} kg
                    </td>
                    <td className="py-2 px-3 text-right font-mono font-bold text-slate-900">
                      {it.peso_total_kg.toFixed(1)} kg
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-slate-600">
                      {it.volume_total_m3.toFixed(4)} m³
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Rodapé com Ações */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/60 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">
            Total de {itens.length} material(is) registrado(s) neste pedido.
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-100 transition shadow-xs"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};

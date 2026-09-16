import React, { useState, useMemo } from 'react';
import { DecoupledOrderInput } from '../../types/dispatch';
import { SituacaoBadge } from '../common/Badge';
import { Search, Filter, ListOrdered, DollarSign, MapPin } from 'lucide-react';

interface RawOrdersViewProps {
  orders: DecoupledOrderInput[];
}

export const RawOrdersView: React.FC<RawOrdersViewProps> = ({ orders }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [situacaoFilter, setSituacaoFilter] = useState<string>('TODOS');

  const filteredOrders = useMemo(() => {
    return orders.filter((o) => {
      const matchSearch =
        o.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (o.cliente && o.cliente.toLowerCase().includes(searchTerm.toLowerCase())) ||
        o.cidade.toLowerCase().includes(searchTerm.toLowerCase());

      const matchSituacao =
        situacaoFilter === 'TODOS' || o.situacao.toUpperCase() === situacaoFilter.toUpperCase();

      return matchSearch && matchSituacao;
    });
  }, [orders, searchTerm, situacaoFilter]);

  const totalValue = useMemo(() => {
    return orders.reduce((acc, o) => acc + (o.valor || 0), 0);
  }, [orders]);

  const uniqueCities = useMemo(() => {
    return new Set(orders.map((o) => o.cidade)).size;
  }, [orders]);

  return (
    <div className="space-y-6">
      
      {/* Cards de Resumo do Lote */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-nobre-400 flex items-center justify-center font-bold">
              <ListOrdered className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-500">Pedidos no Lote</span>
              <div className="text-lg font-black text-slate-900 font-mono">
                {orders.length} pedidos
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center font-bold">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-500">Faturamento Bruto</span>
              <div className="text-lg font-black text-emerald-700 font-mono">
                R$ {totalValue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-nobre-50 text-nobre-800 border border-nobre-200 flex items-center justify-center font-bold">
              <MapPin className="w-5 h-5 text-nobre-600" />
            </div>
            <div>
              <span className="text-xs text-slate-500">Cidades / Destinos</span>
              <div className="text-lg font-black text-slate-900 font-mono">
                {uniqueCities} localidades
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Barra de Filtros e Busca */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por cliente, código ou cidade..."
            className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-nobre-500 text-slate-900 placeholder:text-slate-400"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          <span className="text-xs text-slate-500 font-medium">Situação:</span>
          <select
            value={situacaoFilter}
            onChange={(e) => setSituacaoFilter(e.target.value)}
            className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-nobre-500 cursor-pointer"
          >
            <option value="TODOS">Todas ({orders.length})</option>
            <option value="NORMAL">NORMAL</option>
            <option value="URGENTE">URGENTE</option>
            <option value="CARRO HORARIO">CARRO HORÁRIO</option>
            <option value="PROGRAMADO">PROGRAMADO</option>
            <option value="TOPIQUE">TOPIQUE</option>
            <option value="RETIRADA">RETIRADA BALCÃO</option>
            <option value="CANCELADO">CANCELADO</option>
          </select>
        </div>
      </div>

      {/* Tabela de Pedidos do Lote */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Pedido ID</th>
                <th className="py-3 px-4">Cliente</th>
                <th className="py-3 px-4">Cidade & Endereço</th>
                <th className="py-3 px-4 text-center">Situação</th>
                <th className="py-3 px-4 text-right">Valor</th>
                <th className="py-3 px-4 text-center">Itens</th>
                <th className="py-3 px-4 text-center">Cobrança</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredOrders.map((o) => (
                <tr key={o.id} className="hover:bg-slate-50 transition">
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">{o.id}</td>
                  <td className="py-3 px-4 font-bold text-slate-900">{o.cliente || '—'}</td>
                  <td className="py-3 px-4">
                    <span className="font-semibold text-slate-900">{o.cidade}</span>
                    <span className="text-slate-500 block truncate max-w-xs">{o.endereco}</span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <SituacaoBadge situacao={o.situacao} />
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                    R$ {(o.valor || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4 text-center font-mono font-semibold text-slate-600">
                    {o.itens ? o.itens.length : 0} SKUs
                  </td>
                  <td className="py-3 px-4 text-center">
                    {o.pagamento_entrega === 'A RECEBER' ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700 border border-red-300">
                        A RECEBER
                      </span>
                    ) : (
                      <span className="text-slate-400 text-[10px]">PAGO</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

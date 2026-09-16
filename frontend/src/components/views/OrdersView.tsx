import React, { useEffect, useState, useMemo } from 'react';
import { api } from '../../services/api';
import {
  UnifiedOrderItem,
  OrderAllocationStatus,
  DecoupledOrderInput,
  DecoupledDispatchResponse,
} from '../../types/dispatch';
import {
  Package,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Search,
  RefreshCw,
  Eye,
  X,
  Truck,
  MapPin,
  Calendar,
  Layers,
} from 'lucide-react';

interface OrdersViewProps {
  dispatchResult: DecoupledDispatchResponse | null;
  uploadedOrders: DecoupledOrderInput[];
  onNavigateToPrepare?: () => void;
}

export const OrdersView: React.FC<OrdersViewProps> = ({
  dispatchResult,
  uploadedOrders,
  onNavigateToPrepare,
}) => {
  const [orders, setOrders] = useState<UnifiedOrderItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | OrderAllocationStatus>('ALL');
  const [selectedOrderForDrilldown, setSelectedOrderForDrilldown] = useState<UnifiedOrderItem | null>(null);

  // Carrega os pedidos unificados da API ou sincroniza com o lote carregado/despachado
  const loadOrders = async () => {
    setLoading(true);
    try {
      const data = await api.fetchAllOrders();
      if (data && data.pedidos && data.pedidos.length > 0) {
        setOrders(data.pedidos);
      } else if (uploadedOrders && uploadedOrders.length > 0) {
        // Fallback: se há pedidos carregados no estado do front mas sem despacho no backend
        const mappedFromUploaded: UnifiedOrderItem[] = uploadedOrders.map((o) => {
          const totalW = (o.itens || []).reduce((acc, it) => acc + it.quantidade * 25.0, 0);
          const totalV = (o.itens || []).reduce((acc, it) => acc + it.quantidade * 0.015, 0);
          const totalVal = o.valor || (o.itens || []).reduce((acc, it) => acc + (it.subtotal || it.quantidade * (it.preco_unitario || 38.0)), 0);

          return {
            id: String(o.id || 'SEM_ID'),
            external_id: String(o.id || 'SEM_ID'),
            cliente: o.cliente || 'Cliente Nobre Lar',
            cidade: o.cidade || 'Crateús',
            endereco: o.endereco || o.cidade || 'Crateús - CE',
            situacao: o.situacao || 'NORMAL',
            peso_kg: totalW,
            volume_m3: totalV,
            valor: totalVal,
            status: 'PENDENTE' as OrderAllocationStatus,
            status_label: 'Aguardando Otimização',
            viagem_id: null,
            viagem_titulo: null,
            veiculo_nome: null,
            veiculo_placa: null,
            eixo_nome: 'Crateús Urbano',
            ordem_carregamento: null,
            ordem_entrega: null,
            motivo: 'Lote importado aguardando execução da otimização.',
            itens: (o.itens || []).map((it) => ({
              codigo: it.codigo || '00000',
              descricao: it.descricao,
              quantidade: it.quantidade,
              unidade: it.unidade || 'UN',
              preco_unitario: it.preco_unitario || 0,
              peso_unitario_kg: 25.0,
              peso_total_kg: it.quantidade * 25.0,
              volume_total_m3: it.quantidade * 0.015,
              e_item_6m: false,
              cubagem_estimada: true,
            })),
          };
        });
        setOrders(mappedFromUploaded);
      } else {
        setOrders([]);
      }
    } catch (err) {
      console.error('Erro ao buscar pedidos:', err);
      if (uploadedOrders && uploadedOrders.length > 0) {
        // Fallback
      } else {
        setOrders([]);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, [dispatchResult, uploadedOrders]);

  // Contadores agregados
  const counts = useMemo(() => {
    const total = orders.length;
    const alocados = orders.filter((o) => o.status === 'ALOCADO').length;
    const naoAlocados = orders.filter((o) => o.status === 'NAO_ALOCADO').length;
    const descartados = orders.filter((o) => o.status === 'DESCARTADO').length;
    const pendentes = orders.filter((o) => o.status === 'PENDENTE').length;

    const valorTotal = orders.reduce((acc, o) => acc + (o.valor || 0), 0);
    const pesoTotal = orders.reduce((acc, o) => acc + (o.peso_kg || 0), 0);

    return { total, alocados, naoAlocados, descartados, pendentes, valorTotal, pesoTotal };
  }, [orders]);

  // Filtragem e Busca
  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      // Filtro de status
      if (statusFilter !== 'ALL' && order.status !== statusFilter) {
        return false;
      }

      // Busca textual (id, cliente, cidade, eixo, viagem)
      if (searchTerm.trim() !== '') {
        const term = searchTerm.toLowerCase();
        const matchId = order.id.toLowerCase().includes(term) || order.external_id.toLowerCase().includes(term);
        const matchCliente = (order.cliente || '').toLowerCase().includes(term);
        const matchCidade = (order.cidade || '').toLowerCase().includes(term);
        const matchEixo = (order.eixo_nome || '').toLowerCase().includes(term);
        const matchViagem = (order.viagem_titulo || '').toLowerCase().includes(term);
        return matchId || matchCliente || matchCidade || matchEixo || matchViagem;
      }

      return true;
    });
  }, [orders, statusFilter, searchTerm]);

  const fmtMoney = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  return (
    <div className="max-w-6xl mx-auto py-8 px-6 space-y-8 animate-fadeIn">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Package className="w-8 h-8 text-amber-500" />
            <span>Listagem Geral de Pedidos</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Visão unificada de todos os pedidos: alocados em viagens, pendentes de alocação e descartes por regras de negócio.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadOrders}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition shadow-xs cursor-pointer"
            title="Atualizar lista de pedidos"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-amber-600' : ''}`} />
            <span>Atualizar</span>
          </button>

          {onNavigateToPrepare && (
            <button
              onClick={onNavigateToPrepare}
              className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-slate-950 bg-amber-400 hover:bg-amber-500 rounded-xl transition shadow-xs cursor-pointer"
            >
              <span>{dispatchResult ? 'Ver Viagens' : 'Novo Lote'}</span>
              &rarr;
            </button>
          )}
        </div>
      </div>

      {/* Cards de Métricas e Resumo */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Geral */}
        <div className="border border-slate-200 bg-white rounded-2xl p-5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500 block mb-0.5">Total de Pedidos</span>
            <span className="text-2xl font-black text-slate-900 font-mono">{counts.total}</span>
            <span className="text-[11px] text-slate-400 block mt-1">
              {fmtMoney(counts.valorTotal)} • {Math.round(counts.pesoTotal).toLocaleString('pt-BR')} Kg
            </span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center shrink-0">
            <Package className="w-5 h-5" />
          </div>
        </div>

        {/* Alocados */}
        <div
          onClick={() => setStatusFilter(statusFilter === 'ALOCADO' ? 'ALL' : 'ALOCADO')}
          className={`border rounded-2xl p-5 shadow-xs flex items-center justify-between cursor-pointer transition ${
            statusFilter === 'ALOCADO' ? 'border-emerald-500 bg-emerald-50/50 ring-2 ring-emerald-400/30' : 'border-emerald-200 bg-white hover:border-emerald-300'
          }`}
        >
          <div>
            <span className="text-xs font-semibold text-emerald-700 block mb-0.5">Pedidos Alocados</span>
            <span className="text-2xl font-black text-emerald-800 font-mono">{counts.alocados}</span>
            <span className="text-[11px] text-emerald-600 block mt-1">
              Em {dispatchResult?.cargas_caminhao.length || 0} viagens ativas
            </span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        {/* Não Alocados */}
        <div
          onClick={() => setStatusFilter(statusFilter === 'NAO_ALOCADO' ? 'ALL' : 'NAO_ALOCADO')}
          className={`border rounded-2xl p-5 shadow-xs flex items-center justify-between cursor-pointer transition ${
            statusFilter === 'NAO_ALOCADO' ? 'border-amber-500 bg-amber-50/50 ring-2 ring-amber-400/30' : 'border-amber-200 bg-white hover:border-amber-300'
          }`}
        >
          <div>
            <span className="text-xs font-semibold text-amber-700 block mb-0.5">Não Alocados / Pendentes</span>
            <span className="text-2xl font-black text-amber-800 font-mono">
              {counts.naoAlocados + counts.pendentes}
            </span>
            <span className="text-[11px] text-amber-600 block mt-1">
              {counts.naoAlocados > 0 ? 'Capacidade / frota esgotada' : 'Aguardando alocação'}
            </span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        {/* Descartados na Limpeza */}
        <div
          onClick={() => setStatusFilter(statusFilter === 'DESCARTADO' ? 'ALL' : 'DESCARTADO')}
          className={`border rounded-2xl p-5 shadow-xs flex items-center justify-between cursor-pointer transition ${
            statusFilter === 'DESCARTADO' ? 'border-rose-500 bg-rose-50/50 ring-2 ring-rose-400/30' : 'border-slate-200 bg-white hover:border-rose-200'
          }`}
        >
          <div>
            <span className="text-xs font-semibold text-slate-600 block mb-0.5">Descartados (Expurgo)</span>
            <span className="text-2xl font-black text-slate-700 font-mono">{counts.descartados}</span>
            <span className="text-[11px] text-slate-500 block mt-1">
              Retirada Balcão / Cancelados
            </span>
          </div>
          <div className="w-11 h-11 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center shrink-0">
            <XCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Barra de Filtros e Busca */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Filtros em Abas */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              statusFilter === 'ALL'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Todos ({counts.total})
          </button>
          <button
            onClick={() => setStatusFilter('ALOCADO')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              statusFilter === 'ALOCADO'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
            }`}
          >
            Alocados ({counts.alocados})
          </button>
          <button
            onClick={() => setStatusFilter('NAO_ALOCADO')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              statusFilter === 'NAO_ALOCADO'
                ? 'bg-amber-500 text-slate-950 shadow-xs'
                : 'bg-amber-50 text-amber-800 hover:bg-amber-100'
            }`}
          >
            Não Alocados ({counts.naoAlocados})
          </button>
          {counts.pendentes > 0 && (
            <button
              onClick={() => setStatusFilter('PENDENTE')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                statusFilter === 'PENDENTE'
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'bg-sky-50 text-sky-700 hover:bg-sky-100'
              }`}
            >
              Pendentes ({counts.pendentes})
            </button>
          )}
          <button
            onClick={() => setStatusFilter('DESCARTADO')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              statusFilter === 'DESCARTADO'
                ? 'bg-rose-600 text-white shadow-xs'
                : 'bg-rose-50 text-rose-700 hover:bg-rose-100'
            }`}
          >
            Descartados ({counts.descartados})
          </button>
        </div>

        {/* Input de Busca */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar pedido, cliente, cidade..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 transition"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Tabela de Pedidos */}
      <div className="border border-slate-200 bg-white rounded-2xl overflow-hidden shadow-xs">
        {filteredOrders.length === 0 ? (
          <div className="p-12 text-center">
            <Package className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="font-bold text-slate-800 text-base">Nenhum pedido encontrado</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {orders.length === 0
                ? 'Importe um lote de pedidos na aba "Preparar" para visualizar os pedidos alocados e pendentes.'
                : 'Nenhum pedido corresponde aos critérios de busca ou filtros selecionados.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-4">Pedido / Cliente</th>
                  <th className="py-3.5 px-4">Destino / Eixo</th>
                  <th className="py-3.5 px-4">Status de Alocação</th>
                  <th className="py-3.5 px-4 text-right">Peso (Kg)</th>
                  <th className="py-3.5 px-4 text-right">Volume (m³)</th>
                  <th className="py-3.5 px-4 text-right">Valor</th>
                  <th className="py-3.5 px-4 text-center">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredOrders.map((order) => {
                  const isAllocated = order.status === 'ALOCADO';
                  const isUnallocated = order.status === 'NAO_ALOCADO';
                  const isDiscarded = order.status === 'DESCARTADO';
                  const isPending = order.status === 'PENDENTE';

                  return (
                    <tr key={order.id} className="hover:bg-slate-50/70 transition">
                      {/* Pedido / Cliente */}
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900 flex items-center gap-1.5">
                          <span>{order.id}</span>
                          {order.situacao === 'URGENTE' && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-black bg-rose-100 text-rose-700 border border-rose-200">
                              URGENTE
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-600 truncate max-w-[200px]" title={order.cliente || 'Consumidor Final'}>
                          {order.cliente || 'Consumidor Final'}
                        </div>
                        {order.endereco && (
                          <div className="text-[10px] text-slate-400 truncate max-w-[220px]" title={order.endereco}>
                            {order.endereco}
                          </div>
                        )}
                      </td>

                      {/* Destino / Eixo */}
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-800 flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                          <span>{order.cidade || '—'}</span>
                        </div>
                        <div className="text-[10px] text-amber-700 font-medium mt-0.5">
                          {order.eixo_nome || 'Eixo não classificado'}
                        </div>
                      </td>

                      {/* Status de Alocação */}
                      <td className="py-3.5 px-4">
                        {isAllocated && (
                          <div className="space-y-1">
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>{order.viagem_titulo || 'Alocado'}</span>
                            </span>
                            <div className="text-[10px] text-slate-500 font-medium flex items-center gap-1">
                              <Truck className="w-3 h-3 text-slate-400" />
                              <span>{order.veiculo_nome ? order.veiculo_nome.split(' ')[0] : 'Caminhão'}</span>
                              {order.ordem_entrega && (
                                <span className="font-mono text-emerald-600 font-bold">
                                  • {order.ordem_entrega}ª Parada
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        {isUnallocated && (
                          <div className="space-y-0.5">
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                              <AlertTriangle className="w-3 h-3 text-amber-700" />
                              <span>Não Alocado</span>
                            </span>
                            <p className="text-[10px] text-amber-700 max-w-[190px] leading-tight" title={order.motivo || ''}>
                              {order.motivo || 'Capacidade da frota excedida'}
                            </p>
                          </div>
                        )}

                        {isDiscarded && (
                          <div className="space-y-0.5">
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-300">
                              <XCircle className="w-3 h-3 text-slate-500" />
                              <span>Descartado</span>
                            </span>
                            <p className="text-[10px] text-slate-500 max-w-[190px] leading-tight" title={order.motivo || ''}>
                              {order.motivo || 'Regra de expurgo aplicada'}
                            </p>
                          </div>
                        )}

                        {isPending && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-sky-50 text-sky-700 border border-sky-200">
                            <Calendar className="w-3 h-3" />
                            <span>Pendente de Otimização</span>
                          </span>
                        )}
                      </td>

                      {/* Peso */}
                      <td className="py-3.5 px-4 text-right font-mono font-semibold text-slate-700">
                        {order.peso_kg > 0 ? `${order.peso_kg.toFixed(1)} Kg` : '—'}
                      </td>

                      {/* Volume */}
                      <td className="py-3.5 px-4 text-right font-mono text-slate-600">
                        {order.volume_m3 > 0 ? `${order.volume_m3.toFixed(3)} m³` : '—'}
                      </td>

                      {/* Valor */}
                      <td className="py-3.5 px-4 text-right font-mono font-bold text-slate-900">
                        {order.valor > 0 ? fmtMoney(order.valor) : '—'}
                      </td>

                      {/* Ações: Drill-down de Itens */}
                      <td className="py-3.5 px-4 text-center">
                        <button
                          onClick={() => setSelectedOrderForDrilldown(order)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:text-slate-950 bg-slate-100 hover:bg-amber-100 rounded-lg transition cursor-pointer"
                          title="Inspecionar materiais e itens do pedido"
                        >
                          <Eye className="w-3 h-3 text-amber-600" />
                          <span>Itens ({order.itens ? order.itens.length : 0})</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal de Drill-Down dos Itens do Pedido */}
      {selectedOrderForDrilldown && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden">
            {/* Header Modal */}
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-900 flex items-center justify-center font-bold">
                  <Package className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                    <span>Pedido #{selectedOrderForDrilldown.id}</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                        selectedOrderForDrilldown.status === 'ALOCADO'
                          ? 'bg-emerald-100 text-emerald-800'
                          : selectedOrderForDrilldown.status === 'NAO_ALOCADO'
                          ? 'bg-amber-100 text-amber-900'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {selectedOrderForDrilldown.status_label}
                    </span>
                  </h3>
                  <p className="text-xs text-slate-500">
                    {selectedOrderForDrilldown.cliente || 'Consumidor Final'} • {selectedOrderForDrilldown.cidade}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setSelectedOrderForDrilldown(null)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Conteúdo: Detalhes de Alocação e Tabela de Materiais */}
            <div className="p-6 overflow-y-auto space-y-5">
              {/* Box de Informações de Transporte */}
              <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Viagem</span>
                  <span className="font-bold text-slate-800">
                    {selectedOrderForDrilldown.viagem_titulo || 'Não Alocada'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Veículo</span>
                  <span className="font-bold text-slate-800">
                    {selectedOrderForDrilldown.veiculo_nome || 'Aguardando Frota'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Sequência</span>
                  <span className="font-bold text-slate-800">
                    {selectedOrderForDrilldown.ordem_entrega
                      ? `${selectedOrderForDrilldown.ordem_entrega}ª Parada`
                      : 'Sem parada'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Faturamento</span>
                  <span className="font-bold text-slate-800 font-mono">
                    {fmtMoney(selectedOrderForDrilldown.valor)}
                  </span>
                </div>
              </div>

              {selectedOrderForDrilldown.motivo && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <strong className="block font-bold">Observação / Motivo:</strong>
                    <span>{selectedOrderForDrilldown.motivo}</span>
                  </div>
                </div>
              )}

              {/* Tabela de Produtos / Itens do Pedido */}
              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-amber-600" />
                  <span>Itens e Materiais do Pedido ({selectedOrderForDrilldown.itens?.length || 0})</span>
                </h4>

                {(!selectedOrderForDrilldown.itens || selectedOrderForDrilldown.itens.length === 0) ? (
                  <div className="p-6 text-center border border-slate-200 rounded-xl text-xs text-slate-400">
                    Nenhum item individual cadastrado neste pedido.
                  </div>
                ) : (
                  <div className="border border-slate-200 rounded-xl overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                        <tr>
                          <th className="py-2.5 px-3">Código</th>
                          <th className="py-2.5 px-3">Descrição do Produto</th>
                          <th className="py-2.5 px-3 text-center">Quantidade</th>
                          <th className="py-2.5 px-3 text-right">Peso</th>
                          <th className="py-2.5 px-3 text-right">Volume</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                        {selectedOrderForDrilldown.itens.map((it, idx) => (
                          <tr key={idx} className="hover:bg-slate-50">
                            <td className="py-2 px-3 text-slate-500">{it.codigo || '—'}</td>
                            <td className="py-2 px-3 font-sans font-medium text-slate-900">{it.descricao}</td>
                            <td className="py-2 px-3 text-center font-bold text-slate-800">
                              {it.quantidade} {it.unidade}
                            </td>
                            <td className="py-2 px-3 text-right text-slate-600">
                              {it.peso_total_kg.toFixed(1)} Kg
                            </td>
                            <td className="py-2 px-3 text-right text-slate-600">
                              {it.volume_total_m3.toFixed(3)} m³
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Rodapé Modal */}
            <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex justify-end">
              <button
                onClick={() => setSelectedOrderForDrilldown(null)}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white transition shadow-xs cursor-pointer"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
import React, { useState } from 'react';
import {
  DecoupledOrderInput,
  DecoupledDispatchResponse,
  CargaCaminhaoViagem,
  RoteiroEntregaViagem,
} from '../../types/dispatch';
import {
  Upload,
  ArrowLeft,
  FileText,
  Loader2,
  MapPin,
  AlertTriangle,
  Layers,
  Route,
  CheckCircle2,
  Package,
} from 'lucide-react';
import { api } from '../../services/api';

interface PreparationViewProps {
  orders: DecoupledOrderInput[];
  dispatchResult: DecoupledDispatchResponse | null;
  isProcessing: boolean;
  onUploadCustomOrders: (orders: DecoupledOrderInput[]) => void;
  onExecuteDispatch: () => void;
  onClear?: () => void;
  onNavigateToOrders?: () => void;
  onNavigateToLoads?: () => void;
  onNavigateToRoutes?: () => void;
}

export const PreparationView: React.FC<PreparationViewProps> = ({
  orders,
  dispatchResult,
  isProcessing,
  onUploadCustomOrders,
  onExecuteDispatch,
  onClear,
  onNavigateToOrders,
  onNavigateToLoads,
  onNavigateToRoutes,
}) => {
  // Sub-etapas: 'upload' (Etapa 1), 'trucks' (Etapa 2), 'detail' (Etapa 3)
  // Inicia sempre no passo 1 (upload/visão limpa)
  const [currentStep, setCurrentStep] = useState<'upload' | 'trucks' | 'detail'>('upload');
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null);
  const [detailMode, setDetailMode] = useState<'carga' | 'rota'>('carga');

  // Cálculos agregados da Etapa 1 (Pré-visualização dos pedidos carregados)
  const totalPedidos = orders.length;
  const allItems = orders.flatMap((o) =>
    o.itens.map((it) => ({
      ...it,
      pedidoId: o.id,
      cliente: o.cliente || 'Cliente',
      cidade: o.cidade,
    }))
  );
  const totalProdutos = allItems.length;
  const totalVolumeEstimado = allItems.reduce((acc, it) => acc + (it.quantidade * 0.015), 0);
  const totalPesoEstimado = allItems.reduce((acc, it) => acc + (it.quantidade * 25.0), 0);
  const totalValor = orders.reduce((acc, o) => acc + (o.valor || 0), 0);

  // Viagens resultantes
  const trips = dispatchResult?.cargas_caminhao || [];
  const routes = dispatchResult?.roteiros_entrega || [];

  const activeTripId = selectedTripId || (trips.length > 0 ? trips[0].viagem_id : null);
  const selectedTripCarga: CargaCaminhaoViagem | undefined = trips.find(
    (t) => t.viagem_id === activeTripId
  );
  const selectedTripRoute: RoteiroEntregaViagem | undefined = routes.find(
    (r) => r.viagem_id === activeTripId
  );

  // Manipulador de upload de arquivo JSON/CSV
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        if (file.name.endsWith('.json')) {
          const parsed = JSON.parse(content);
          const list = Array.isArray(parsed)
            ? parsed
            : parsed.pedidos
            ? parsed.pedidos
            : (parsed.id || parsed.itens || parsed.items)
            ? [parsed]
            : [];
          onUploadCustomOrders(list);
        } else {
          alert('Por favor, selecione um arquivo JSON contendo os pedidos faturados.');
        }
      } catch (err) {
        alert('Formato de arquivo inválido. Certifique-se de selecionar um JSON válido.');
      }
    };
    reader.readAsText(file);
  };

  // Helper para formatar moeda
  const fmtMoney = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  return (
    <div className="max-w-6xl mx-auto py-8 px-6 space-y-8 animate-fadeIn">
      {/* Título Centralizado conforme Figma */}
      <div className="text-center space-y-3">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          Preparação
        </h1>

        {/* Barra de Navegação entre Etapas de Expedição */}
        {dispatchResult && trips.length > 0 && (
          <div className="flex items-center justify-center gap-2 bg-slate-100 p-1.5 rounded-2xl max-w-lg mx-auto">
            <button
              onClick={() => setCurrentStep('upload')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                currentStep === 'upload' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              1. Importar Pedidos
            </button>
            <button
              onClick={() => setCurrentStep('trucks')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                currentStep === 'trucks' ? 'bg-amber-400 text-slate-950 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              2. Viagens ({trips.length})
            </button>
            <button
              onClick={() => setCurrentStep('detail')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                currentStep === 'detail' ? 'bg-amber-400 text-slate-950 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              3. Detalhes (Carga & Rota)
            </button>
          </div>
        )}
      </div>

      {/* =================================================================== */}
      {/* ETAPA 1: Carregar CSV / Pré-visualização (Figma Imagem 2)            */}
      {/* =================================================================== */}
      {currentStep === 'upload' && (
        <div className="space-y-6">
          {/* Caixa de Carregamento Superior */}
          <div className="border border-amber-400 bg-white rounded-2xl p-4 md:p-5 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm">
            <div className="flex items-center gap-3 w-full md:w-auto">
              <Upload className="w-5 h-5 text-amber-600" />
              <span className="font-semibold text-slate-800 text-sm md:text-base">
                Carregar Arquivo de Pedidos (JSON / CSV)
              </span>
              <label className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-300 cursor-pointer transition">
                Escolher Arquivo
                <input
                  type="file"
                  accept=".csv,.json"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
            </div>

            <div className="flex items-center gap-2 w-full md:w-auto justify-end">
              {onNavigateToOrders && (orders.length > 0 || dispatchResult) && (
                <button
                  onClick={onNavigateToOrders}
                  className="text-xs text-slate-700 hover:text-slate-950 font-semibold px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 transition cursor-pointer flex items-center gap-1.5"
                >
                  <Package className="w-3.5 h-3.5 text-amber-500" />
                  <span>Ver Listagem de Pedidos</span>
                </button>
              )}
              {(orders.length > 0 || dispatchResult) && (
                <button
                  onClick={() => {
                    if (onClear) {
                      onClear();
                    } else {
                      onUploadCustomOrders([]);
                    }
                  }}
                  className="text-xs text-rose-600 hover:text-rose-800 font-semibold px-3 py-1.5 rounded-lg border border-rose-200 hover:bg-rose-50 transition cursor-pointer"
                >
                  Limpar Lote / Nova Expedição
                </button>
              )}
            </div>
          </div>

          {/* 5 Cards de Métricas Gerais */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Pedidos</h4>
              <div className="text-2xl font-bold text-slate-900 font-mono">
                {totalPedidos}
              </div>
            </div>

            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Produtos</h4>
              <div className="text-2xl font-bold text-slate-900 font-mono">
                {totalProdutos}
              </div>
            </div>

            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Volume</h4>
              <div className="text-2xl font-bold text-slate-900 font-mono">
                {totalPedidos === 0
                  ? '0.00 m³'
                  : dispatchResult?.resumo.total_allocated_volume_m3
                  ? `${dispatchResult.resumo.total_allocated_volume_m3.toFixed(2)} m³`
                  : `${totalVolumeEstimado.toFixed(1)} m³`}
              </div>
            </div>

            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Peso</h4>
              <div className="text-2xl font-bold text-slate-900 font-mono">
                {totalPedidos === 0
                  ? '0 Kg'
                  : dispatchResult?.resumo.total_allocated_weight_kg
                  ? `${Math.round(dispatchResult.resumo.total_allocated_weight_kg).toLocaleString('pt-BR')} Kg`
                  : `${Math.round(totalPesoEstimado).toLocaleString('pt-BR')} Kg`}
              </div>
            </div>

            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm col-span-2 md:col-span-1">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Valor</h4>
              <div className="text-xl font-bold text-slate-900 font-mono">
                {fmtMoney(totalValor)}
              </div>
            </div>
          </div>

          {/* Tabela de Produtos Carregados ou Estado Vazio */}
          {totalPedidos === 0 ? (
            <div className="border border-amber-400/60 border-dashed bg-white rounded-2xl p-12 text-center shadow-sm">
              <Upload className="w-10 h-10 text-amber-500/70 mx-auto mb-3" />
              <h3 className="font-bold text-slate-800 text-base">Nenhum pedido carregado</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                Clique em <strong>Escolher Arquivo</strong> acima para carregar o lote JSON ou CSV contendo os pedidos faturados reais.
              </p>
            </div>
          ) : (
            <div className="border border-amber-400 bg-white rounded-2xl overflow-hidden shadow-sm">
              <div className="max-h-96 overflow-y-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 text-slate-700 font-bold border-b border-amber-300 sticky top-0">
                    <tr>
                      <th className="py-3 px-4">Produto</th>
                      <th className="py-3 px-4">Unidade de Venda</th>
                      <th className="py-3 px-4 text-center">Quantidade</th>
                      <th className="py-3 px-4 text-right">Volume</th>
                      <th className="py-3 px-4 text-right">Peso</th>
                      <th className="py-3 px-4 text-right">Valor</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {allItems.slice(0, 50).map((it, idx) => {
                      const volItem = it.quantidade * 0.015;
                      const pesoItem = it.quantidade * 25.0;
                      const valItem = it.subtotal || it.quantidade * (it.preco_unitario || 38.0);
                      return (
                        <tr key={idx} className="hover:bg-amber-50/50 transition">
                          <td className="py-2.5 px-4 font-medium text-slate-900">
                            {it.descricao}
                            <span className="block text-[10px] text-slate-400 font-mono">
                              Cód: {it.codigo} • Pedido: {it.pedidoId} ({it.cidade})
                            </span>
                          </td>
                          <td className="py-2.5 px-4 text-slate-600">{it.unidade}</td>
                          <td className="py-2.5 px-4 text-center font-mono font-semibold">
                            {it.quantidade}
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono text-slate-600">
                            {volItem.toFixed(3)} m³
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono text-slate-600">
                            {pesoItem.toFixed(1)} Kg
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono font-semibold text-slate-900">
                            {fmtMoney(valItem)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Botão Inferior de Execução */}
          <div className="flex items-center justify-between pt-2">
            {dispatchResult && trips.length > 0 && (
              <button
                onClick={() => setCurrentStep('trucks')}
                className="text-amber-700 hover:text-amber-800 font-semibold text-sm flex items-center gap-1.5 cursor-pointer"
              >
                Ver viagens já calculadas ({trips.length}) &rarr;
              </button>
            )}
            <button
              onClick={() => {
                onExecuteDispatch();
                setCurrentStep('trucks');
              }}
              disabled={isProcessing || totalPedidos === 0}
              className="ml-auto bg-amber-400 hover:bg-amber-500 active:bg-amber-600 disabled:opacity-50 text-slate-950 font-bold px-10 py-3 rounded-xl shadow transition flex items-center gap-2 text-base cursor-pointer"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Otimizando Lote...</span>
                </>
              ) : (
                <span>Executar</span>
              )}
            </button>
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* ETAPA 2: Lista de Caminhões / Eixos (Figma Imagem 3)                */}
      {/* =================================================================== */}
      {currentStep === 'trucks' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <button
              onClick={() => setCurrentStep('upload')}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5 bg-white border border-slate-200 px-3.5 py-2 rounded-xl shadow-sm transition self-start sm:self-auto cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Voltar para Carregamento</span>
            </button>

            <div className="flex items-center gap-2 flex-wrap">
              {onNavigateToLoads && (
                <button
                  onClick={onNavigateToLoads}
                  className="text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 px-3 py-2 rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer"
                >
                  <Layers className="w-3.5 h-3.5 text-amber-500" />
                  <span>Visão Cargas</span>
                </button>
              )}
              {onNavigateToRoutes && (
                <button
                  onClick={onNavigateToRoutes}
                  className="text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 px-3 py-2 rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer"
                >
                  <Route className="w-3.5 h-3.5 text-amber-500" />
                  <span>Visão Rotas</span>
                </button>
              )}
              {onNavigateToOrders && (
                <button
                  onClick={onNavigateToOrders}
                  className="text-xs font-bold text-slate-900 bg-amber-400 hover:bg-amber-500 px-3.5 py-2 rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer"
                >
                  <Package className="w-4 h-4" />
                  <span>Todos os Pedidos</span>
                </button>
              )}
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider ml-1">
                {trips.length} Viagens
              </span>
            </div>
          </div>

          {dispatchResult?.pedidos_nao_alocados && dispatchResult.pedidos_nao_alocados.length > 0 && (
            <div className="p-4 bg-amber-50 border border-amber-300 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-amber-900 shadow-xs">
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
                <div>
                  <span className="font-bold">
                    {dispatchResult.pedidos_nao_alocados.length} pedido(s) não foram alocados nesta janela.
                  </span>
                  <span className="block text-amber-700 text-[11px]">
                    Capacidade da frota ou limite de volume excedido.
                  </span>
                </div>
              </div>
              {onNavigateToOrders && (
                <button
                  onClick={onNavigateToOrders}
                  className="px-3.5 py-1.5 bg-amber-400 hover:bg-amber-500 font-bold text-slate-950 rounded-xl transition shrink-0 cursor-pointer self-start sm:self-auto"
                >
                  Ver Pedidos Não Alocados &rarr;
                </button>
              )}
            </div>
          )}

          {/* Lista de Cards Horizontais com borda dourada conforme Figma */}
          <div className="space-y-4">
            {trips.map((viagem, index) => {
              return (
                <div
                  key={viagem.viagem_id}
                  className="border border-amber-400 bg-white rounded-2xl p-5 md:p-6 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm hover:shadow transition"
                >
                  <div className="space-y-1 w-full md:w-auto">
                    <div className="flex items-center gap-2.5">
                      <h3 className="text-base md:text-lg font-bold text-slate-900">
                        Viagem {index + 1} - {viagem.eixo_nome}
                      </h3>
                    </div>

                    <p className="text-xs text-slate-500 font-mono">
                      {viagem.veiculo.nome} ({viagem.veiculo.placa}) • {viagem.total_pedidos} pedidos •{' '}
                      {Math.round(viagem.peso_total_kg)} kg ({viagem.ocupacao_peso_pct}%) •{' '}
                      {viagem.volume_total_m3.toFixed(2)} m³ • Recurso Limitante:{' '}
                      <span className="font-bold text-slate-800">{viagem.recurso_limitante}</span>
                    </p>
                  </div>

                  <button
                    onClick={() => {
                      setSelectedTripId(viagem.viagem_id);
                      setCurrentStep('detail');
                    }}
                    className="w-full md:w-auto bg-amber-400 hover:bg-amber-500 active:bg-amber-600 text-slate-950 font-bold px-8 py-2.5 rounded-xl shadow-sm transition text-sm cursor-pointer"
                  >
                    Visualizar
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* ETAPA 3: Detalhe da Viagem / Eixo (Figma Imagem 4)                  */}
      {/* =================================================================== */}
      {currentStep === 'detail' && selectedTripCarga && (
        <div className="space-y-6">
          {/* Botão de Retorno e Alternador de Visão */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <button
              onClick={() => setCurrentStep('trucks')}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5 bg-white border border-slate-200 px-3.5 py-2 rounded-xl shadow-sm transition self-start"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Voltar para Lista de Viagens</span>
            </button>

            <div className="flex items-center gap-2 self-end">
              <button
                onClick={() => setDetailMode('carga')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                  detailMode === 'carga'
                    ? 'bg-slate-900 text-white'
                    : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Carga da Viagem</span>
              </button>

              <button
                onClick={() => setDetailMode('rota')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                  detailMode === 'rota'
                    ? 'bg-slate-900 text-white'
                    : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
                }`}
              >
                <Route className="w-3.5 h-3.5" />
                <span>Roteiro TSP</span>
              </button>
            </div>
          </div>

          {/* Barra Superior Dourada/Amarela conforme Figma */}
          <div className="bg-amber-400 text-slate-950 font-bold text-center py-3 px-6 rounded-2xl shadow-sm text-base md:text-lg tracking-tight">
            {selectedTripCarga.titulo} — {selectedTripCarga.eixo_nome} ({selectedTripCarga.veiculo.nome})
          </div>

          {/* Alerta de Carroceria Aberta */}
          {selectedTripCarga.alerta_carroceria && (
            <div className="p-3.5 bg-amber-50 border border-amber-300 rounded-xl text-xs text-amber-950 font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
              <span>{selectedTripCarga.alerta_carroceria}</span>
            </div>
          )}

          {/* 5 Cards de Métricas Específicos do Caminhão */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Pedidos</h4>
              <div className="text-2xl font-bold text-slate-900 font-mono">
                {selectedTripCarga.total_pedidos}
              </div>
            </div>

            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Produtos</h4>
              <div className="text-2xl font-bold text-slate-900 font-mono">
                {selectedTripCarga.pedidos_carroceria.reduce(
                  (acc, p) => acc + p.itens.length,
                  0
                )}
              </div>
            </div>

            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Volume</h4>
              <div className="text-lg md:text-xl font-bold text-slate-900 font-mono">
                {selectedTripCarga.volume_total_m3.toFixed(2)} m³ /{' '}
                <span className="text-xs text-slate-400">
                  {selectedTripCarga.veiculo.volume_util_m3} m³
                </span>
              </div>
            </div>

            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Peso</h4>
              <div className="text-lg md:text-xl font-bold text-slate-900 font-mono">
                {Math.round(selectedTripCarga.peso_total_kg).toLocaleString('pt-BR')} Kg
              </div>
            </div>

            <div className="border border-amber-400 bg-white rounded-2xl p-4 text-center shadow-sm col-span-2 md:col-span-1">
              <h4 className="text-xs font-semibold text-slate-600 mb-1">Valor</h4>
              <div className="text-base md:text-lg font-bold text-slate-900 font-mono">
                {fmtMoney(selectedTripCarga.faturamento_total)}
              </div>
            </div>
          </div>

          {/* MODO A: VISÃO CARGA NO CAMINHÃO (Agrupamento Pedidos) */}
          {detailMode === 'carga' && (
            <div className="space-y-4">
              <div className="border border-amber-400 bg-white rounded-2xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-50 text-slate-700 font-bold border-b border-amber-300">
                      <tr>
                        <th className="py-3 px-4">Produto</th>
                        <th className="py-3 px-4">Unidade de Venda</th>
                        <th className="py-3 px-4 text-center">Quantidade</th>
                        <th className="py-3 px-4 text-right">Volume</th>
                        <th className="py-3 px-4 text-right">Peso</th>
                        <th className="py-3 px-4 text-right">Valor</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedTripCarga.pedidos_carroceria.map((ped, pedIdx) => (
                        <React.Fragment key={ped.pedido}>
                          {/* Linha Amarela de Agrupamento por Pedido conforme Figma */}
                          <tr className="bg-[#FEF3C7] border-t-2 border-b border-amber-300 font-bold text-slate-900">
                            <td colSpan={6} className="py-2.5 px-4">
                              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                                <span>
                                  Pedido {String(pedIdx + 1).padStart(3, '0')} — {ped.pedido}{' '}
                                  ({ped.cliente || 'Cliente Nobre Lar'}) • {ped.cidade}
                                </span>
                                <span className="text-[11px] font-mono text-slate-700">
                                  {ped.pagamento_na_entrega ? (
                                    <span className="text-rose-700 font-bold">
                                      A RECEBER NA ENTREGA
                                    </span>
                                  ) : (
                                    <span className="text-emerald-700">Quitado</span>
                                  )}
                                </span>
                              </div>
                            </td>
                          </tr>

                          {/* Linhas de Produtos pertencentes a este pedido */}
                          {ped.itens.map((it, itIdx) => (
                            <tr
                              key={`${ped.pedido}-${itIdx}`}
                              className="hover:bg-amber-50/40 border-b border-slate-100 transition"
                            >
                              <td className="py-2.5 px-4 font-medium text-slate-900">
                                {it.descricao}
                                <span className="block text-[10px] text-slate-400 font-mono">
                                  Cód: {it.codigo}
                                </span>
                              </td>
                              <td className="py-2.5 px-4 text-slate-600">{it.unidade}</td>
                              <td className="py-2.5 px-4 text-center font-mono font-semibold">
                                {it.quantidade}
                              </td>
                              <td className="py-2.5 px-4 text-right font-mono text-slate-600">
                                {it.volume_total_m3.toFixed(3)} m³
                              </td>
                              <td className="py-2.5 px-4 text-right font-mono text-slate-600">
                                {it.peso_total_kg.toFixed(1)} Kg
                              </td>
                              <td className="py-2.5 px-4 text-right font-mono font-semibold text-slate-900">
                                {fmtMoney(it.quantidade * (it.preco_unitario || 38.0))}
                              </td>
                            </tr>
                          ))}
                        </React.Fragment>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ============================================================= */}
          {/* MODO B: VISÃO ROTEIRO TSP (Sequência de Paradas e Cobrança)    */}
          {/* ============================================================= */}
          {detailMode === 'rota' && selectedTripRoute && (
            <div className="space-y-4">
              <div className="bg-slate-900 text-white p-4 rounded-xl flex items-center justify-between text-xs">
                <div>
                  <span className="text-slate-400 block">Extensão Estimada da Rota</span>
                  <span className="text-lg font-bold font-mono">
                    {selectedTripRoute.distancia_estimada_km.toFixed(1)} km
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Total a Receber na Rota</span>
                  <span className="text-lg font-bold font-mono text-amber-400">
                    {fmtMoney(selectedTripRoute.total_a_receber_rota)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Total Paradas</span>
                  <span className="text-lg font-bold font-mono">
                    {selectedTripRoute.total_paradas}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                {selectedTripRoute.paradas.map((parada) => (
                  <div
                    key={parada.parada}
                    className={`border rounded-xl p-4 bg-white shadow-sm transition ${
                      parada.status_pagamento === 'A RECEBER'
                        ? 'border-rose-400 bg-rose-50/20'
                        : 'border-slate-200'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-slate-900 text-amber-400 font-bold text-xs flex items-center justify-center">
                          #{parada.parada}
                        </span>
                        <h4 className="font-bold text-sm text-slate-900">
                          {parada.pedido} — {parada.cliente}
                        </h4>
                      </div>

                      {parada.status_pagamento === 'A RECEBER' ? (
                        <span className="bg-rose-600 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">
                          A RECEBER: {fmtMoney(parada.valor_a_receber)}
                        </span>
                      ) : (
                        <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          Quitado
                        </span>
                      )}
                    </div>

                    <div className="mt-2.5 text-xs text-slate-600 flex items-start gap-1.5">
                      <MapPin className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <span>{parada.endereco_completo}</span>
                    </div>

                    {parada.alerta_cobranca && (
                      <div className="mt-2 text-xs text-rose-700 font-bold bg-rose-100/70 p-2 rounded-lg border border-rose-200">
                        ⚠️ {parada.alerta_cobranca}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Botão Inferior Direito "Gerar PDF" conforme Figma */}
          <div className="flex items-center justify-end pt-2">
            <a
              href={
                detailMode === 'carga'
                  ? api.getLoadingSheetPdfUrl(selectedTripCarga.viagem_id)
                  : api.getDeliveryRoutePdfUrl(selectedTripCarga.viagem_id)
              }
              target="_blank"
              rel="noopener noreferrer"
              className="bg-amber-400 hover:bg-amber-500 active:bg-amber-600 text-slate-950 font-bold px-10 py-3 rounded-xl shadow transition flex items-center gap-2 text-sm md:text-base cursor-pointer"
            >
              <FileText className="w-5 h-5" />
              <span>Gerar PDF</span>
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
